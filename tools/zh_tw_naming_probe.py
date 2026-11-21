#!/usr/bin/env python3
"""Real PyBoy input replay to find the GBC naming screen and mode transitions.

Exploratory diagnostics, NOT a passing end-to-end naming test. No ROM exported.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from pyboy import PyBoy


def locate_symbols(rom):
    for path in sorted(rom.parent.glob("*.sym")):
        raw = path.read_text(encoding="utf-8", errors="ignore")
        if "NamingScreen" in raw and "wNamingScreenLetterCase" in raw:
            return path
    raise FileNotFoundError(f"Naming symbols .sym not found beside {rom}")


def probe(rom, output):
    output.mkdir(parents=True, exist_ok=True)
    symbols = locate_symbols(rom)
    game = PyBoy(str(rom), symbols=str(symbols), window="null", sound_emulated=False)
    game.set_emulation_speed(0)
    rows, visits = [], []
    addr = {label: game.symbol_lookup(label) for label in (
        "wNamingScreenLetterCase", "wIMELine", "wIMEMaxLine", "wNamingScreenCurNameLength"
    )}
    game.hook_register(None, "NamingScreen", lambda ctx: ctx.append("entered"), visits)

    def state():
        return {name: game.memory[location] for name, location in addr.items()}

    def picture(label):
        file = output / f"zh_tw_naming_probe_{label}.png"
        game.screen.image.copy().save(file)
        return file.name

    def record(label):
        rows.append({"step": label, "file": picture(label), "state": state()})

    def press(button, held=3, after=90):
        game.button_press(button)
        game.tick(held, render=True)
        game.button_release(button)
        game.tick(after, render=True)

    try:
        game.tick(3600, render=True)
        record("title")
        press("start", after=180)
        record("title_menu")
        press("a", after=220)
        record("new_game")
        for step in range(1, 101):
            press("a", after=100)
            if visits:
                record("naming_entered")
                break
            if step in (1, 2, 3, 5, 8, 12, 20, 30, 40, 50, 65, 80, 100):
                record(f"intro_{step:03}")
        if visits:
            for idx in range(1, 5):
                press("select", after=40)
                record(f"mode_{idx}")
                press("right", after=15)
                record(f"direction_{idx}")
    finally:
        game.stop(save=False)
    result = {
        "actual_naming_hook_reached": bool(visits),
        "naming_hook_visits": len(visits),
        "symbol_file": symbols.name,
        "observations": rows,
        "qualification": "Exploratory PyBoy replay; do not call passing input functionality without actual entry/candidate/del/confirm tests.",
    }
    (output / "zh_tw_naming_probe_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"entered": result["actual_naming_hook_reached"], "events": len(rows), "last": rows[-1]}, ensure_ascii=False))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=Path("."))
    args = p.parse_args()
    probe(args.rom, args.output)
