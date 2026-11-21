#!/usr/bin/env python3
"""Real Quick/速成 input test against the compiled Game Boy Color ROM.

Controller events: SELECT×4 -> Quick; A+A -> 晶 or A+RIGHT+A -> 明.
Check ROM Quick table symbol pointer, selected glyph bytes, committed player
name, and capture actual screenshots. This is a *limited dictionary* prototype,
not a full licensed Quick IME.
"""
from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path
from pyboy import PyBoy

ROUTES = (
    (), # Quick now auto-focuses the first candidate after valid two-code lookup
    ("down", "down"), ("down", "down", "right"),
    ("right", "down", "down"), ("left", "down", "down"),
    ("down", "down", "left"), ("down", "down", "right", "right"),
    ("down", "down", "down"), ("down", "down", "down", "right"),
)


def char_code(charmap: Path, ch: str):
    text = charmap.read_text(encoding="utf-8")
    expr = re.compile(r'^\s*charmap_w\s+"' + re.escape(ch)
                      + r'"\s*,\s*\$([0-9A-Fa-f]{1,2})\s*,\s*\$([0-9A-Fa-f]{1,2})', re.M)
    matches = expr.findall(text)
    if len(matches) != 1:
        raise AssertionError(f"Need one mapped double-byte glyph {ch}, found {len(matches)}")
    return [int(v, 16) for v in matches[0]]


def run(rom: Path, source: Path, folder: Path, strict: bool):
    folder.mkdir(parents=True, exist_ok=True)
    sym = next((f for f in sorted(rom.parent.glob("*.sym"))
                if "wNamingScreenLetterCase" in f.read_text(errors="ignore")), None)
    if sym is None:
        raise RuntimeError("No compiled .sym file next to the ROM")
    gb = PyBoy(str(rom), symbols=str(sym), window="null", sound_emulated=False)
    gb.set_emulation_speed(0)
    labels = ["wNamingScreenLetterCase", "wIMEMaxLine", "wIMEAddr", "wIMEBank",
              "wIMEPinyin", "wNamingScreenCurNameLength", "wIMEChar", "wPlayerName"]
    symbols = {label: gb.symbol_lookup(label) for label in labels}
    failures, scenarios, visits = [], {}, []
    gb.hook_register(None, "NamingScreen", lambda v: v.append("entry"), visits)

    def read(label, delta=0):
        bank, address = symbols[label]
        return gb.memory[bank, address + delta]

    def button(name, delay=35):
        gb.button_press(name)
        gb.tick(3, render=True)
        gb.button_release(name)
        gb.tick(delay, render=True)

    def snapshot(label):
        name = "zh_tw_quick_pyboy_" + label + ".png"
        gb.screen.image.copy().save(folder / name)
        return name

    def save_state():
        with io.BytesIO() as stream:
            gb.save_state(stream)
            return stream.getvalue()

    def load_state(state):
        gb.load_state(io.BytesIO(state))
        gb.tick(3, render=True)

    try:
        gb.tick(3600, render=True)
        button("start", 180)
        button("a", 220)
        for _ in range(110):
            button("a", 100)
            if visits:
                break
        if not visits:
            raise AssertionError("Cannot enter player naming from actual new-game flow")
        for _ in range(4):
            button("select")
        if read("wNamingScreenLetterCase") != 4:
            raise AssertionError("SELECT×4 did not enter Quick mode")
        quick_blank = snapshot("quick_blank")
        baseline = save_state()
        for code, label, han, move in (("AA", "QuickV2_AA", "晶", ()),
                                        ("AB", "QuickV2_AB", "明", ("right",))):
            case = {"code": code, "target": han, "initial": quick_blank}
            scenarios[code] = case
            try:
                load_state(baseline)
                button("a", 45)  # Type first A, not choose a static character.
                for direction in move:
                    button(direction, 30)
                button("a", 45)  # Type next A/B from on-screen keyboard.
                case["composition_raw"] = [read("wIMEPinyin", offset) for offset in range(3)]
                case["candidate_pages"] = read("wIMEMaxLine")
                requested_bank, requested_address = gb.symbol_lookup(label)
                raw_pointer = read("wIMEAddr") | read("wIMEAddr", 1) << 8
                resolved = (read("wIMEBank"), raw_pointer)
                case["lookup_pointer"] = [*resolved]
                case["expected_symbol_pointer"] = [requested_bank, requested_address]
                case["candidates_screen"] = snapshot("code_" + code)
                if resolved != (requested_bank, requested_address):
                    raise AssertionError(f"{code}: wrong candidate table {resolved} != "
                                         f"{(requested_bank, requested_address)}")
                if case["candidate_pages"] != 1:
                    raise AssertionError(f"{code}: expected one candidate page")
                composition_state = save_state()
                expected = char_code(source / "constants/charmap_cn.asm", han)
                case["expected_charmap_bytes"] = expected
                for route in ROUTES:
                    load_state(composition_state)
                    for direction in route:
                        button(direction, 25)
                    button("a", 55)
                    if read("wNamingScreenCurNameLength") != 2:
                        continue
                    bytes_written = [read("wPlayerName"), read("wPlayerName", 1)]
                    case["selected_bytes"] = bytes_written
                    case["route"] = list(route)
                    if bytes_written == expected:
                        case["selected_character_screen"] = snapshot("committed_" + code)
                        case["passed"] = True
                        break
                if not case.get("passed"):
                    raise AssertionError(f"{code}: candidate rendered but could not pick {han} "
                                         f"via D-pad/A, expected bytes {expected}")
            except Exception as e:
                case["passed"] = False
                failures.append(f"{code}: {type(e).__name__}: {e}")
    except Exception as e:
        failures.append(f"setup: {type(e).__name__}: {e}")
    finally:
        gb.stop(save=False)
        report = {
            "passed": not failures and set(scenarios) == {"AA", "AB"},
            "real_controller_input": True,
            "rom": rom.name,
            "source_symbol_file": sym.name,
            "tested": scenarios,
            "failures": failures,
            "warning": "Full MIT Quick dictionary integrated; full Cangjie/Zhuyin and save/reload still pending.",
        }
        (folder / "zh_tw_quick_pyboy_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"passed": report["passed"], "cases": {key: val.get("passed") for key, val in scenarios.items()},
                          "failures": failures}, ensure_ascii=False))
    if strict and not report["passed"]:
        raise SystemExit(2)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    parser.add_argument("--output", type=Path, default=Path("."))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    run(args.rom, args.source, args.output, args.strict)
