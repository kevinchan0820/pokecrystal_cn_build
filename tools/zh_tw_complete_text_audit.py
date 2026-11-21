#!/usr/bin/env python3
"""Exhaustive text-source audit for this Crystal Traditional-Chinese build.

Covers every translated workbook text cell and EVERY quoted ASM display
directive, not only menu directories. Keeps separate:
- mechanical simplified-only leftovers (strict release gate)
- contexts that need Taiwan/Hong Kong editorial review (non-blocking)
- Chinese literals outside recognized display directives (coverage warning)
This cannot validate text rasterized inside graphics or runtime strings.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from opencc import OpenCC
from openpyxl import load_workbook
from zh_tw_static import DISPLAY_LINE, QUOTED, separate_comment, SKIP

DIALOGUE = re.compile(r"文[1-9]$")
TERM_FLAGS = {
    "效果拔群": "Legacy unofficial battle translation; use 效果絕佳",
    "效果拔羣": "Legacy unofficial battle translation; use 效果絕佳",
    "甭": "PRC idiom; review against the English/Japanese source",
    "那啥": "PRC idiom; review against the English/Japanese source",
    "啥": "Mainland colloquialism; review per context",
    "初訓家": "OT term: check screen width and trainer identity meaning",
    "比賽規則": "Incorrect when referring to the Shift/Set battle option",
    "邊框       類型": "Bad frame-style menu layout; should display numbered style",
    "重新設置": "Potential mistranslation of Options as Reset",
    "重新設定": "Potential mistranslation of Options as Reset",
    "打印": "PRC term; UI generally uses 列印 in Taiwan",
    "軟件": "PRC term; Taiwan UI usually uses 軟體",
    "網絡": "PRC term; Taiwan UI uses 網路 (context dependent)",
    "信息": "PRC term; Taiwan UI usually uses 資訊 (context dependent)",
}


def workbook_cells(path):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        for ws in book:
            if DIALOGUE.fullmatch(ws.title):
                col = 5
                for row in ws.iter_rows(min_col=col, max_col=col):
                    for cell in row:
                        if isinstance(cell.value, str) and cell.value:
                            yield f"{ws.title}!{cell.coordinate}", cell.value
            elif ws.title in {"宝", "訓", "训", "类", "類", "城", "道", "招", "其"}:
                col = 4
                for row in ws.iter_rows(min_col=col, max_col=col):
                    for cell in row:
                        if isinstance(cell.value, str) and cell.value:
                            yield f"{ws.title}!{cell.coordinate}", cell.value
            elif ws.title in {"图", "圖"}:
                col = 5
                for row in ws.iter_rows(min_col=col, max_col=col):
                    for cell in row:
                        if isinstance(cell.value, str) and cell.value:
                            yield f"{ws.title}!{cell.coordinate}", cell.value
    finally:
        book.close()


def audit(root: Path, workbook: Path) -> dict:
    converter = OpenCC("s2twp")
    counts = Counter()
    remaining = []
    flagged = []
    unclassified = []
    term_totals = Counter()
    seen = set()

    def add(location: str, value: str, source: str):
        if not any("\u3400" <= ch <= "\u9fff" for ch in value):
            return
        counts[source + "_strings"] += 1
        proposed = converter.convert(value)
        if proposed != value:
            counts["unconverted"] += 1
            if len(remaining) < 300:
                remaining.append({"where": location, "source": source,
                                  "text": value[:140], "converted": proposed[:140]})
        for term, reason in TERM_FLAGS.items():
            k = value.count(term)
            if k:
                term_totals[term] += k
                if len(flagged) < 300:
                    flagged.append({"where": location, "term": term,
                                    "reason": reason, "text": value[:140]})

    for location, value in workbook_cells(workbook):
        add(location, value, "workbook")

    for path in sorted(root.rglob("*.asm")):
        rel = path.relative_to(root).as_posix()
        if rel in SKIP:
            continue
        counts["asm_files"] += 1
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code, _ = separate_comment(line)
            if '"' not in code:
                continue
            matches = [m.group(1) for m in QUOTED.finditer(code)]
            if not matches:
                continue
            display = DISPLAY_LINE.match(code) is not None
            for value in matches:
                if not any("\u3400" <= ch <= "\u9fff" for ch in value):
                    continue
                where = f"{rel}:{lineno}"
                if display:
                    add(where, value, "asm")
                else:
                    counts["uncategorized_chinese_literal"] += 1
                    if len(unclassified) < 150:
                        unclassified.append({"where": where, "text": value[:140]})

    result = {
        "scope": {
            "workbook": str(workbook), "asm_root": str(root),
            "not_tested": ["text drawn into PNG/GFX assets",
                           "runtime formatting of player names",
                           "manual visual pagination and line wrap"],
        },
        "counts": dict(counts),
        "unconverted": remaining,
        "regional_term_counts": dict(term_totals),
        "regional_term_examples": flagged,
        "unclassified_literals": unclassified,
        "passes_mechanical_translation": counts["unconverted"] == 0,
        "editorial_qa_complete": False,
        "note": "0 convertible items means OpenCC idempotence in covered cells, NOT official terminology or perfect Traditional glyph rendering.",
    }
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    p.add_argument("--workbook", type=Path, default=Path("text.zh-TW.xlsx"))
    p.add_argument("--report", type=Path, default=Path("zh_tw_complete_text_audit_report.json"))
    p.add_argument("--strict", action="store_true")
    a = p.parse_args()
    result = audit(a.source, a.workbook)
    a.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = result["counts"]
    print(f"Full text audit: workbook {counts.get('workbook_strings',0)}; "
          f"ASM {counts.get('asm_strings',0)} in {counts.get('asm_files',0)} files; "
          f"not converted {counts.get('unconverted',0)}; "
          f"uncategorized literals {counts.get('uncategorized_chinese_literal',0)}")
    if a.strict and not result["passes_mechanical_translation"]:
        for entry in result["unconverted"][:30]:
            print("LEFTOVER", entry)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
