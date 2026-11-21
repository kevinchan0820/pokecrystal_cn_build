#!/usr/bin/env python3
"""Block non-Taiwan glyphs in ALL custom naming-screen UI image labels.

Assets: 96x8 action bar 中文符號刪除完成 and 144x8 input mode bar
拼音英文臺灣香港速成倉頡. Each Han character is 12x8 source pixels
compiled as GBC 8x8 tiles; OpenCC cannot convert pre-rasterized art.
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

ASSETS = {
    "gfx/naming_screen/selection_chinese.png": "中文符號刪除完成",
    "gfx/naming_screen/mode_labels_zh_hant.png": "拼音英文臺灣香港速成倉頡注音",
}

def raster(text, font):
    out = Image.new("L", (len(text)*12, 8), 255)
    for i, ch in enumerate(text):
        tile=Image.new("L",(40,40),255)
        draw=ImageDraw.Draw(tile)
        x0,y0,x1,y1=draw.textbbox((0,0),ch,font=font)
        draw.text(((40-(x1-x0))/2-x0,(40-(y1-y0))/2-y0),ch,font=font,fill=0)
        box=ImageChops.difference(tile,Image.new("L",(40,40),255)).getbbox()
        if not box: raise ValueError("Missing Traditional glyph "+ch)
        glyph=tile.crop(box).resize((min(12,box[2]-box[0]),8),Image.Resampling.LANCZOS)
        glyph=glyph.point(lambda p: 0 if p<150 else 255)
        out.paste(glyph,(i*12+(12-glyph.width)//2,0))
    return out

def verify(root,font_path,report_path):
    font=ImageFont.truetype(str(font_path),12,index=3)
    assets=[]
    for filename,text in ASSETS.items():
        source=root/filename
        expected=raster(text,font)
        errors=[]
        if not source.exists():
            errors.append("Missing source image")
        else:
            actual=Image.open(source).convert("L")
            if actual.size!=expected.size:
                errors.append(f"Wrong dimensions: {actual.size} vs {expected.size}")
            else:
                for n,char in enumerate(text):
                    region=(n*12,0,(n+1)*12,8)
                    if actual.crop(region).tobytes()!=expected.crop(region).tobytes():
                        errors.append(f"Wrong Taiwan Traditional glyph: {char} (index {n})")
        assets.append({"source":filename,"text":text,
                       "font_face":"NotoSansCJK TTC Taiwan index 3",
                       "size":[len(text)*12,8],"errors":errors,"verified":not errors})
    result={"verified":all(x["verified"] for x in assets),"assets":assets}
    report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    if not result["verified"]:raise SystemExit(2)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("pokecrystal_cn"))
    p.add_argument("--font",type=Path,required=True)
    p.add_argument("--report",type=Path,default=Path("zh_tw_toolbar_bitmap_audit_report.json"))
    args=p.parse_args()
    verify(args.source,args.font,args.report)
