#!/usr/bin/env python3
"""Capture the real 160×144 title/options UI for manual Traditional-Chinese QA.

This is a deterministic input REPLAY in PyBoy, not an OCR-based proof.
Images must be inspected for text, glyph and border overlap before release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pyboy import PyBoy


def capture(rom: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    game = PyBoy(str(rom), window="null", sound_emulated=False)
    game.set_emulation_speed(0)
    shots = {}

    def press(button, held=3, after=30):
        game.button_press(button)
        game.tick(held, render=True)
        game.button_release(button)
        game.tick(after, render=True)

    def snap(label):
        im = game.screen.image.copy().convert("RGB")
        if im.size != (160, 144):
            raise ValueError(f"Wrong GBC image size: {im.size}")
        filename = output / f"zh_tw_ui_{label}.png"
        im.save(filename)
        shots[label] = {
            "file": str(filename),
            "pixel_sha256": hashlib.sha256(im.tobytes()).hexdigest(),
            "color_count": len(im.getcolors(maxcolors=300000) or []),
        }

    try:
        game.tick(3600, render=True)
        snap("title")
        press("start", after=150)
        snap("title_menu")
        press("down", after=12)
        press("a", after=150)
        snap("options")
        # Navigate to last real option (frame) and change the frame once.
        for _ in range(6):
            press("down", after=12)
        snap("frame_selector")
        press("right", after=50)
        snap("frame_changed")
    finally:
        game.stop(save=False)
    if all(item["color_count"] < 2 for item in shots.values()):
        raise AssertionError("No visible game UI rendered")
    result = {
        "screenshots": shots,
        "press_sequence": "START, DOWN, A, DOWNx6, RIGHT",
        "target": "Title menu -> Options -> frame style 1 through 8",
        "critical_limitation": "Captures real emulator graphics but navigation target and Chinese layout still require image review.",
        "text_ocr_verified": False,
    }
    (output / "zh_tw_ui_capture_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=Path("."))
    a = p.parse_args()
    capture(a.rom, a.output)
