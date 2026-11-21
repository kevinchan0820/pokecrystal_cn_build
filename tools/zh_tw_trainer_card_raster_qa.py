#!/usr/bin/env python3
"""Block simplified / PRC-style trainer-card title art.

Runtime uses gfx/trainer_card/card_status.2bpp directly. The source is a
48x8 PNG image, so OpenCC workbook translation cannot alter it.
Reference text: 目前狀態 (natural Taiwan UI terminology), TTC TC face #3.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

TEXT = "目前狀態"
FONT_SIZE = 13
THRESHOLD = 155


def reference(font_path: Path):
    font = ImageFont.truetype(str(font_path), FONT_SIZE, index=3)
    out = Image.new("L", (48, 8), 255)
    for i, char in enumerate(TEXT):
        tile = Image.new("L", (40, 40), 255)
        draw = ImageDraw.Draw(tile)
        left, top, right, bottom = draw.textbbox((0, 0), char, font=font)
        draw.text(((40 - (right - left)) / 2 - left,
                   (40 - (bottom - top)) / 2 - top), char, font=font, fill=0)
        bbox = ImageChops.difference(tile, Image.new("L", tile.size, 255)).getbbox()
        if not bbox:
            raise ValueError("Font lacks glyph: " + char)
        glyph = tile.crop(bbox).resize(
            (min(12, bbox[2] - bbox[0]), 8), Image.Resampling.LANCZOS)
        glyph = glyph.point(lambda x: 0 if x < THRESHOLD else 255)
        out.paste(glyph, (i * 12 + (12 - glyph.width) // 2, 0))
    return out


def audit(source: Path, font_path: Path, report: Path):
    png = source / "gfx/trainer_card/card_status.png"
    actual = Image.open(png).convert("L")
    expected = reference(font_path)
    errors = []
    if actual.size != (48, 8):
        errors.append(f"Trainer Card bitmap expected 48x8, got {actual.size}")
    else:
        for i, char in enumerate(TEXT):
            bbox = (i*12, 0, (i+1)*12, 8)
            if actual.crop(bbox).tobytes() != expected.crop(bbox).tobytes():
                errors.append(f"Wrong Taiwan glyph {char} at position {i}")
    result = {
        "verified": not errors,
        "source": str(png),
        "approved_text": TEXT,
        "errors": errors,
        "raster": "NotoSansCJK Taiwan face #3, 13px downscaled to 12x8",
        "limitation": "Source pixel audit; runtime Trainer Card visual test still needed",
    }
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--report", type=Path,
                        default=Path("zh_tw_trainer_card_raster_report.json"))
    args = parser.parse_args()
    audit(args.source, args.font, args.report)
