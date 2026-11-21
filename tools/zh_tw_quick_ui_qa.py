#!/usr/bin/env python3
"""GBC Quick UI regression: actual D-pad code VD -> 好 and keyboard integrity.

This test refuses to call a candidate lookup a usable IME unless the code
was really entered through the GBC controller, the correct candidate
rendered, and the player-name buffer contains the right character.
"""
from __future__ import annotations

import argparse
from collections import deque
import io
import json
import re
from pathlib import Path
from pyboy import PyBoy

from zh_tw_quick_pyboy import ROUTES, char_code


def run(rom, source, folder):
    folder.mkdir(parents=True, exist_ok=True)
    sym = next((p for p in rom.parent.glob("*.sym")
                if "wNamingScreenLetterCase" in p.read_text(errors="ignore")), None)
    if sym is None:
        raise FileNotFoundError("ROM .sym symbols missing")
    gb = PyBoy(str(rom), symbols=str(sym), window="null", sound_emulated=False)
    gb.set_emulation_speed(0)
    names = ("wNamingScreenLetterCase", "wIMEPinyin", "wIMEMaxLine",
             "wIMEAddr", "wIMEBank", "wPlayerName", "wNamingScreenCurNameLength",
             "wNamingScreenCursorObjectPointer", "wTilemap")
    addr = {name: gb.symbol_lookup(name) for name in names}
    entry = []
    gb.hook_register(None, "NamingScreen", lambda o: o.append(True), entry)
    failures = []
    result = {"test": "real Quick VD -> 好, keyboard unaffected by label/code",
              "scenarios": {}, "failures": failures}

    def val(symbol, index=0):
        bank, offset = addr[symbol]
        return gb.memory[bank, offset + index]

    def key(name, delay=28):
        gb.button_press(name)
        gb.tick(3, render=True)
        gb.button_release(name)
        gb.tick(delay, render=True)

    def state():
        with io.BytesIO() as f:
            gb.save_state(f)
            return f.getvalue()

    def restore(saved):
        gb.load_state(io.BytesIO(saved))
        gb.tick(2, render=True)

    def pos():
        pointer = val("wNamingScreenCursorObjectPointer") | (
            val("wNamingScreenCursorObjectPointer", 1) << 8)
        # constants/sprite_anim_constants.asm: VAR1 = 0xC, VAR2 = 0xD
        return gb.memory[0, pointer + 0xC], gb.memory[0, pointer + 0xD]

    def keyboard():
        bank, offset = addr["wTilemap"]
        return [gb.memory[bank, offset + row*20 + col]
                for row in (8, 9, 10) for col in range(20)]

    def snapshot(name):
        file = folder / f"zh_tw_quick_ui_{name}.png"
        gb.screen.image.copy().save(file)
        return file.name

    def find_letter(saved, wanted, nth, max_states=105):
        """BFS real cursor movement, restricted to the two alphabet rows."""
        queue = deque([(saved, [])])
        seen = set()
        while queue and len(seen) < max_states:
            current, path = queue.popleft()
            restore(current)
            xy = pos()
            if xy in seen:
                continue
            seen.add(xy)
            if xy[1] <= 1:
                key("a")
                if val("wIMEPinyin", nth) == wanted:
                    return path, state()
            for button in ("right", "down", "left", "up"):
                restore(current)
                key(button, 10)
                nxt = pos()
                if nxt[1] <= 1 and nxt not in seen:
                    queue.append((state(), path + [button]))
        raise AssertionError(
            f"Couldn't type target input byte {wanted:02X} using real keyboard "
            f"after exploring {len(seen)} cursor positions")

    try:
        gb.tick(3600, render=True)
        key("start", 180)
        key("a", 220)
        for _ in range(110):
            key("a", 100)
            if entry:
                break
        if not entry:
            raise AssertionError("No actual naming screen entry")
        for _ in range(4):
            key("select")
        if val("wNamingScreenLetterCase") != 4:
            raise AssertionError("Quick mode wasn't selected")

        result["initial_image"] = snapshot("quick_initial")
        stable_keys = keyboard()
        baseline = state()
        # Read the *same input encoding used by the assembled dictionary*.
        table_bank, table_addr = gb.symbol_lookup("QuickTB")
        # QuickTB has six seven-byte keys: empty, A, AA, AB, AD, VD.
        key_v = gb.memory[table_bank, table_addr + 5*7]
        key_d = gb.memory[table_bank, table_addr + 5*7 + 1]

        path_v, first_state = find_letter(baseline, key_v, 0)
        restore(first_state)
        result["code_V_image"] = snapshot("typed_V")
        if keyboard() != stable_keys:
            raise AssertionError("Entering V overwrote alphabet keyboard tiles")
        path_d, second_state = find_letter(first_state, key_d, 1)
        restore(second_state)
        result["code_VD_image"] = snapshot("typed_VD")
        if keyboard() != stable_keys:
            raise AssertionError("Entering VD overwrote alphabet keyboard tiles")
        candidate_bank, pointer = gb.symbol_lookup("QuickCandidatesVD")
        got_pointer = (val("wIMEBank"),
                       val("wIMEAddr") | val("wIMEAddr", 1) << 8)
        if got_pointer != (candidate_bank, pointer):
            raise AssertionError(f"VD candidate lookup wrong: {got_pointer}")
        result["scenarios"]["code_to_candidate"] = {
            "typed": "VD", "first_route": path_v, "second_route": path_d,
            "candidate": "好", "lookup_pointer": list(got_pointer),
            "keyboard_preserved": True}
        expected = char_code(source / "constants/charmap_cn.asm", "好")
        for route in ROUTES:
            restore(second_state)
            for d in route:
                key(d, 18)
            key("a", 45)
            if val("wNamingScreenCurNameLength") != 2:
                continue
            given = [val("wPlayerName"), val("wPlayerName", 1)]
            if given == expected:
                result["scenarios"]["name_written"] = {
                    "name": "好", "actual_name_bytes": given,
                    "expected_name_bytes": expected,
                    "route": list(route), "screen": snapshot("name_HAO")}
                break
        if "name_written" not in result["scenarios"]:
            raise AssertionError("VD displayed 好 but could not commit the glyph using GBC keys")
    except Exception as exc:
        failures.append(type(exc).__name__ + ": " + str(exc))
    finally:
        gb.stop(save=False)
        result["passed"] = not failures and len(result["scenarios"]) == 2
        report = folder / "zh_tw_quick_ui_report.json"
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        print(json.dumps({"passed": result["passed"], "scenarios": result["scenarios"],
                          "failures": failures}, ensure_ascii=False))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("rom", type=Path)
    p.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    p.add_argument("--output", type=Path, default=Path("."))
    a = p.parse_args()
    if not run(a.rom, a.source, a.output)["passed"]:
        raise SystemExit(2)
