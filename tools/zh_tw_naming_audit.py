#!/usr/bin/env python3
"""Audit Traditional Chinese nickname choices in the existing ROM input engine.

This does not implement Zhuyin, Cangjie or Jyutping. It verifies that sample
TW/HK name characters can at least appear in the current Pinyin candidate
table and are encoded in the generated 12×12 font charmap.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CHARS = ("阿明", "家豪", "怡君", "嘉敏", "子軒", "阿寶", "小火", "皮卡")
CHARMAP = re.compile(r'^\s*charmap_w\s+"([^"]+)"', re.MULTILINE)
INPUT_ENTRY = re.compile(r'^\s*db_w\s+"([^"]+)"', re.MULTILINE)


def inspect(source: Path) -> dict:
    charmap_file = source / "constants/charmap_cn.asm"
    charmap = set(CHARMAP.findall(charmap_file.read_text(encoding="utf-8")))
    name_source = (source / "engine/menus/naming_screen.asm").read_text(encoding="utf-8")
    ime_files = [
        source / "data/ime/ime_table1.asm",
        source / "data/ime/ime_table2.asm",
    ]
    input_chars = set()
    for path in ime_files:
        for entry in INPUT_ENTRY.findall(path.read_text(encoding="utf-8")):
            input_chars.update(c for c in entry if "\u3400" <= c <= "\u9fff")
    examples = []
    for name in CHARS:
        examples.append({
            "name": name,
            "missing_in_charmap": [ch for ch in name if ch not in charmap],
            "missing_in_pinyin_candidates": [ch for ch in name if ch not in input_chars],
        })
    mode_labels = [
        "NamingScreen_ApplyTextInputModeChinese:",
        "NamingScreen_ApplyTextInputModeEnglish:",
        "IME_TryAddCharacter:",
    ]
    missing_modes = [label for label in mode_labels if label not in name_source]
    errors = []
    if missing_modes:
        errors.append(f"Missing name entry routines: {missing_modes}")
    for item in examples:
        if item["missing_in_charmap"] or item["missing_in_pinyin_candidates"]:
            errors.append(f"{item['name']}: unmapped/unavailable {item['missing_in_charmap']}, "
                          f"{item['missing_in_pinyin_candidates']}")
    return {
        "available_input_modes": ["Mandarin Pinyin", "English"],
        "not_yet_implemented": ["Taiwan Zhuyin", "Hong Kong Cangjie", "Quick", "Jyutping", "post-start trainer rename"],
        "sample_name_checks": examples,
        "source_charmap_characters": len(charmap),
        "source_ime_candidate_characters": len(input_chars),
        "errors": errors,
        "sample_coverage_passed": not errors,
        "important_limit": "Static availability only; candidate selection and in-game layout require emulator QA.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    parser.add_argument("--report", type=Path, default=Path("zh_tw_naming_audit_report.json"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = inspect(args.source)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"Name input audit: {len(result['sample_name_checks'])} sample names, "
          f"{len(result['errors'])} missing-font/input errors")
    if args.strict and result["errors"]:
        raise SystemExit(2)
