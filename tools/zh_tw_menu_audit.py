#!/usr/bin/env python3
"""Fail builds if common menu text still uses Simplified-Chinese vocabulary.

This is a targeted regression gate for untranslated inline-label strings in
the original Crystal assembly. It does not replace gameplay screenshot QA.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from opencc import OpenCC
from zh_tw_static import DISPLAY_LINE, QUOTED, separate_comment


def audit(root: Path, conversion: str) -> dict:
    converter = OpenCC(conversion)
    folders = [
        "engine/menus", "engine/items", "engine/pokedex",
        "engine/pokemon", "data/mon_menu.asm",
        "engine/events/pokecenter_pc.asm",
    ]
    files = []
    for location in folders:
        target = root / location
        if target.is_file():
            files.append(target)
        elif target.is_dir():
            files.extend(target.rglob("*.asm"))
    violations = []
    examined = 0
    for file in sorted(set(files)):
        for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
            if not DISPLAY_LINE.match(line):
                continue
            code, _ = separate_comment(line)
            for match in QUOTED.finditer(code):
                original = match.group(1)
                if not any("\u3400" <= ch <= "\u9fff" for ch in original):
                    continue
                examined += 1
                translated = converter.convert(original)
                if translated != original:
                    violations.append({
                        "file": file.relative_to(root).as_posix(),
                        "line": number,
                        "original": original,
                        "suggested": translated,
                    })
    return {
        "scanned_files": len(set(files)),
        "scanned_chinese_strings": examined,
        "unconverted_menu_strings": len(violations),
        "violations": violations,
        "scope": folders,
        "note": "A pass here is not proof that graphics or all runtime screens are localized.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("build"))
    parser.add_argument("--report", type=Path, default=Path("zh_tw_menu_audit_report.json"))
    parser.add_argument("--opencc", default="s2twp")
    args = parser.parse_args()
    result = audit(args.source, args.opencc)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"Menu audit: {result['scanned_files']} files, "
          f"{result['scanned_chinese_strings']} Chinese strings, "
          f"{result['unconverted_menu_strings']} incomplete translations")
    if result["violations"]:
        for item in result["violations"][:30]:
            print(f"  {item['file']}:{item['line']} {item['original']} -> {item['suggested']}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
