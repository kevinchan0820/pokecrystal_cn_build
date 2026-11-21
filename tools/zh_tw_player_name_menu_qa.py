#!/usr/bin/env python3
"""Verify the *actual compiled player-naming selection strings* are zh-Hant.

These are inline db_w strings in source/data/player_names.asm, NOT workbook
cells, so changing the translated XLSX cannot repair them.
"""
import argparse
import json
import re
from pathlib import Path

EXPECTED = {"自己決定": 2, "小陽": 1, "克麗絲": 1, "千瑤": 1}
FORBIDDEN = ("自己决定", "小阳", "克丽丝", "千瑶")

def audit(text):
    values = [v.removesuffix("@") for v in re.findall(r'(?m)^\s*db_w\s+"([^"]+)"', text)]
    failures = []
    for bad in FORBIDDEN:
        if bad in text:
            failures.append("Simplified source still present: " + bad)
    for good, needed in EXPECTED.items():
        count = values.count(good)
        if count != needed:
            failures.append("Expected " + repr(good) + " in db_w " +
                            str(needed) + " times, got " + str(count))
    return {"verified": not failures,
            "expected": EXPECTED,
            "forbidden": list(FORBIDDEN),
            "observed_db_w": values,
            "failures": failures,
            "source": "data/player_names.asm"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    p.add_argument("--report", type=Path, default=Path("zh_tw_player_names_report.json"))
    args = p.parse_args()
    name_file = args.source / "data/player_names.asm"
    result = audit(name_file.read_text(encoding="utf-8"))
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verified": result["verified"],
                      "failures": result["failures"]}, ensure_ascii=False))
    if not result["verified"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
