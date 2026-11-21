#!/usr/bin/env python3
"""Reject legacy simplified naming-toolbar bitmaps.

Source PNG is eight 12x8 glyphs: 中文符號刪除完成.
It cannot be fixed by OpenCC text conversion. Compare actual pixels against
NotoSansCJK TTC Taiwan face #3 and fail CI on a mismatch.
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

TEXT = "中文符號刪除完成"
def render(font_file):
    font = ImageFont.truetype(str(font_file), 12, index=3)
    expected = Image.new("L", (96, 8), 255)
    for i, ch in enumerate(TEXT):
        tile = Image.new("L", (40, 40), 255)
        d = ImageDraw.Draw(tile)
        x0, y0, x1, y1 = d.textbbox((0, 0), ch, font=font)
        d.text(((40-(x1-x0))/2-x0,(40-(y1-y0))/2-y0), ch, font=font, fill=0)
        bbox = ImageChops.difference(tile, Image.new("L",(40,40),255)).getbbox()
        if not bbox:
            raise ValueError(f"Missing TC glyph: {ch}")
        glyph = tile.crop(bbox).resize((min(12,bbox[2]-bbox[0]),8),Image.Resampling.LANCZOS)
        glyph = glyph.point(lambda value: 0 if value < 150 else 255)
        expected.paste(glyph, (i*12+(12-glyph.width)//2,0))
    return expected

def verify(source, font_file, report):
    src = source / "gfx/naming_screen/selection_chinese.png"
    observed = Image.open(src).convert("L")
    reference = render(font_file)
    errors = []
    if observed.size != (96,8):
        errors.append(f"Bitmap must be 96x8, got {observed.size}")
    else:
        for i,ch in enumerate(TEXT):
            a = observed.crop((i*12,0,(i+1)*12,8))
            b = reference.crop((i*12,0,(i+1)*12,8))
            if a.tobytes()!=b.tobytes():
                errors.append(f"Wrong TC glyph or changed pixel region: {ch} at {i}")
    result = {"text":TEXT,"actual_source":str(src),"font_face":"Taiwan TC index 3",
              "glyphs_checked":len(TEXT),"passed":not errors,"errors":errors}
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    if errors:
        raise SystemExit(2)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("pokecrystal_cn"))
    p.add_argument("--font",type=Path,required=True)
    p.add_argument("--report",type=Path,default=Path("zh_tw_toolbar_bitmap_audit_report.json"))
    a = p.parse_args()
    verify(a.source,a.font,a.report)
