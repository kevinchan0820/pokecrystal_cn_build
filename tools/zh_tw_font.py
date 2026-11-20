#!/usr/bin/env python3
"""Rasterize missing Traditional-Chinese characters into existing DFS 12x12 slots.

Must be run on a disposable clone after converting dialogue and static strings.
Original Simplified characters whose slots are reused may display as Traditional;
run save/menu/IME tests before shipping.
"""
import argparse
import json
import re
from pathlib import Path

from opencc import OpenCC
from openpyxl import load_workbook
from PIL import Image, ImageDraw, ImageFont

CODES = re.compile(r'^\s*charmap_w\s+"([^"]+)"\s*,\s*\$([0-9A-Fa-f]{2})\s*,\s*\$([0-9A-Fa-f]{2})', re.M)
QUOTES = re.compile(r'"((?:[^"\\]|\\.)*)"')
EXCLUDED = {"constants/charmap.asm", "constants/charmap_cn.asm", "macros/charmap_w.asm"}


def han(ch):
    return len(ch) == 1 and ("\u3400" <= ch <= "\u9fff" or "\uf900" <= ch <= "\ufaff")


def usage(source, workbook):
    used = set()
    book = load_workbook(workbook, read_only=True, data_only=True)
    for sheet in book:
        if sheet.title in {"宝", "训", "类", "城", "道", "招"}:
            index = 3
        elif sheet.title in {"图"}:
            index = 4
        elif re.fullmatch(r"文[1-9]", sheet.title):
            index = 4
        else:
            continue
        for row in sheet.iter_rows(values_only=True):
            if len(row) > index and isinstance(row[index], str):
                used.update(c for c in row[index] if han(c))
    book.close()

    for file in source.rglob("*.asm"):
        if file.relative_to(source).as_posix() in EXCLUDED:
            continue
        for line in file.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith(";"):
                continue
            for match in QUOTES.finditer(line.split(";", 1)[0]):
                used.update(c for c in match.group(1) if han(c))
    return used


def render(char, font):
    image = Image.new("L", (12, 12), 0)
    draw = ImageDraw.Draw(image)
    x0, y0, x1, y1 = draw.textbbox((0, 0), char, font=font)
    draw.text(((12 - (x1 - x0)) // 2 - x0,
               (12 - (y1 - y0)) // 2 - y0), char, font=font, fill=255)
    if image.getbbox() is None:
        raise ValueError("Empty glyph: " + char)
    # Three 4-pixel-wide by 12-pixel-tall bitplanes, 6 bytes per plane.
    bits = [int(image.getpixel((plane * 4 + x, y)) > 100)
            for plane in range(3) for y in range(12) for x in range(4)]
    result = bytes(sum(bits[pos+j] << (7-j) for j in range(8))
                   for pos in range(0, 144, 8))
    assert len(result) == 18
    return result


def write_glyph(root, high, low, glyph):
    if not 1 <= high <= 0x2e:
        raise ValueError("Unsupported font plane")
    side = "H" if low >= 128 else "L"
    file = root / "gfx" / "dfs" / ("ChineseFonts_%02X_%s.bin" % (high, side))
    blob = bytearray(file.read_bytes())
    start = (low & 127) * 18
    if start + 18 > len(blob):
        raise ValueError("Unavailable font slot: " + str((high, low)))
    blob[start:start+18] = glyph
    file.write_bytes(blob)
    return str(file.relative_to(root))


def build(root, workbook, fontname, report, pointsize):
    file = root / "constants" / "charmap_cn.asm"
    original = file.read_text(encoding="utf-8")
    codepoints = [(m.group(1), int(m.group(2), 16), int(m.group(3), 16))
                  for m in CODES.finditer(original)]
    if len(codepoints) < 2000:
        raise ValueError("Missing original GB2312 character map")
    existing = {ch: (hi, lo) for ch, hi, lo in codepoints if len(ch) == 1}
    required = usage(root, workbook)
    converter = OpenCC("s2t")
    predecessor = {}
    for char, hi, lo in codepoints:
        if not han(char):
            continue
        converted = converter.convert(char)
        if han(converted) and converted != char:
            predecessor.setdefault(converted, []).append(char)

    available = [(ch, hi, lo) for ch, hi, lo in codepoints
                 if han(ch) and ch not in required]
    allocated = set()
    additions = {}
    failures = []
    for target in sorted(c for c in required if c not in existing):
        candidates = [x for x in available if x[0] in predecessor.get(target, ())]
        candidates += available
        candidate = next((x for x in candidates if x[1:] not in allocated), None)
        if candidate is None:
            failures.append(target)
            continue
        old, hi, lo = candidate
        additions[target] = (hi, lo, old)
        allocated.add((hi, lo))

    # NotoSansCJK-Regular.ttc contains JP, KR, SC, TC and HK faces.
    # The Taiwan font is face #3, NOT the default Japanese face #0.
    font_index = 3 if Path(fontname).name == "NotoSansCJK-Regular.ttc" else 0
    chosen_font = ImageFont.truetype(fontname, size=pointsize, index=font_index)
    changed = set()
    for character, (hi, lo, old) in additions.items():
        changed.add(write_glyph(root, hi, lo, render(character, chosen_font)))

    if additions:
        lines = [original.rstrip("\n"),
                 "; Generated zh-Hant glyph aliases; originals occupy these codes."]
        for target, (hi, lo, old) in sorted(additions.items()):
            lines.append('\tcharmap_w "%s", $%02X, $%02X ; original %s' %
                         (target, hi, lo, old))
        file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    data = {
        "required_han": len(required),
        "existing_han": len(existing),
        "added_glyphs": len(additions),
        "rewritten_font_files": sorted(changed),
        "failed_chars": failures,
        "warning": "Generated bitmap characters need visual and emulator QA.",
    }
    report.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: v for k, v in data.items() if k != "rewritten_font_files"},
                     ensure_ascii=False))
    if failures:
        raise ValueError("Missing font capacity for: " + "".join(failures))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    p.add_argument("--workbook", type=Path, default=Path("text.zh-TW.xlsx"))
    p.add_argument("--font", required=True)
    p.add_argument("--size", type=int, default=12)
    p.add_argument("--report", type=Path, default=Path("zh_tw_font_report.json"))
    a = p.parse_args()
    build(a.source, a.workbook, a.font, a.report, a.size)


if __name__ == "__main__":
    main()
