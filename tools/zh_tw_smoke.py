#!/usr/bin/env python3
"""Boot and render the compiled ROM in the PyBoy Game Boy Color emulator.

This is a *smoke test*, not a full-game regression / localization QA.
No ROM is exported; screenshots and a factual JSON result are produced.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from pyboy import PyBoy


def smoke(rom: Path, output: Path) -> dict:
    data = rom.read_bytes()
    if not data or len(data) < 0x150 or len(data) % 0x4000:
        raise ValueError("Invalid Game Boy ROM structure")
    title = data[0x134:0x143].rstrip(b"\x00").decode("ascii", errors="replace")
    output.mkdir(parents=True, exist_ok=True)
    emulator = PyBoy(str(rom), window="null", sound_emulated=False)
    emulator.set_emulation_speed(0)
    samples = {}
    try:
        for target in (180, 600, 1200):
            ticks = target - (max(samples) if samples else 0)
            emulator.tick(ticks, render=True)
            picture = emulator.screen.image.copy()
            if picture.width != 160 or picture.height != 144:
                raise AssertionError("Unexpected GBC screen dimensions")
            colors = len(picture.convert("RGB").getcolors(maxcolors=256**3) or [])
            png = output / ("zh_tw_boot_%04d.png" % target)
            picture.save(png)
            samples[target] = {"png": str(png), "unique_colors": colors}
    finally:
        emulator.stop(save=False)
    summary = {
        "rom_title": title,
        "rom_bytes": len(data),
        "cgb_flag": data[0x143],
        "frames_emulated": 1200,
        "rendered_screenshots": samples,
        "screen_nonblank": any(v["unique_colors"] > 1 for v in samples.values()),
        "qualification": "Automated boot/render smoke check only, not complete game QA",
    }
    if not summary["screen_nonblank"]:
        raise AssertionError("Emulator displayed only blank monochrome screens")
    (output / "zh_tw_emulator_report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--output", type=Path, default=Path("."))
    args = parser.parse_args()
    smoke(args.rom, args.output)
