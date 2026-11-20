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


def apply(root: Path, workbook: Path, rules_file: Path, report: Path):
    settings = json.loads(rules_file.read_text(encoding="utf-8"))
    results = []
    for rule in settings["ui_rules"]:
        target = root / rule["path"]
        if not target.is_file():
            raise FileNotFoundError(f"Missing localized UI source: {target}")
        count = substitute_exact_asm(target, rule["from"], rule["to"])
        if count != 1:
            raise ValueError(
                f"Rule {rule['id']} expected exactly one UI string; found {count}. "
                "Review the source/translation instead of silently skipping."
            )
        results.append({"id": rule["id"], "path": rule["path"], "count": count,
                        "old": rule["from"], "new": rule["to"]})

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
