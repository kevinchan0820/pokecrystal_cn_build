#!/usr/bin/env python3
"""Reproducible PyBoy interactive naming tests for four *existing* 1.x modes.

Exercises genuine new-game -> naming screen, SELECT switching, controller
typing, deletion and visual screenshots. Candidate grid is NOT Zhuyin/Cangjie.
Exploratory until --strict; failures are always written to JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
from pyboy import PyBoy

MODES = ("pinyin", "english", "taiwan_common", "hongkong_common")
ROUTES = ((), ("down",), ("down","down"), ("down","down","right"),
          ("down","down","left"), ("down","down","down"),
          ("down","down","down","right"), ("right",),
          ("right","down","down"), ("left","down","down"))


def test(rom, output, strict):
    output.mkdir(parents=True, exist_ok=True)
    sym = next((f for f in sorted(rom.parent.glob("*.sym"))
                if "wNamingScreenLetterCase" in f.read_text(errors="ignore")), None)
    if sym is None:
        raise RuntimeError("Missing naming symbols; need build/pokecrystal11.sym")
    gb = PyBoy(str(rom), symbols=str(sym), window="null", sound_emulated=False)
    gb.set_emulation_speed(0)
    symbols = {}
    for label in ("wNamingScreenLetterCase", "wIMELine", "wIMEMaxLine",
                  "wIMEPinyin", "wIMEChar", "wNamingScreenCurNameLength",
                  "wJumptableIndex", "wNamingScreenType", "wIMEAddr", "wIMEBank"):
        symbols[label] = gb.symbol_lookup(label)

    def memory(label, offset=0):
        bank, addr = symbols[label]
        return gb.memory[bank, addr + offset]

    def image(name):
        im = gb.screen.image.copy().convert("RGB")
        p = output / f"zh_tw_naming_qa_{name}.png"
        im.save(p)
        return {"png": p.name, "sha256_pixels": hashlib.sha256(im.tobytes()).hexdigest()}

    def press(button, after=30):
        gb.button_press(button)
        gb.tick(3, render=True)
        gb.button_release(button)
        gb.tick(after, render=True)

    def save():
        with io.BytesIO() as f:
            gb.save_state(f)
            return f.getvalue()

    def restore(state):
        gb.load_state(io.BytesIO(state))
        gb.tick(3, render=True)

    def err(name, reason):
        failures.append({"case": name, "error": reason})

    visits, failures = [], []
    record = {"scope": "Real PyBoy 1.x name entry; not entire game, not full Zhuyin/Cangjie",
              "mode_results": {}, "failures": failures, "actual_entry_reached": False,
              "input_modes": list(MODES), "source_sym": sym.name}
    try:
        gb.hook_register(None, "NamingScreen", lambda ctx: ctx.append("entered"), visits)
        gb.tick(3600, render=True)
        press("start", 180)
        press("a", 220)
        for step in range(1, 110):
            press("a", 100)
            if visits:
                record["entered_after_A_presses"] = step
                break
        if not visits:
            err("entry", "Never reached NamingScreen from title -> new game")
        else:
            record["actual_entry_reached"] = True
            record["initial"] = {"type": memory("wNamingScreenType"),
                                 "mode": memory("wNamingScreenLetterCase"),
                                 "image": image("intro_player")}
            if record["initial"]["type"] != 1:
                err("entry", f"Expected NAME_PLAYER = 1, got {record['initial']['type']}")
            base = save()
            mode_hashes = []
            for idx, name in enumerate(MODES):
                restore(base)
                for _ in range(idx):
                    press("select", 40)
                got = memory("wNamingScreenLetterCase")
                nlines = memory("wIMEMaxLine")
                case = {"mode": got, "lines": nlines, "before": image(f"{name}_screen"),
                        "routes_tried": [], "input_success": False, "deletion_success": False}
                record["mode_results"][name] = case
                mode_hashes.append(case["before"]["sha256_pixels"])
                expected = [1, 11, 12, 12][idx]
                if got != idx:
                    err(name, f"Wrong SELECT mode: expected {idx}, got {got}")
                    continue
                if nlines != expected:
                    err(name, f"Wrong candidate line count: expected {expected}, got {nlines}")
                mode_state = save()
                for route in ROUTES:
                    restore(mode_state)
                    for key in route:
                        press(key, 14)
                    before = memory("wNamingScreenCurNameLength")
                    compose = memory("wIMEPinyin")
                    press("a", 45)
                    after = memory("wNamingScreenCurNameLength")
                    is_chinese = idx in (2,3)
                    if idx == 0:
                        success = memory("wIMEPinyin") != compose
                    else:
                        success = (after - before == (2 if is_chinese else 1))
                    case["routes_tried"].append({"route": list(route), "delta_bytes": after-before,
                                                  "composition_changed": memory("wIMEPinyin") != compose})
                    if success:
                        case["input_success"] = True
                        case["tested_route"] = list(route)
                        case["after_input"] = image(f"{name}_typed")
                        press("b", 45)
                        case["deletion_success"] = (
                            memory("wNamingScreenCurNameLength") == before if idx != 0
                            else memory("wIMEPinyin") == compose
                        )
                        case["after_delete"] = image(f"{name}_deleted")
                        break
                if not case["input_success"]:
                    err(name, "Actual controller A did not insert/composite expected type")
                if not case["deletion_success"]:
                    err(name, "Actual B button did not erase chosen input")
            if len(set(mode_hashes)) != 4:
                err("visual", "Two or more mode screens are pixel-identical")
            restore(base)
            for _ in range(4):
                press("select", 40)
            record["mode_wraparound"] = (memory("wNamingScreenLetterCase") == 0)
            if not record["mode_wraparound"]:
                err("wraparound", "Four SELECT presses did not cycle back to Pinyin")
    except Exception as ex:
        err("runner", f"{type(ex).__name__}: {ex}")
    finally:
        gb.stop(save=False)
        record["passed"] = not failures and record["actual_entry_reached"]
        report = output / "zh_tw_naming_qa_report.json"
        report.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"passed":record["passed"], "modes":{k:{"typed":v.get("input_success"), "deleted":v.get("deletion_success"), "route":v.get("tested_route")} for k,v in record["mode_results"].items()}, "failures": failures}, ensure_ascii=False))
    if strict and failures:
        raise SystemExit(2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--output", type=Path, default=Path("."))
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    test(args.rom, args.output, args.strict)
