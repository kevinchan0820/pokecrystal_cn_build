#!/usr/bin/env python3
"""Deep PyBoy naming regressions: pages, final confirmation, length, input schemes.

Uses the real 1.x Crystal ROM, CPU symbols and physical GBC button events.
No ROM or saved copyrighted state is included in test artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

from pyboy import PyBoy


def run(rom: Path, folder: Path):
    folder.mkdir(exist_ok=True, parents=True)
    sym = next((f for f in rom.parent.glob("*.sym") if "wNamingScreenLetterCase"
                in f.read_text(errors="ignore")), None)
    if sym is None:
        raise AssertionError("Compiled symbol file missing")
    py = PyBoy(str(rom), symbols=str(sym), window="null", sound_emulated=False)
    py.set_emulation_speed(0)
    addr = {name: py.symbol_lookup(name) for name in (
        "wNamingScreenLetterCase", "wIMELine", "wIMEMaxLine",
        "wNamingScreenCurNameLength", "wNamingScreenMaxNameLength",
        "wIMEPinyin", "wIMEChar", "wPlayerName"
    )}
    writes, entries = [], []
    py.hook_register(None, "NamingScreen", lambda ctx: ctx.append(1), entries)
    py.hook_register(None, "NamingScreen_StoreEntry", lambda ctx: ctx.append(1), writes)

    def read(key, offset=0):
        bank, address = addr[key]
        return py.memory[bank, address + offset]

    def press(key, after=40):
        py.button_press(key)
        py.tick(3, render=True)
        py.button_release(key)
        py.tick(after, render=True)

    def snap(label):
        im = py.screen.image.copy().convert("RGB")
        path = folder / f"zh_tw_naming_deep_{label}.png"
        im.save(path)
        return {"name": path.name, "sha256": hashlib.sha256(im.tobytes()).hexdigest()}

    def save():
        with io.BytesIO() as f:
            py.save_state(f)
            return f.getvalue()

    def restore(state):
        py.load_state(io.BytesIO(state))
        py.tick(3, render=True)

    def choose_mode(baseline, index):
        restore(baseline)
        for _ in range(index):
            press("select")
        if read("wNamingScreenLetterCase") != index:
            raise AssertionError("Cannot select naming mode " + str(index))

    def type_first_chinese():
        for key in ("down", "down", "right", "a"):
            press(key)
        return read("wNamingScreenCurNameLength")

    report = {"modes": {}, "failures": [], "source_rom": rom.name,
              "scope": "Player-name screen only, not save/restore or trade naming."}

    def check(name, work):
        try:
            report["modes"][name] = {"passed": True, **work()}
        except Exception as exc:
            report["modes"][name] = {"passed": False}
            report["failures"].append(f"{name}: {type(exc).__name__}: {exc}")

    try:
        py.tick(3600, render=True)
        press("start", 180)
        press("a", 220)
        for _ in range(110):
            press("a", 100)
            if entries:
                break
        if not entries:
            raise AssertionError("Never entered player-name screen")
        base = save()

        def check_pinyin():
            choose_mode(base, 0)
            before = read("wIMEPinyin")
            press("a")
            assert read("wIMEPinyin") != before, "Pinyin key did not build composition"
            length = type_first_chinese()
            assert length == 2, f"Could not select a Pinyin Chinese candidate: len={length}"
            return {"composed": True, "chinese_selected": True,
                    "typed": snap("pinyin_entered")}

        def check_english():
            choose_mode(base, 1)
            press("a")
            press("a")
            length = read("wNamingScreenCurNameLength")
            assert length == 2, f"Expected 2 English bytes, got {length}"
            expected = read("wPlayerName")
            write_before = len(writes)
            press("start", 20)
            press("a", 50)
            assert len(writes) > write_before, "END did not invoke NamingScreen_StoreEntry"
            assert read("wPlayerName") == expected, "Commit corrupted player-name buffer"
            return {"typed_english_chars": 2, "finish_event": True,
                    "confirmed": snap("english_confirmed")}

        def check_grid(label, index):
            choose_mode(base, index)
            got = type_first_chinese()
            assert got == 2, f"{label}: A did not insert first two-byte candidate"
            code = [read("wIMEChar"), read("wIMEChar",1)]
            assert any(code), f"{label}: invalid double-byte code"
            chosen = snap(label + "_typed")
            write_before = len(writes)
            press("start",20)
            press("a",50)
            assert len(writes) > write_before, f"{label}: END never committed"
            assert [read("wPlayerName"), read("wPlayerName",1)] == code, (
                f"{label}: committed player-name bytes differ from selected candidate")
            confirm = snap(label + "_confirmed")

            choose_mode(base,index)
            for key in ("down","down","down","a"):
                press(key,20)
            after_pg = read("wIMELine")
            page = snap(label + "_page_down")
            assert after_pg == 1, f"{label}: page-down arrow didn't advance, page={after_pg}"
            press("up",20)
            press("a",30)
            assert read("wIMELine") == 0, f"{label}: page-up arrow didn't return to page zero"

            choose_mode(base,index)
            for key in ("down","down","right"):
                press(key,20)
            cap = read("wNamingScreenMaxNameLength")
            for _ in range(8):
                press("a",20)
            entered = read("wNamingScreenCurNameLength")
            assert 0 < entered <= cap, f"{label}: name length overflow {entered} > {cap}"
            before_erase = entered
            press("b",40)
            assert read("wNamingScreenCurNameLength") == before_erase-2, (
                f"{label}: Chinese backspace did not remove two bytes")
            return {"first_selected_code":code, "confirmed_name_bytes":True,
                    "page_down_and_up":True,"max_stored_bytes":entered,
                    "allowed_name_bytes":cap,"chinese_backspace":True,
                    "screenshots":[chosen,confirm,page]}

        check("pinyin_candidate", check_pinyin)
        check("english_confirm", check_english)
        check("taiwan_grid", lambda: check_grid("taiwan",2))
        check("hongkong_grid", lambda: check_grid("hongkong",3))
    except Exception as error:
        report["failures"].append(f"setup: {type(error).__name__}: {error}")
    finally:
        py.stop(save=False)
        report["passed"] = not report["failures"] and len(report["modes"]) == 4
        (folder/"zh_tw_naming_deep_report.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2) + "\n",encoding="utf-8")
        print(json.dumps({"passed":report["passed"],"failures":report["failures"],
                          "modes":{k:v["passed"] for k,v in report["modes"].items()}},
                         ensure_ascii=False))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("--output", type=Path, default=Path("."))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    results = run(args.rom,args.output)
    if args.strict and not results["passed"]:
        raise SystemExit(2)
