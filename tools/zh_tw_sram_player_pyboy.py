#!/usr/bin/env python3
"""Real-controller player-name -> in-game SAVE -> battery SRAM -> reboot acceptance.

This test NEVER substitutes PyBoy save_state() for an in-game save. A
save_state snapshot is used only to search a D-pad route to the game's SAVE
menu. The actual accepted path must run SavePlayerData on GBC CPU, write
cartridge SRAM, stop the emulator into an isolated RAM buffer, and be loaded
by a fresh emulator instance using CONTINUE. No ROM or copyrighted RAM is
included in test artifacts.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
from pyboy import PyBoy


def run(rom: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    sym = next((p for p in rom.parent.glob("*.sym")
                if "wPlayerName" in p.read_text(errors="ignore")
                and "sPlayerData" in p.read_text(errors="ignore")), None)
    if sym is None:
        raise AssertionError("Missing ROM symbol file containing SRAM and player name")
    keys = ("wPlayerName", "wPlayerData", "sPlayerData", "wSaveFileExists",
            "wNamingScreenLetterCase", "wNamingScreenCurNameLength", "wMenuCursorY")
    evidence = {"verified": False, "scenarios": {}, "failures": [],
                "scope": "Real player-name game SAVE and battery SRAM reboot (not Pokemon nicknames)"}
    rom_emulator = None
    reboot = None
    try:
        rom_emulator = PyBoy(str(rom), symbols=str(sym), window="null",
                            sound_emulated=False)
        rom_emulator.set_emulation_speed(0)
        addr = {name: rom_emulator.symbol_lookup(name) for name in keys}
        entered, start_menu, save_menu, saved_player = [], [], [], []
        rom_emulator.hook_register(None, "NamingScreen",
                                   lambda events: events.append(True), entered)
        rom_emulator.hook_register(None, "StartMenu",
                                   lambda events: events.append(True), start_menu)
        rom_emulator.hook_register(None, "SaveMenu",
                                   lambda events: events.append(True), save_menu)
        rom_emulator.hook_register(None, "SavePlayerData",
                                   lambda events: events.append(True), saved_player)
        yes_no_events = []
        rom_emulator.hook_register(None, "SaveTheGame_yesorno",
                                   lambda events: events.append(True), yes_no_events)

        def value(name, index=0):
            bank, offset = addr[name]
            return rom_emulator.memory[bank, offset + index]

        def key(name, delay=55):
            rom_emulator.button_press(name)
            rom_emulator.tick(3, render=True)
            rom_emulator.button_release(name)
            rom_emulator.tick(delay, render=True)

        def snapshot(tag):
            file = output / ("zh_tw_sram_" + tag + ".png")
            frame = rom_emulator.screen.image.copy()
            if frame.size != (160, 144):
                raise AssertionError("Not a native Game Boy screen")
            frame.save(file)
            return file.name

        def capture_state():
            buffer = io.BytesIO()
            rom_emulator.save_state(buffer)
            return buffer.getvalue()

        def restore_state(raw):
            rom_emulator.load_state(io.BytesIO(raw))
            rom_emulator.tick(2, render=True)

        rom_emulator.tick(3600, render=True)
        key("start", 180)
        key("a", 220)
        for _ in range(110):
            key("a", 95)
            if entered:
                break
        if not entered:
            raise AssertionError("Real player naming scene not reached")
        key("select", 35)
        if value("wNamingScreenLetterCase") != 1:
            raise AssertionError("Could not select English naming mode")
        key("a", 40)
        key("a", 40)
        if value("wNamingScreenCurNameLength") != 2:
            raise AssertionError("Two English characters did not enter player name")
        name = [value("wPlayerName", j) for j in range(3)]
        if name[2] != 0x50:
            raise AssertionError("Player name not properly terminated before game SAVE")
        evidence["scenarios"]["real_controller_player_name"] = {
            "name_bytes": name, "screen": snapshot("name_entered")}
        key("start", 20)
        key("a", 70)

        # Advance *real game* introduction, occasionally attempting START.
        # A game menu hook is mandatory; do not fake progress through WRAM.
        for attempt in range(420):
            key("a", 65)
            if (attempt % 8) == 7:
                key("start", 24)
            if start_menu:
                break
        evidence["intro_controller_steps"] = attempt + 1
        if not start_menu:
            raise AssertionError(
                "START menu not reached after real introductory controller presses")

        # The StartMenu CPU hook fires before its menu has finished drawing.
        # Earlier CI captured a blank menu and selected the Trainer Card with
        # down/down/A while mistaking an eventual SaveMenu hook for the route.
        # Wait for real menu initialization, then assert the selected menu
        # command is SAVE (enum 4), not merely that a hook fired.
        rom_emulator.tick(120, render=True)
        selection = rom_emulator.symbol_lookup("wMenuSelection")
        if selection is None:
            raise AssertionError("Missing wMenuSelection symbol for START menu")
        def selected_command():
            bank, offset = selection
            return rom_emulator.memory[bank, offset]

        open_menu = capture_state()
        evidence["scenarios"]["start_menu"] = {
            "screen": snapshot("start_menu"),
            "initial_command": selected_command(),
        }
        # Try down positions from the actual open START menu, checking the
        # CPU's SaveMenu hook. Search uses emulator snapshots only to
        # avoid having to replay the entire intro for every menu row.
        save_route = None
        for down_count in range(9):
            restore_state(open_menu)
            before = len(save_menu)
            for _ in range(down_count):
                key("down", 20)
            command_before_a = selected_command()
            if command_before_a != 4:  # STARTMENUITEM_SAVE
                continue
            key("a", 55)
            if len(save_menu) > before:
                save_route = ["down"] * down_count + ["a"]
                break
        if save_route is None:
            raise AssertionError("Real START menu SAVE command unreachable using D-pad")

        restore_state(open_menu)
        for button in save_route[:-1]:
            key(button, 55)
        if selected_command() != 4:
            raise AssertionError("SAVE route replay selected a different START menu command")
        key("a", 55)
        # SaveMenu hook occurs before the save question is ready for input.
        # Do not begin route search while the prompt is still rendering.
        rom_emulator.tick(120, render=True)
        evidence["scenarios"]["save_prompt"] = {
            "menu_route": save_route, "screen": snapshot("game_save_yes_no")}
        # Search *controller actions* on the actual game's yes/no screen.
        # Default choice cannot be assumed from earlier menu input.
        # State snapshots are only used to select a reliable route; the
        # final route is replayed from the original save dialog.
        at_prompt = capture_state()
        # A SaveMenu entry hook alone does not prove that the yes/no dialog
        # is visible: the routine may still be rendering text. Record a
        # controller-independent CPU checkpoint and the menu cursor so that
        # a failed CI distinguishes an unopened dialog from bad button input.
        evidence["scenarios"]["save_prompt"]["diagnostic"] = {
            "cursor_y": value("wMenuCursorY") if "wMenuCursorY" in addr else None,
            "screen_before_search": snapshot("save_prompt_before_search"),
            "save_menu_hook_count": len(save_menu),
            "save_player_hook_count": len(saved_player),
        }
        # Explore short deterministic controller sequences, not a guessed
        # default YES position. Include B to distinguish dialog dismissal.
        # Stop at first actual SavePlayerData CPU hook; then replay from the
        # identical prompt state to exclude accidental stale hook events.
        from itertools import product
        confirmation_routes = [("a",)]
        for depth in range(2, 5):
            confirmation_routes.extend(product(("up", "down", "a", "b"), repeat=depth))
        evidence["scenarios"]["save_prompt"]["route_search_size"] = len(confirmation_routes)
        confirmation = None
        for route in confirmation_routes:
            restore_state(at_prompt)
            count_before = len(saved_player)
            for button in route:
                key(button, 90)
                if len(saved_player) > count_before:
                    confirmation = list(route)
                    break
            if confirmation:
                break
        if confirmation is None:
            evidence["scenarios"]["save_prompt"]["after_rejection"] = snapshot(
                "save_yes_no_unresolved")
            evidence["scenarios"]["save_prompt"]["diagnostic"].update({
                "yes_no_hook_count": len(yes_no_events),
                "save_player_hook_count_after_search": len(saved_player),
                "screen_after_search": snapshot("save_prompt_after_search"),
            })
            raise AssertionError("In-game SAVE yes/no was never confirmed; explored "+
                                 str(len(confirmation_routes))+" actual D-pad routes; "+
                                 "inspect zh_tw_sram_player_report.json and diagnostic PNGs")
        restore_state(at_prompt)
        count_before = len(saved_player)
        for button in confirmation:
            key(button, 90)
            if len(saved_player) > count_before:
                break
        if len(saved_player) <= count_before:
            raise AssertionError("Real game SAVE did not replay verified controller route")
        rom_emulator.tick(160, render=True)
        if not value("wSaveFileExists"):
            raise AssertionError("Game never marked actual SRAM save as present")
        expected_name = name[:]
        name_after_save = [value("wPlayerName", j) for j in range(3)]
        if name_after_save != expected_name:
            raise AssertionError("In-game SAVE changed player name in WRAM")
        evidence["scenarios"]["game_save"] = {
            "save_menu_route": save_route, "confirmation_route": confirmation,
            "save_player_data_hook": True,
            "screen": snapshot("saved_in_game"),
            "name_bytes": name_after_save}

        # Verify SRAM was actually written by the game, not by emulator
        # snapshots or a manual memory injection.
        wbank, wbase = addr["wPlayerData"]
        pbank, pbase = addr["wPlayerName"]
        sbank, sbase = addr["sPlayerData"]
        if wbank != pbank:
            raise AssertionError("Unexpected player name / data WRAM bank mismatch")
        offset = pbase - wbase
        if not 0 <= offset < 0x3000:
            raise AssertionError("Player name layout outside expected player data block")
        sram_name = [rom_emulator.memory[sbank, sbase + offset + j]
                     for j in range(3)]
        if sram_name != expected_name:
            raise AssertionError("Battery SRAM does not contain committed player name")

        battery = io.BytesIO()
        rom_emulator.stop(save=True, ram_file=battery)
        rom_emulator = None
        ram_bytes = battery.getvalue()
        if len(ram_bytes) < 0x2000:
            raise AssertionError("Emulator exported no battery-backed SRAM")

        # Fresh emulator: NO load_state(), NO WRAM patch. Only battery RAM.
        reboot = PyBoy(str(rom), symbols=str(sym), window="null",
                       sound_emulated=False, ram_file=io.BytesIO(ram_bytes))
        reboot.set_emulation_speed(0)
        loaded = []
        reboot.hook_register(None, "TryLoadSaveFile",
                             lambda events: events.append(True), loaded)
        reboot_addr = reboot.symbol_lookup("wPlayerName")
        exists_addr = reboot.symbol_lookup("wSaveFileExists")

        def key_reboot(name, delay=60):
            reboot.button_press(name)
            reboot.tick(3, render=True)
            reboot.button_release(name)
            reboot.tick(delay, render=True)

        reboot.tick(3600, render=True)
        key_reboot("start", 180)
        if reboot.memory[exists_addr] != 1:
            raise AssertionError("Reboot did not recognize battery save")
        key_reboot("a", 180)  # first item CONTINUE on existing save
        for _ in range(40):
            if loaded:
                break
            key_reboot("a", 55)
        if not loaded:
            raise AssertionError("Real CONTINUE did not call TryLoadSaveFile")
        got = [reboot.memory[reboot_addr[0], reboot_addr[1] + j] for j in range(3)]
        if got != expected_name:
            raise AssertionError("After CONTINUE player name differs from saved SRAM")
        png = output / "zh_tw_sram_player_name_reloaded.png"
        reboot.screen.image.copy().save(png)
        evidence["scenarios"]["battery_reboot_continue"] = {
            "name_bytes": got, "fresh_emulator": True,
            "real_continue_hook": True, "screen": png.name,
            "ram_bytes": len(ram_bytes)}
        evidence["verified"] = True
    except Exception as error:
        evidence["failures"].append(type(error).__name__ + ": " + str(error))
    finally:
        if rom_emulator is not None:
            rom_emulator.stop(save=False)
        if reboot is not None:
            reboot.stop(save=False)
        file = output / "zh_tw_sram_player_report.json"
        file.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(json.dumps({"verified": evidence["verified"],
                          "scenarios": list(evidence["scenarios"]),
                          "failures": evidence["failures"]}, ensure_ascii=False))
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("--output", type=Path, default=Path("."))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = run(args.rom, args.output)
    if args.strict and not report["verified"]:
        raise SystemExit(2)
