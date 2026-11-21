#!/usr/bin/env python3
"""Real source-tile audit of the GBC bag's 精靈球 pocket label.

ASM draws four pocket titles by looking up gfx/pack/pack_menu.tilemap.
The atlas contains Chinese glyph pixels, so OpenCC of ASM cannot alter it.
Fail on old 精灵球 and any corruption of the approved Taiwan glyphs.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse, json

def render_tc_label(fontpath):
    font=ImageFont.truetype(str(fontpath),16,index=3)
    label=Image.new("L",(48,16),0)
    for i,ch in enumerate("精靈球"):
        t=Image.new("L",(40,40),0)
        d=ImageDraw.Draw(t)
        box=d.textbbox((0,0),ch,font=font)
        d.text(((40-(box[2]-box[0]))//2-box[0],
                (40-(box[3]-box[1]))//2-box[1]),ch,font=font,fill=255)
        glyph=t.crop(t.getbbox()).resize((16,16),Image.Resampling.LANCZOS)
        glyph=glyph.point(lambda p:255 if p>140 else 0)
        label.paste(glyph,(16*i,0))
    return label

def check(source, fontpath, report):
    atlas=Image.open(source/"gfx/pack/pack_menu.png").convert("L")
    tiles=(source/"gfx/pack/pack_menu.tilemap").read_bytes()
    errors=[]
    if atlas.size != (64,80) or len(tiles)!=48:
        errors.append(f"Atlas/tilemap geometry changed: {atlas.size}, {len(tiles)} bytes")
    label=Image.new("L",(48,16),0)
    if not errors:
        # Pocket 1 is the visible ball pocket; the other three are
        # item/key item/TM. Only touch the ball's uniquely mapped 12 tiles.
        target=tiles[12:24]
        for y in range(2):
            for x in range(6):
                index=target[y*6+x]
                tile=atlas.crop(((index%8)*8,(index//8)*8,
                                 (index%8+1)*8,(index//8+1)*8))
                label.paste(tile,(x*8,y*8))
        tc=render_tc_label(fontpath)
        if label.tobytes()!=tc.tobytes():
            errors.append("Compiled bag pocket still not approved Taiwan Traditional 精靈球 16px art")
    result={"tested":"精靈球", "source":"gfx/pack/pack_menu.png",
            "tilemap":"gfx/pack/pack_menu.tilemap", "raster":"Taiwan TTC face3",
            "verified":not errors,"errors":errors,
            "limitations":"This checks only the ball pocket; other unused/legacy PNGs need review."}
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    if errors:raise SystemExit(2)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("pokecrystal_cn"))
    p.add_argument("--font",type=Path,required=True)
    p.add_argument("--report",type=Path,default=Path("zh_tw_pack_pocket_audit_report.json"))
    a=p.parse_args()
    check(a.source,a.font,a.report)
