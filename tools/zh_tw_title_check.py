#!/usr/bin/env python3
"""Verify the 4-tone game title artwork is the approved Traditional version.

This checks a pinned, visually reviewed bitmap. It is not OCR and does not
validate all the remaining menus. The old Simplified Chinese bitmap is
explicitly rejected.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PIL import Image

EXPECTED_SHA256 = "ad450a5d1d90ff85ce7a9bbabffa225effde9423527d44c8ada9e05ad258b1fb"
OLD_SIMPLIFIED_SHA256 = "ade4a84c45e63a2d84cb445b14e8a0bf5ae01f558ad65bd3e382d608e3f9b83d"
TARGET_TEXT = "精靈寶可夢"


def verify(source: Path, report: Path, preview: Path) -> None:
    raw = source.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    with Image.open(source) as image:
        actual_size = list(image.size)
        luminance = image.convert("L")
        colors = sorted(set(luminance.getdata()))
        if actual_size != [128, 72]:
            raise ValueError("Title PNG must remain 128×72 to fit the game engine")
        if colors != [0, 85, 170, 255]:
            raise ValueError(f"Title PNG requires 4 grayscale palette levels; got {colors}")
        if checksum == OLD_SIMPLIFIED_SHA256:
            raise ValueError("Still using the original Simplified Chinese logo")
        if checksum != EXPECTED_SHA256:
            raise ValueError(
                "Title logo differs from reviewed Traditional raster; "
                "manually review and update EXPECTED_SHA256 if intentional."
            )
        luminance.save(preview)
    data = {
        "asset": str(source),
        "target_text": TARGET_TEXT,
        "sha256": checksum,
        "size": actual_size,
        "grayscale_levels": colors,
        "verified_against_reviewed_asset": True,
        "runtime_rendered_and_reviewed": False,
    }
    report.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Traditional title graphic verified: {checksum}")


if __name__ == "__main__":
    source = Path("pokecrystal_cn/gfx/title/logo.png")
    verify(source, Path("zh_tw_title_report.json"), Path("zh_tw_title_logo.png"))
