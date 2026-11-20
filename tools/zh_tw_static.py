#!/usr/bin/env python3
"""Translate Chinese display strings inside ASM quotes, not labels or directives."""
import argparse
import json
import re
from pathlib import Path

from opencc import OpenCC

QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"')
SKIP = {"constants/charmap_cn.asm", "constants/charmap.asm", "macros/charmap_w.asm"}
TEXT_DIRECTIVES = ("db_w", "li", "text", "line", "cont", "next", "para", "db")
# Source text often has a label and a text directive on the SAME line:
#   .PokedexString: db_w "图鉴@"
# The old first-token-only check saw ".PokedexString:" and silently missed it.
DISPLAY_LINE = re.compile(
    r"^\s*(?:(?:[A-Za-z_.][A-Za-z0-9_.$@]*)(?:::|:)\s*)?"
    r"(?:" + "|".join(TEXT_DIRECTIVES) + r")(?=\s|$)"
)


def separate_comment(line):
    """Keep comments intact, including when a quoted text contains ';'."""
    quoted = False
    escaped = False
    for i, char in enumerate(line):
        if char == '"' and not escaped:
            quoted = not quoted
        if char == ";" and not quoted:
            return line[:i], line[i:]
        if char == "\\" and not escaped:
            escaped = True
        else:
            escaped = False
    return line, ""



def rewrite(source, config):
    converter = OpenCC(config)
    modified = {}
    for path in source.rglob("*.asm"):
        rel = path.relative_to(source).as_posix()
        if rel in SKIP:
            continue
        old_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        new_lines = []
        lines_edited = 0
        for line in old_lines:
            if not DISPLAY_LINE.match(line):
                new_lines.append(line)
                continue
            # Translate the command text, not any quoted wording in a comment.
            code, comment = separate_comment(line)
            def convert(m):
                text = m.group(1)
                if not any("\u3400" <= ch <= "\u9fff" for ch in text):
                    return m.group(0)
                return '"' + converter.convert(text) + '"'
            updated = QUOTED.sub(convert, code) + comment
            if updated != line:
                lines_edited += 1
            new_lines.append(updated)
        if lines_edited:
            path.write_text("".join(new_lines), encoding="utf-8")
            modified[rel] = lines_edited
    return modified


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("pokecrystal_cn"))
    p.add_argument("--opencc", default="s2twp")
    p.add_argument("--report", type=Path, default=Path("zh_tw_static_report.json"))
    a = p.parse_args()
    result = rewrite(a.source, a.opencc)
    a.report.write_text(json.dumps(
        {"edited_files": len(result), "edited_lines": sum(result.values()), "files": result},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Converted {sum(result.values())} Chinese ASM lines in {len(result)} files")


if __name__ == "__main__":
    main()
