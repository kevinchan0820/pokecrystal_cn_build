#!/usr/bin/env python3
"""Prepare a Traditional Chinese workbook candidate and audit missing glyphs.

Requires openpyxl and opencc-python-reimplemented. This does not modify font
binary assets; a clean audit does not mean a playable ROM has been tested.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
import re
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook
from opencc import OpenCC

CHARMAP_RE = re.compile(r'^\s*charmap_w\s+"([^"]+)"\s*,', re.MULTILINE)
NAMED_SHEETS = {"宝", "训", "类", "城", "道", "招", "其"}


def translation_cells(workbook):
    """Avoid changing spreadsheet metadata, control labels, or English/Japanese."""
    for sheet in workbook:
        if sheet.title in NAMED_SHEETS:
            for row in range(2, sheet.max_row + 1):
                yield sheet, row, 4
        elif sheet.title == "图":
            for row in range(1, sheet.max_row + 1):
                if (row - 1) % 9 in (1, 5, 6, 7):
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


def prepare(source, charmap, output, report_path, conversion, overrides, species_file, move_file, item_file, audit_only=False):
    supported = available_glyphs(charmap)
    converter = OpenCC(conversion)
    workbook = load_workbook(source)
    item_names = {}
    if item_file:
        item_names = json.loads(item_file.read_text(encoding="utf-8"))["byEnglish"]
    if move_file:
        move_names = json.loads(move_file.read_text(encoding="utf-8"))["names"]
        if len(move_names) != 251 or not all(isinstance(x, str) and x for x in move_names):
            raise ValueError("Move names file must contain 251 nonempty strings")
    else:
        move_names = []
    if species_file:
        names = json.loads(species_file.read_text(encoding="utf-8"))["names"]
        if len(names) != 251 or len(set(names)) != 251:
            raise ValueError("Species names file must contain exactly 251 unique indexed names")
        pokemon_sheet = workbook["宝"]
        original_names = {
            pokemon_sheet.cell(row=i + 2, column=4).value: names[i]
            for i in range(251)
        }
        original_names.update({
            converter.convert(old): new for old, new in list(original_names.items())
        })
        # Longer species names first so substrings such as "伊布" do not shadow "水伊布".
        name_pairs = sorted(
            ((old, new) for old, new in original_names.items() if old and new),
            key=lambda p: (-len(p[0]), p[0]),
        )
        name_regex = re.compile("|".join(re.escape(old) for old, _ in name_pairs))
        name_mapping = dict(name_pairs)
    else:
        names = []
        name_regex = None
        name_mapping = {}
    scanned = Counter()
    missing = Counter()
    examples = []
    changed = 0

    for sheet, row, column in translation_cells(workbook):
        cell = sheet.cell(row=row, column=column)
        if not isinstance(cell.value, str) or not cell.value:
            continue
        original = cell.value
        translated = original
        if not audit_only:
            translated = converter.convert(original)
            if names and sheet.title == "宝" and column == 4 and 2 <= row <= 252:
                translated = names[row - 2]
            elif move_names and sheet.title == "招" and column == 4 and 2 <= row <= 252:
                translated = move_names[row - 2]
            elif sheet.title == "道" and column == 4 and item_names:
                source_name = sheet.cell(row=row, column=2).value
                if isinstance(source_name, str):
                    normalized = "".join(ch for ch in unicodedata.normalize("NFKD", source_name)
                                         if ord(ch) < 128 and ch.isalnum()).upper()
                    found_name = item_names.get(normalized)
                    if found_name and sum(2 if ord(c) > 127 else 1 for c in found_name) <= 12:
                        translated = found_name
            elif name_regex:
                translated = name_regex.sub(lambda match: name_mapping[match.group()], translated)
            for old, new in sorted(overrides.items(), key=lambda kv: -len(kv[0])):
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
    parser.add_argument("--species", type=Path,
                        default=Path("data/pokemon_zh_hant_251.json"))
    parser.add_argument("--moves", type=Path,
                        default=Path("data/move_zh_hant_251.json"))
    parser.add_argument("--items", type=Path,
                        default=Path("data/item_zh_hant_english.json"))
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero when Unicode characters lack a charmap entry")
    parser.add_argument("--audit-only", action="store_true",
                        help="Inspect workbook without converting its text a second time")
    options = parser.parse_args()
    replacements = {}
    if options.overrides:
        replacements = json.loads(options.overrides.read_text(encoding="utf-8"))
        if not isinstance(replacements, dict) or not all(
                isinstance(k, str) and isinstance(v, str)
                for k, v in replacements.items()):
            parser.error("--overrides must be a JSON object of string-to-string replacements")
    result = prepare(options.input, options.charmap, options.output,
                     options.report, options.opencc, replacements,
                     options.species, options.moves, options.items, options.audit_only)
    print(f"Scanned {result['scanned_cells']} cells; modified "
          f"{result['changed_cells']}; missing glyphs: {result['missing_unique_count']}. "
          f"Report: {options.report}")
    if options.strict and result["missing_unique_count"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
