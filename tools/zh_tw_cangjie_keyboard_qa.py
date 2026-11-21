#!/usr/bin/env python3
"""Rime-reference 26-root GBC keyboard: preserve 8x8 key size and Latin modes.
Reference: https://github.com/rime/rime-cangjie/blob/master/cangjie5_express.schema.yaml
"""
from pathlib import Path
from PIL import Image
import argparse, json

ROOTS = "日月金木水火土竹戈十大中一弓人心手口尸廿山女田難卜符"

def audit(source):
    root = source / "gfx/naming_screen"
    png = root / "cangjie_roots.png"
    binary = root / "cangjie_roots.1bpp"
    asm = (source / "engine/menus/naming_screen.asm").read_text(encoding="utf-8")
    original = (source / "data/text/name_input_chars.asm").read_text(encoding="utf-8")
    errors = []
    for term in ("NamingScreen_RefreshCangjieKeyboard::", 
                 "NamingScreenGFX_CangjieRoots:",
                 "NamingScreen_ApplyTextInputModeQuick:", "vTiles1", "ld de, Font"):
        if term not in asm:
            errors.append("Missing source interface: " + term)
    if 'db_w "ABCDE FGHIJ KLMNOP"' not in original:
        errors.append("Original English keyboard was changed")
    if not binary.exists() or not png.exists():
        errors.append("Root 8x8 bitmap and source PNG missing")
    else:
        data = binary.read_bytes()
        image = Image.open(png).convert("1")
        if len(data) != 26*8 or image.size != (26*8,8):
            errors.append("Expected 26 8x8 1bpp tiles")
        else:
            rebuilt = bytearray()
            for i in range(26):
                for row in range(8):
                    byte = sum((128 >> x) for x in range(8)
                               if image.getpixel((i*8 + x, row)) == 0)
                    rebuilt.append(byte)
                if not any(data[i*8:(i+1)*8]):
                    errors.append("Blank Cangjie root " + ROOTS[i])
            if bytes(rebuilt) != data:
                errors.append("Root PNG / 1bpp mismatch")
    return {"canonical_roots": ROOTS,
            "letter_to_root":dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",ROOTS)),
            "key_dimensions_px":[8,8],
            "pass":not errors, "errors":errors}

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("pokecrystal_cn"))
    p.add_argument("--report",type=Path,default=Path("zh_tw_cangjie_keyboard_report.json"))
    a=p.parse_args()
    result=audit(a.source)
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"pass":result["pass"],"errors":result["errors"]},ensure_ascii=False))
    if not result["pass"]:raise SystemExit(2)
