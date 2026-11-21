#!/usr/bin/env python3
"""Identify direct ASM/build-source references to raster assets.

A no-reference result never proves the asset is absent from the ROM: implicit
build rules, generated files, or indirect references can still exist.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

TARGETS = {
    "gfx/new_game/name_chinese.png": [
        "gfx/new_game/name_chinese.png",
        "gfx/new_game/name_chinese.2bpp",
        "gfx/new_game/name_chinese.1bpp",
        "name_chinese",
        "NameChinese",
    ],
    "gfx/naming_screen/selection_chinese.png": [
        "gfx/naming_screen/selection_chinese.2bpp",
        "gfx/naming_screen/selection_chinese.png",
    ],
    "gfx/trainer_card/card_status.png": [
        "gfx/trainer_card/card_status.2bpp",
        "gfx/trainer_card/card_status.png",
    ],
}
SUFFIXES = {".asm", ".inc", ".mk", ".py", ".c", ".h", ".txt"}
SKIP_PARTS = {".git", "build", ".venv", "venv", "__pycache__"}

def scan(root: Path):
    matches = {asset: [] for asset in TARGETS}
    files_scanned = 0
    for file in root.rglob("*"):
        if not file.is_file() or any(p in SKIP_PARTS for p in file.relative_to(root).parts):
            continue
        if file.suffix not in SUFFIXES and file.name not in {"Makefile", "makefile", "GNUmakefile"}:
            continue
        try:
            body = file.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        files_scanned += 1
        rel = file.relative_to(root).as_posix()
        for lineno, line in enumerate(body.splitlines(), 1):
            bare = line.lstrip()
            if bare.startswith(";") or bare.startswith("#"):
                continue
            for asset, patterns in TARGETS.items():
                if any(pat.lower() in line.lower() for pat in patterns):
                    matches[asset].append({"file": rel, "line": lineno, "snippet": line.strip()[:220]})
    return {
        "files_scanned": files_scanned,
        "assets": {
            asset: {
                "source_file_exists": (root / asset).is_file(),
                "direct_source_references": entries,
                "classification": "directly referenced" if entries else "no direct reference found; runtime use NOT PROVEN",
                "runtime_rendering_verified": False,
            }
            for asset, entries in matches.items()
        },
        "caveat": "Static source search only. No runtime pixel/output proof, and a missing direct match is not proof of unused asset.",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    p.add_argument("--report", type=Path, default=Path("zh_tw_asset_reference_report.json"))
    a = p.parse_args()
    if not a.source.is_dir():
        raise SystemExit("Game source directory missing: " + str(a.source))
    data = scan(a.source)
    a.report.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key, item in data["assets"].items():
        print(key + ": " + item["classification"] + " (" +
              str(len(item["direct_source_references"])) + " references)")
    if data["files_scanned"] < 100:
        raise SystemExit("Unexpectedly few source files scanned; checkout may be incomplete")

if __name__ == "__main__":
    main()
