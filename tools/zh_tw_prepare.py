#!/usr/bin/env python3
"""Prepare a Traditional Chinese workbook candidate and audit missing glyphs.

Requires openpyxl and opencc-python-reimplemented. This does not modify font
binary assets; a clean audit does not mean a playable ROM has been tested.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook
from opencc import OpenCC

CHARMAP_RE = re.compile(r'^\s*charmap_w\s+"([^"]+)"\s*,', re.MULTILINE)
NAMED_SHEETS = {"宝", "训", "类", "城", "道", "招"}


def translation_cells(workbook):
    """Avoid changing spreadsheet metadata, control labels, or English/Japanese."""
    for sheet in workbook:
        if sheet.title in NAMED_SHEETS:
            for row in range(2, sheet.max_row + 1):
                yield sheet, row, 4
        elif sheet.title == "图":
            for row in range(1, sheet.max_row + 1):
                if (row - 1) % 9 in (5, 6, 7):
                    yield sheet, row, 5
        elif re.fullmatch(r"文[1-9]", sheet.title):
            for row in range(1, sheet.max_row + 1):
                yield sheet, row, 5


def available_glyphs(chinese_charmap):
    charmap_files = [chinese_charmap, chinese_charmap.with_name("charmap.asm")]
    characters = set()
    for source in charmap_files:
        content = source.read_text(encoding="utf-8")
        characters.update(s for s in CHARMAP_RE.findall(content) if len(s) == 1)
    return characters


def prepare(source, charmap, output, report_path, conversion, overrides):
    supported = available_glyphs(charmap)
    converter = OpenCC(conversion)
    workbook = load_workbook(source)
    scanned = Counter()
    missing = Counter()
    examples = []
    changed = 0

    for sheet, row, column in translation_cells(workbook):
        cell = sheet.cell(row=row, column=column)
        if not isinstance(cell.value, str) or not cell.value:
            continue
        original = cell.value
        translated = converter.convert(original)
        for old, new in overrides.items():
            translated = translated.replace(old, new)
        scanned[sheet.title] += 1
        if translated != original:
            cell.value = translated
            changed += 1

        # Existing <PLAYER> and <USER> expressions are control tokens.
        # They must not be counted as glyphs or rewritten.
        visible_text = re.sub(r"<[^<>]+>", "", translated)
        for glyph in visible_text:
            if ord(glyph) > 127 and glyph not in supported:
                missing[glyph] += 1
                if len(examples) < 50:
                    examples.append({
                        "sheet": sheet.title,
                        "cell": cell.coordinate,
                        "glyph": glyph,
                        "text": translated[:160],
                    })

    result = {
        "source": str(source),
        "candidate": str(output) if output else None,
        "opencc_config": conversion,
        "scanned_cells": sum(scanned.values()),
        "changed_cells": changed,
        "sheets": dict(scanned),
        "missing_glyphs": dict(sorted(missing.items(), key=lambda p: (-p[1], p[0]))),
        "missing_unique_count": len(missing),
        "examples": examples,
        "font_remapping_completed": False,
        "rom_build_verified": False,
    }

    if output:
        if output.resolve() == source.resolve():
            raise ValueError("Refusing to overwrite upstream text.xlsx")
        output.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(output)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("text.xlsx"))
    parser.add_argument("--charmap", type=Path,
                        default=Path("pokecrystal_cn/constants/charmap_cn.asm"))
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=Path("zh_tw_report.json"))
    parser.add_argument("--opencc", default="s2twp")
    parser.add_argument("--overrides", type=Path, default=None)
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero when Unicode characters lack a charmap entry")
    options = parser.parse_args()
    replacements = {}
    if options.overrides:
        replacements = json.loads(options.overrides.read_text(encoding="utf-8"))
        if not isinstance(replacements, dict) or not all(
                isinstance(k, str) and isinstance(v, str)
                for k, v in replacements.items()):
            parser.error("--overrides must be a JSON object of string-to-string replacements")
    result = prepare(options.input, options.charmap, options.output,
                     options.report, options.opencc, replacements)
    print(f"Scanned {result['scanned_cells']} cells; modified "
          f"{result['changed_cells']}; missing glyphs: {result['missing_unique_count']}. "
          f"Report: {options.report}")
    if options.strict and result["missing_unique_count"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
