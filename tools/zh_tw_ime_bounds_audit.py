#!/usr/bin/env python3
"""Bounded IME lookup regression gate: reject ROM-table overreads and broken indices.

A real Quick or Pinyin code outside the dictionary must return the empty entry.
Unbounded seven-byte table scans can interpret unrelated machine code as input
keys and lead to corrupt candidates, lockups, or unbounded execution.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

RECORD = re.compile(r'^\s*db_w\s+"([A-Z@]{7})"\s*(?:;.*)?$', re.M)
ENTRY = re.compile(r'^\s*dbbw\s+\d+\s*,\s*BANK\([^)]+\)\s*,\s*(\w+)', re.M)

def table(content, name, end):
    left = content.find(name + ":")
    right = content.find(end + ":", left + len(name) + 1)
    if left < 0 or right < 0:
        return [], ["Missing boundary marker " + name + " / " + end]
    found = RECORD.findall(content[left:right])
    return [key.rstrip("@") for key in found], []

def audit(root: Path):
    engine = (root/"engine/dfs/ime.asm").read_text(encoding="utf-8")
    quick = (root/"data/ime/ime_quick_twhk.asm").read_text(encoding="utf-8")
    pinyin = (root/"data/ime/ime_entry.asm").read_text(encoding="utf-8")
    errors = []
    qkeys, qs = table(quick, "QuickTB", "QuickTBEnd")
    pkeys, ps = table(pinyin, "PinyinTB", "PinyinTBEnd")
    errors.extend(qs + ps)
    for name, keys in (("Quick", qkeys), ("Pinyin", pkeys)):
        if not keys or keys[0] != "":
            errors.append(name+" must begin with empty fallback key")
        if keys != sorted(keys) or len(set(keys)) != len(keys):
            errors.append(name+" table must be sorted and have unique keys")
        if name == "Quick" and any(len(k)>2 for k in keys):
            errors.append("Quick code must not exceed two letters")
        if name == "Pinyin" and any(len(k)>6 for k in keys):
            errors.append("Pinyin code must not exceed six letters")
    count = len(ENTRY.findall(quick.partition("QuickTBEntry:")[2]))
    if count != len(qkeys):
        errors.append(f"Quick candidate-pointer count {count} != code count {len(qkeys)}")
    # Delimit actual ASM labels, not a branch operand 'jr nz, .start'.
    # The previous substring partition mistakenly cut off half the guard.
    match = re.search(r"(?ms)^\s*\.miss\s*\n(.*?)^\s*\.start\s*$", engine)
    miss = match.group(1) if match else ""
    for token in ("QuickTBEnd", "PinyinTBEnd"):
        if token not in miss:
            errors.append("GetPinyinNo missing end-of-table guard: "+token)
    if "ld bc, $0000" not in miss:
        errors.append("GetPinyinNo must return empty candidate on lookup exhausted")
    if len(qkeys) >= 256:
        errors.append("Quick prototype page index >=256; upgrade index/pointer strategy")
    return {"verified":not errors,"quick_codes":len(qkeys),
            "pinyin_codes":len(pkeys),"quick_examples":qkeys[:8],
            "invalid_inputs":["Z", "ZZ", "QZ", "ZZZZZZ"],
            "errors":errors,
            "scope":"Static guard test; actual D-pad invalid-code/hang and render tests also mandatory"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=Path("pokecrystal_cn"))
    parser.add_argument("--report",type=Path,default=Path("zh_tw_ime_bounds_report.json"))
    args=parser.parse_args()
    result=audit(args.source)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    if not result["verified"]:
        raise SystemExit(2)

if __name__=="__main__":
    main()
