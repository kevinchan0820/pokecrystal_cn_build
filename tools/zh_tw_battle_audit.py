#!/usr/bin/env python3
"""Fail release builds when critical Taiwan Pokémon battle wording regresses.

The workbook is the translated text-import source. This checks known game
message identities, not merely whether a keyword occurs somewhere in a story.
It does not claim in-game emulator screenshots have been reviewed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from openpyxl import load_workbook

CANONICAL = {
    ("文3", "E2337"): "受到了灼傷的傷害！",
    ("文3", "E2429"): "敵人的【0】",
    ("文3", "E2829"): "擊中了要害！",
    ("文3", "E2837"): "效果絕佳！",
    ("文3", "E2842"): "效果不太好<……>",
}
LEGACY = ("效果拔群", "效果拔羣", "效果超卓", "好像效果不好")
SOURCES = {
    "super_effective": "https://tw.portal-pokemon.com/special/pika_vee/tc/20180712/",
    "not_very_effective": "https://niantic.helpshift.com/hc/zh-hant/6-pokemon-go/faq/2132-type-effectiveness-in-battle/",
}


def inspect(workbook: Path) -> dict:
    book = load_workbook(workbook, read_only=True, data_only=True)
    try:
        checks = []
        errors = []
        for (sheet, address), expected in CANONICAL.items():
            actual = book[sheet][address].value if sheet in book else None
            checks.append({
                "sheet": sheet,
                "cell": address,
                "expected": expected,
                "actual": actual,
                "pass": actual == expected,
            })
            if actual != expected:
                errors.append(f"{sheet}!{address}: expected {expected!r}, found {actual!r}")

        legacy = []
        checked = 0
        for sheet in book:
            if not (len(sheet.title) == 2 and sheet.title[0] == "文"
                    and sheet.title[1].isdigit()):
                continue
            for row in sheet.iter_rows(min_col=5, max_col=5):
                for cell in row:
                    value = cell.value
                    if not isinstance(value, str):
                        continue
                    checked += 1
                    for old in LEGACY:
                        if old in value:
                            legacy.append({
                                "sheet": sheet.title,
                                "cell": cell.coordinate,
                                "term": old,
                                "text": value[:120],
                            })
        if legacy:
            errors.append(f"{len(legacy)} legacy non-Taiwan battle term occurrence(s)")
        return {
            "canonical_battle_checks": checks,
            "checked_dialogue_cells": checked,
            "legacy_battle_phrases": legacy,
            "errors": errors,
            "verified": not errors,
            "source_urls": SOURCES,
            "scope": "Main text workbook only; manual battle rendering QA required",
        }
    finally:
        book.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=Path("text.zh-TW.xlsx"))
    parser.add_argument("--report", type=Path, default=Path("zh_tw_battle_audit_report.json"))
    args = parser.parse_args()
    data = inspect(args.workbook)
    args.report.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    for entry in data["errors"]:
        print("FAIL:", entry)
    if data["errors"]:
        raise SystemExit(2)
    print(f"Battle wording PASS: {len(data['canonical_battle_checks'])} critical "
          f"messages, {data['checked_dialogue_cells']} dialogue cells, "
          "no legacy effectiveness phrase")
