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
    interactions = {}
    try:
        for target in (180, 600, 1200, 2400, 3600):
            ticks = target - (max(samples) if samples else 0)
            emulator.tick(ticks, render=True)
            picture = emulator.screen.image.copy()
            if picture.width != 160 or picture.height != 144:
                raise AssertionError("Unexpected GBC screen dimensions")
            colors = len(picture.convert("RGB").getcolors(maxcolors=256**3) or [])
            png = output / ("zh_tw_boot_%04d.png" % target)
            picture.save(png)
            samples[target] = {"png": str(png), "unique_colors": colors}

        # Move beyond the intro: try title -> menu -> new-game dialogue.
        # Screens are captured for human review; input timing is not taken
        # as proof that the full game or every translation is correct.
        for button, label, ticks in [
            ("start", "menu", 180),
            ("a", "new_game", 240),
            ("a", "dialogue_1", 180),
            ("a", "dialogue_2", 180),
        ]:
            emulator.button(button)
            emulator.tick(ticks, render=True)
            image = emulator.screen.image.copy()
            screenshot = output / ("zh_tw_%s.png" % label)
            image.save(screenshot)
            interactions[label] = {
                "png": str(screenshot),
                "unique_colors": len(image.convert("RGB").getcolors(maxcolors=256**3) or []),
            }
    finally:
        emulator.stop(save=False)
    summary = {
        "rom_title": title,
        "rom_bytes": len(data),
        "cgb_flag": data[0x143],
        "frames_emulated": 4380,
        "rendered_screenshots": samples,
        "interaction_screenshots": interactions,
        "screen_nonblank": any(v["unique_colors"] > 1 for v in list(samples.values()) + list(interactions.values())),
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
