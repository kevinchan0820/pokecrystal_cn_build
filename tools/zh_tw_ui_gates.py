#!/usr/bin/env python3
"""Protect the most visible Taiwan/HK GBC menu labels and their meaning."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def require(actual, expected, errors, field):
    if expected not in actual:
        errors.append({"field": field, "expected": expected})


def inspect(source: Path):
    options = (source / "engine/menus/options_menu.asm").read_text(encoding="utf-8")
    start = (source / "engine/menus/start_menu.asm").read_text(encoding="utf-8")
    main = (source / "engine/menus/main_menu.asm").read_text(encoding="utf-8")
    errors = []

    option_labels = options.split("StringOptions:", 1)[1].split("GetOptionPointer:", 1)[0]
    for term in ('"文字速度"', '"戰鬥動畫"', '"對戰規則"',
                 '"列印濃度"', '"邊框樣式"', '"選單說明"'):
        require(option_labels, term, errors, "options-label")

    for wrong in ("類型", "类型", "邊框       類型", "比赛规则"):
        if wrong in option_labels:
            errors.append({"field": "options-legacy", "found": wrong})
    # The vanilla GBC engine uses a numeric 1..8 frame selector. Keep the
    # dynamic value instead of writing static labels 1..8 into the row.
    frame = options.split("Options_Frame:", 1)[1].split("Options_Cancel:", 1)[0]
    for instr in ("maskbits NUM_FRAMES", "UpdateFrame:",
                  "hlcoord 15, 14", 'add "1"'):
        require(frame, instr, errors, "frame-1-to-8")

    scene = options.split("Options_BattleScene:", 1)[1].split("Options_BattleStyle:", 1)[0]
    for label in ('"開啟@"', '"關閉@"'):
        require(scene, label, errors, "battle-animation-toggle")

    for label in ('"儲存@"', '"調整遊戲設定"', '"與操作選項@"',
                  '"儲存目前的"', '"冒險進度@"'):
        require(start, label, errors, "start-menu")

    # Options is not Reset. The title menu must display the actual command.
    require(main, '"設定@"', errors, "title-menu-options")
    for legacy in ('"重新設置@"', '"重新設定@"'):
        if legacy in main:
            errors.append({"field": "title-menu-options", "found": legacy})

    return {
        "verified": not errors, "errors": errors,
        "frame_style": "dynamic selection 1 through 8",
        "actual_scope": "ASM source strings after translation + contextual UI patches",
        "visual_layout_verified": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    p.add_argument("--report", type=Path, default=Path("zh_tw_ui_terminology_report.json"))
    args = p.parse_args()
    result = inspect(args.source)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    if result["errors"]:
        for item in result["errors"]:
            print("FAILED", item)
        raise SystemExit(2)
    print("GBC options, 1–8 border styles and save/menu semantics: PASS")


if __name__ == "__main__":
    main()
