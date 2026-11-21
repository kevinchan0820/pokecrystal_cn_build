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
             "wNamingScreenCursorObjectPointer", "wTilemap", "wAttrmap")
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
        # Mode 4/Quick must show the rasterized Traditional label "速成".
        # 5 modes x 3 tiles start at $6e, so Quick starts at $7a.
        # Check actual tilemap rather than assuming the text engine can
        # render 12x12 double-byte characters on this 8px header row.
        bank, start = addr["wTilemap"]
        tile = lambda row, col: gb.memory[bank, start + row*20 + col]
        expected_label_tiles = [0x7a, 0x7b, 0x7c]
        actual_label_tiles = [tile(6, col) for col in range(1, 4)]
        result["quick_label_tiles"] = {
            "actual": actual_label_tiles, "expected": expected_label_tiles}
        if actual_label_tiles != expected_label_tiles:
            raise AssertionError("Mode status must show Taiwanese raster title 速成")
        # The following tile row must remain blank, not a damaged lower
        # half or text spilling into the keyboard.
        empty_tile = tile(7, 12)
        if any(tile(7, x) != empty_tile for x in range(1, 10)):
            raise AssertionError("Mode status spills into blank spacer row")
        stable_keys = keyboard()
        # Rime-root labels MUST occupy precisely the old 8x8 A-Z cells.
        # Compare bytes in actual PyBoy VRAM (not only source code).
        source_roots = (source / "gfx/naming_screen/cangjie_roots.1bpp").read_bytes()
        samples = (0, 1, 2, 21, 25)  # 日 月 金 女 符
        def key_pixels(i):
            return bytes(gb.memory[0, 0x8800 + i*16 + n] for n in range(16))
        def expanded_root(i):
            return bytes(v for row in source_roots[i*8:i*8+8] for v in (row, row))
        for i in samples:
            if key_pixels(i) != expanded_root(i):
                raise AssertionError(f"Quick key {chr(65+i)} is not the Rime root bitmap")
        quick_screen = gb.screen.image.copy()
        snapshot("quick_radicals_raw")
        attr_bank, attr_start = addr["wAttrmap"]
        keyboard_attrs = [gb.memory[attr_bank, attr_start + row*20 + col]
                          for row in (8,9) for col in (1,2,3,4,5,7,8,9,10,11)]
        def vram_bytes(bank, key_index):
            try:
                return [gb.memory[bank, 0x8800+key_index*16+n] for n in range(16)]
            except Exception as exc:
                return [type(exc).__name__ + ": " + str(exc)]
        result["root_display_diagnostics"] = {
            "keyboard_tile_ids": [tile(8,x) for x in range(1,6)],
            "keyboard_attributes": keyboard_attrs,
            "attribute_bank1_count": sum((attr & 8) != 0 for attr in keyboard_attrs),
            "letter_a_vram_bank0": vram_bytes(0,0),
            "letter_a_vram_bank1": vram_bytes(1,0),
            "root_a_expected": list(expanded_root(0)),
        }
        # The original naming keyboard uses bank 1 on the first row
        # (A-P), bank 0 on the second row (Q-Z). Changing that hardware
        # attribute breaks the tested Quick input codes (AA/AB).
        if not all(x & 8 for x in keyboard_attrs[:10]) or any(x & 8 for x in keyboard_attrs[10:]):
            raise AssertionError("Original first-row/second-row VRAM bank mapping was corrupted")
        for i in (0, 1, 2, 3, 5, 10, 15):
            if vram_bytes(1, i) != list(expanded_root(i)):
                raise AssertionError(f"Visible Quick key {chr(i+65)} is still Latin in VRAM bank1")
        # SELECT from Quick to Pinyin must restore the stock Latin alphabet.
        key("select", 35)
        if val("wNamingScreenLetterCase") != 0:
            raise AssertionError("Quick -> Pinyin mode transition failed")
        if any(key_pixels(i) == expanded_root(i) for i in samples):
            raise AssertionError("Latin keyboard glyphs not restored after leaving Quick")
        latin_screen = gb.screen.image.copy()
        snapshot("pinyin_latin_restored")
        result["root_display_diagnostics"]["latin_letter_a_bank0"] = vram_bytes(0,0)
        result["root_display_diagnostics"]["latin_letter_a_bank1"] = vram_bytes(1,0)
        for i in (0, 1, 2, 3):
            if vram_bytes(1,i) == list(expanded_root(i)):
                raise AssertionError("Latin font not restored in VRAM bank1 after leaving Quick")
        if quick_screen.crop((8,64,152,80)).tobytes() == latin_screen.crop((8,64,152,80)).tobytes():
            raise AssertionError("Key display still looks identical in Latin and Cangjie modes")
        # Return to Quick: original keycodes and locations must remain intact.
        for _ in range(4):
            key("select", 35)
        if val("wNamingScreenLetterCase") != 4:
            raise AssertionError("Could not switch back to Quick")
        for i in samples:
            if key_pixels(i) != expanded_root(i):
                raise AssertionError("Cangjie glyphs not restored on entering Quick again")
        for i in (0,1,2,3,5,10,15):
            if vram_bytes(1,i) != list(expanded_root(i)):
                raise AssertionError("Cangjie keys not restored in first-row VRAM bank1")
        if keyboard() != stable_keys:
            raise AssertionError("Keyboard tile IDs changed; Quick lookup code would be corrupted")
        result["root_keyboard_qa"] = {
            "rime_reference": "rime/rime-cangjie cangjie5_express.schema.yaml",
            "checked_roots": ["日", "月", "金", "女", "符"],
            "glyph_size_px": [8, 8],
            "quick_to_pinyin_restoration": True,
            "original_letter_keycodes_preserved": True,
            "quick_screenshot": snapshot("quick_radical_keyboard")
        }
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
