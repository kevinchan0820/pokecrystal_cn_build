#!/usr/bin/env python3
"""Verify pre-approved Taiwan-style trainer-card text pixels.

The source is 48x8 pre-rasterized art (4 glyphs): 目前狀態.
Original Simplified/PRC design fails this audit. Regenerating the glyph on
each CI runner from Noto TTC is *not deterministic*: host font revisions and
Pillow renderer versions give different 8px pixels. Instead compare decoded
pixel hashes of the four approved 12x8 glyphs, independent of PNG metadata.
Any art revision requires a reviewed new source and matching approved hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

TEXT = "目前狀態"
APPROVED_PIXEL_SHA256 = (
    "154822b43f4e02d7097de573fea33ac81b29e627edb1927ccf3146f6f777f32e",
    "2f092b46ef48e1e5f196efe2ded9e841d201d512248ccd6e14df7f5b6029f08d",
    "c908149342714029ac4c89b2e2d5c5e7f96b38640d476401116d2d75510d9b3a",
    "95bf6bff9736249ea4ab425f50ec93dd300d4f23a9b36593b17145f021e59384",
)

def audit(source: Path, font_path: Path, report: Path):
    png = source / "gfx/trainer_card/card_status.png"
    actual = Image.open(png).convert("L")
    errors = []
    observed = []
    if actual.size != (48, 8):
        errors.append(f"Trainer Card bitmap expected 48x8, got {actual.size}")
    else:
        for i, char in enumerate(TEXT):
            bbox = (i*12, 0, (i+1)*12, 8)
            got = hashlib.sha256(actual.crop(bbox).tobytes()).hexdigest()
            observed.append({"glyph":char,"pixel_sha256":got})
            if got != APPROVED_PIXEL_SHA256[i]:
                errors.append(f"Unapproved Taiwan glyph {char} at position {i}")
    result = {
        "verified": not errors,
        "source": str(png),
        "approved_text": TEXT,
        "glyphs": observed,
        "errors": errors,
        "raster": "Manually reviewed 48x8 Taiwan Traditional reference",
        "font_context": "NotoSansCJK Taiwan face #3; compiled pixels pinned across runners",
        "limitation": "Source pixel audit; runtime Trainer Card visual test still needed",
    }
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"verified":result["verified"],"errors":errors},ensure_ascii=False))
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
