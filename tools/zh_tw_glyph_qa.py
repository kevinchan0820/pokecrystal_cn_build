#!/usr/bin/env python3
"""Inspect actual compiled 12x12 glyph bitmaps vs NotoSans CJK Taiwan face.

Runs after font remapping, before ROM build. Generates a pixel-perfect PNG strip
of the actual in-repo binary glyphs. This is not a simulated GBC screenshot.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from PIL import Image, ImageFont
from zh_tw_font import render

SAMPLES = "好你的名字速成碼晶明敵人灼傷害火岩鼠"
CHARMAP = re.compile(r'^\s*charmap_w\s+"([^"]+)"\s*,\s*\$([0-9A-Fa-f]{1,2})\s*,\s*\$([0-9A-Fa-f]{1,2})', re.M)


def inspect(root, font_file, report, png):
    charmap = (root / "constants/charmap_cn.asm").read_text(encoding="utf-8")
    mapping = {ch: (int(hi, 16), int(lo, 16))
               for ch, hi, lo in CHARMAP.findall(charmap)}
    tc_face = ImageFont.truetype(str(font_file), 12, index=3)
    image = Image.new("RGB", (len(SAMPLES) * 56, 56), "white")
    missing = []
    checked = []
    for index, ch in enumerate(SAMPLES):
        if ch not in mapping:
            missing.append(ch)
            continue
        hi, lo = mapping[ch]
        side = "H" if lo >= 128 else "L"
        file = root / "gfx" / "dfs" / f"ChineseFonts_{hi:02X}_{side}.bin"
        blob = file.read_bytes()
        actual = blob[(lo & 127)*18:(lo & 127)*18+18]
        expected = render(ch, tc_face)
        if actual != expected:
            missing.append(ch)
        # Decode exactly the original game's binary glyph bitmap layout:
        # 3 groups of 4 columns, each stored as six bytes of 8 bits.
        bits = [(x >> (7 - k)) & 1 for x in actual for k in range(8)]
        small = Image.new("RGB", (12, 12), "white")
        for plane in range(3):
            for y in range(12):
                for x in range(4):
                    if bits[plane*48+y*4+x]:
                        small.putpixel((plane*4+x, y), (0, 0, 0))
        image.paste(small.resize((48, 48), Image.Resampling.NEAREST), (index*56, 4))
        checked.append({"char": ch, "code": [hi, lo], "matches_tc_face": actual == expected})
    image.save(png)
    result = {"font": font_file.name, "font_face": 3,
              "font_family": tc_face.getname()[0],
              "source": "actual binary DFS glyphs after font generation",
              "checked": checked, "mismatched_or_missing": missing,
              "verified": not missing}
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"verified": result["verified"], "font_family": result["font_family"],
                      "checked": len(checked), "errors": missing},ensure_ascii=False))
    if missing:
        raise SystemExit(2)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--report", type=Path, default=Path("zh_tw_glyph_qa.json"))
    p.add_argument("--png", type=Path, default=Path("zh_tw_glyph_qa.png"))
    args = p.parse_args()
    inspect(args.source,args.font,args.report,args.png)
