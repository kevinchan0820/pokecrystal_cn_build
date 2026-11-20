#!/usr/bin/env python3
"""Apply context-scoped zh-Hant-TW UI wording, audit regional terms.

Run on disposable source checkout after zh_tw_static.py and before font build.
Do not make global replacements that might change story semantics or metadata.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"')
SKIP = {"constants/charmap.asm", "constants/charmap_cn.asm", "macros/charmap_w.asm"}


def substitute_exact_asm(path: Path, original: str, replacement: str) -> int:
    contents = path.read_text(encoding="utf-8")
    lines = contents.splitlines(keepends=True)
    count = 0
    transformed = []
    for line in lines:
        if line.lstrip().startswith(";"):
            transformed.append(line)
            continue
        # A comment may contain quotes. Respect string literals when locating ';'.
        quoted = False
        escaped = False
        split = len(line)
        for i, ch in enumerate(line):
            if ch == '"' and not escaped:
                quoted = not quoted
            elif ch == ";" and not quoted:
                split = i
                break
            if ch == "\\" and not escaped:
                escaped = True
            else:
                escaped = False
        code, comment = line[:split], line[split:]
        def transform(match):
            nonlocal count
            if match.group(1) != original:
                return match.group(0)
            count += 1
            return '"' + replacement + '"'
        transformed.append(QUOTED.sub(transform, code) + comment)
    if count:
        path.write_text("".join(transformed), encoding="utf-8")
    return count


def iter_workbook_strings(workbook):
    book = load_workbook(workbook, read_only=True, data_only=True)
    try:
        for sheet in book:
            for row in sheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str) and cell.value:
                        yield f"{sheet.title}!{cell.coordinate}", cell.value
    finally:
        book.close()


def apply_dialogue_phrases(workbook: Path, rules):
    """Only edit E-column main dialogue in the generated candidate workbook."""
    if not rules:
        return []
    book = load_workbook(workbook)
    changes = []
    try:
        for rule in rules:
            if rule.get("scope") != "dialogue":
                raise ValueError("Unsupported workbook locale scope: " + str(rule.get("scope")))
            count = 0
            examples = []
            if "sheet" in rule or "cell" in rule:
                # Target one reviewed line: never rewrite a similar-looking
                # phrase spoken by another character in another scene.
                sheet_name = rule.get("sheet")
                address = rule.get("cell")
                if not sheet_name or not address or sheet_name not in book:
                    raise ValueError(f"Rule {rule['id']}: invalid sheet/cell selector")
                cell = book[sheet_name][address]
                if cell.column != 5 or not re.fullmatch(r"文[1-9]", sheet_name):
                    raise ValueError(f"Rule {rule['id']}: only dialogue E cells may be edited")
                if isinstance(cell.value, str):
                    count = cell.value.count(rule["from"])
                    if count:
                        cell.value = cell.value.replace(rule["from"], rule["to"])
                        examples.append(f"{sheet_name}!{cell.coordinate}")
            else:
                for sheet in book:
                    if not re.fullmatch(r"文[1-9]", sheet.title):
                        continue
                    for row in range(1, sheet.max_row + 1):
                        cell = sheet.cell(row=row, column=5)
                        if not isinstance(cell.value, str) or rule["from"] not in cell.value:
                            continue
                        count += cell.value.count(rule["from"])
                        cell.value = cell.value.replace(rule["from"], rule["to"])
                        if len(examples) < 20:
                            examples.append(f"{sheet.title}!{cell.coordinate}")
            if "expected_count" in rule and count != rule["expected_count"]:
                raise ValueError(
                    f"Rule {rule['id']} expected {rule['expected_count']} edit(s), "
                    f"found {count}; translation/source changed, review required."
                )
            changes.append({
                "id": rule["id"], "from": rule["from"], "to": rule["to"],
                "count": count, "sample_cells": examples,
            })
        if any(change["count"] for change in changes):
            book.save(workbook)
    finally:
        book.close()
    return changes


def apply(root: Path, workbook: Path, rules_file: Path, report: Path):
    settings = json.loads(rules_file.read_text(encoding="utf-8"))
    dialogue_changes = apply_dialogue_phrases(
        workbook, settings.get("workbook_phrase_rules", []))
    results = []
    for rule in settings["ui_rules"]:
        target = root / rule["path"]
        if not target.is_file():
            raise FileNotFoundError(f"Missing localized UI source: {target}")
        count = substitute_exact_asm(target, rule["from"], rule["to"])
        status = "replaced"
        if count == 0:
            # OpenCC phrase mode may have already chosen the desired Taiwan
            # wording; still require a single exact quoted UI string.
            existing = sum(
                1 for line in target.read_text(encoding="utf-8").splitlines()
                if not line.lstrip().startswith(";")
                for m in QUOTED.finditer(line.split(";", 1)[0])
                if m.group(1) == rule["to"]
            )
            if existing == 1:
                status = "already-localized"
            else:
                raise ValueError(
                    f"Rule {rule['id']} found neither its source string nor "
                    f"one exact expected target string (found {existing})."
                )
        elif count != 1:
            raise ValueError(
                f"Rule {rule['id']} expected exactly one UI string; found {count}. "
                "Review the source/translation instead of silently skipping."
            )
        results.append({"id": rule["id"], "path": rule["path"], "count": count,
                        "status": status, "old": rule["from"], "new": rule["to"]})

    flagged = Counter()
    samples = []
    terms = list(dict.fromkeys(settings.get("review_flags", [])))
    for location, text in iter_workbook_strings(workbook):
        for term in terms:
            count = text.count(term)
            if count:
                flagged[term] += count
                if len(samples) < 80:
                    samples.append({"where": location, "term": term, "text": text[:150]})
    for path in root.rglob("*.asm"):
        rel = path.relative_to(root).as_posix()
        if rel in SKIP:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith(";") or '"' not in line:
                continue
            for term in terms:
                if term in line:
                    flagged[term] += line.count(term)
                    if len(samples) < 80:
                        samples.append({"where": f"{rel}:{n}", "term": term,
                                        "text": line.strip()[:150]})
    payload = {
        "locale": settings["locale"],
        "applied_dialogue_rules": dialogue_changes,
        "applied_ui_rules": results,
        "review_flags": dict(flagged),
        "review_examples": samples,
        "editorial_review": settings.get("editorial_review", []),
        "warning": "Rule application is verified, not full dialogue, typography or screen-layout QA.",
    }
    report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"Taiwan locale rules applied: {len(results)}. "
          f"Terms requiring editorial review: {sum(flagged.values())}.")
    return payload


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    p.add_argument("--workbook", type=Path, default=Path("text.zh-TW.xlsx"))
    p.add_argument("--rules", type=Path, default=Path("data/zh_tw_locale.json"))
    p.add_argument("--report", type=Path, default=Path("zh_tw_locale_report.json"))
    args = p.parse_args()
    apply(args.source, args.workbook, args.rules, args.report)
