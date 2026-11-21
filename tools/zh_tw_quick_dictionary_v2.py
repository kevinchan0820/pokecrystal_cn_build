#!/usr/bin/env python3
"""Generate a pinned, Traditional-only, 8x8-friendly Quick/Cangjie dictionary.

NOT YET LINKED INTO GAME CODE. The current five-code ROM Quick table must not
be called complete; this script prepares a licensed full candidate corpus and
ROM-bank budget for a later safe engine migration.

Upstream main-table rights: MIT; pinned to cangjie-system/rime-cangjie-integrated.
The resources/ subdirectory is NOT imported (its licenses differ).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

UPSTREAM_REPO = "cangjie-system/rime-cangjie-integrated"
UPSTREAM_COMMIT = "dcfba770189078a2f7b347793c8e155c3c39275d"
UPSTREAM_FILE = "cangjie.5-base.dict.yaml"
UPSTREAM_GIT_BLOB_SHA1 = "5b405b8e0d8b37c37a639c3a6ec06af6c52b2852"
UPSTREAM_URL = ("https://raw.githubusercontent.com/" + UPSTREAM_REPO + "/"
                + UPSTREAM_COMMIT + "/" + UPSTREAM_FILE)
CHARMAP = re.compile(r'^\s*charmap_w\s+"([^"]+)"\s*,\s*\$([0-9a-fA-F]+),\s*\$([0-9a-fA-F]+)', re.M)
SOURCE_ENTRY = re.compile(r'^([a-z]{1,5})\t([^\t]+)(?:\t|$)')
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
MAX_QUICK_CANDIDATES = 8 * 255
ROM_CHUNK_TARGET_BYTES = 3000
KEYS = [""] + list(ALPHABET) + [a+b for a in ALPHABET for b in ALPHABET]


def verify_source_bytes(raw: bytes) -> None:
    blob = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    got = hashlib.sha1(blob).hexdigest()
    if got != UPSTREAM_GIT_BLOB_SHA1:
        raise ValueError("Pinned upstream Git blob mismatch: "+got)


def parse_charmap(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    result = {match.group(1) for match in CHARMAP.finditer(text)}
    if not result:
        raise ValueError("No 2-byte game glyphs found in charmap")
    return result


def build_buckets(source: str, supported: set[str], convert=lambda ch: ch):
    buckets = defaultdict(list)
    seen = set()
    scanned = 0
    excluded_missing = 0
    excluded_nontraditional = 0
    for raw in source.splitlines():
        match = SOURCE_ENTRY.match(raw)
        if not match:
            continue
        code, char = match.groups()
        if len(char) != 1:
            continue
        scanned += 1
        if char not in supported:
            excluded_missing += 1
            continue
        if convert(char) != char:
            excluded_nontraditional += 1
            continue
        quick = code if len(code) == 1 else code[0]+code[-1]
        pair = (quick, char)
        if pair in seen:
            continue
        seen.add(pair)
        buckets[quick].append(char)
    if not buckets:
        raise ValueError("No supported dictionary entries")
    bad = {code: len(chars) for code, chars in buckets.items()
           if len(chars) > MAX_QUICK_CANDIDATES}
    if bad:
        raise ValueError("Quick code candidate-page count exceeds 8-bit limit: "+str(bad))
    return buckets, {
        "upstream_rows": scanned,
        "excluded_unmapped": excluded_missing,
        "excluded_nontraditional": excluded_nontraditional,
        "unique_candidates": len(seen),
        "distinct_quick_codes": len(buckets),
    }


def emit_asm(buckets: dict[str,list[str]]):
    """Output fixed 703-index array and chunks for bank-flexible candidate data.

    Candidate strings are padded only at end. PrintIMELine jumps in 16-byte
    increments (8 glyphs per row); a two-byte @@ terminator guards far reads.
    Each chunk is <=3KB to avoid ROMX bank overflow/fragmentation.
    """
    labels = {"": "QuickV2CandidatesEmpty"}
    index = ["PUSHS", 'SECTION "Quick v2 Index", ROMX',
             "; Generated Quick v2 index: 0 empty, 1..26 one letter, 27..702 pairs.",
             "; Upstream MIT table; include full license notice when distributing.",
             "QuickV2Entry:"]
    sections = []
    section = []
    section_bytes = 0
    section_no = -1

    def next_chunk():
        nonlocal section_no,section,section_bytes
        if section:
            sections.append(section)
        section_no += 1
        section = ["PUSHS", f'SECTION "Quick v2 Candidate Chunk {section_no:02d}", ROMX']
        section_bytes = 0

    next_chunk()
    for key in KEYS:
        chars = buckets.get(key, []) if key else []
        name = "QuickV2CandidatesEmpty" if key == "" else "QuickV2_" + key.upper()
        labels[key] = name
        # One two-byte terminator; rounded up only to prevent accidental
        # bank-end high byte over-read, not an entire screen line.
        size = len(chars) * 2 + 2
        if size > ROM_CHUNK_TARGET_BYTES:
            raise ValueError("One Quick candidate group exceeds bank-safe chunk: "+key)
        if section_bytes + size > ROM_CHUNK_TARGET_BYTES:
            section.append("POPS")
            next_chunk()
        section.append(name+":")
        if chars:
            for start in range(0, len(chars), 64):
                section.append('\tdb_w "'+"".join(chars[start:start+64])+'"')
        section.append('\tdb_w "@@"')
        section_bytes += size
    section.append("POPS")
    sections.append(section)
    for key in KEYS:
        chars = buckets.get(key, []) if key else []
        pages = (len(chars)+7)//8
        if pages>255:
            raise ValueError("Candidate row count does not fit a byte: "+key)
        name = labels[key]
        index.append(f"\tdbbw {pages}, BANK({name}), {name} ; {key or '(empty)'} {len(chars)} candidate(s)")
    index.append("POPS")
    return "\n".join(index+[""]+[line for sect in sections for line in sect])+"\n", {
        "entry_slots":len(KEYS),
        "index_bytes":len(KEYS)*4,
        "candidate_bytes":sum(len(buckets.get(k,[]))*2+2 for k in KEYS),
        "source_chunks":section_no+1,
        "max_candidates_per_code":max(map(len,buckets.values())),
        "max_candidate_rows":max((len(x)+7)//8 for x in buckets.values()),
    }


def run(args):
    glyphs = parse_charmap(args.charmap)
    if args.dictionary is None:
        with urllib.request.urlopen(UPSTREAM_URL, timeout=40) as resp:
            raw=resp.read()
        verify_source_bytes(raw)
        pinned=True
    else:
        raw=args.dictionary.read_bytes()
        pinned=False
    # Required even for static tests: filtering Simplified-only characters
    # uses the exact OpenCC conversion installed by the build pipeline.
    from opencc import OpenCC
    converter = OpenCC("s2tw")
    buckets, stats=build_buckets(raw.decode("utf-8-sig"),glyphs,converter.convert)
    report = {
        "implementation_status": "DATA_PREPARED_NOT_LINKED_INTO_ROM",
        "upstream": UPSTREAM_URL, "upstream_commit":UPSTREAM_COMMIT,
        "upstream_git_blob_sha1":UPSTREAM_GIT_BLOB_SHA1 if pinned else None,
        "upstream_license": "MIT (main-table files only; resources/ excluded)",
        "dictionary_pinned":pinned,
        "glyph_map_count":len(glyphs),
        **stats,
        "essential_tests": {
            "A_has_日_曰":all(ch in buckets.get("a",[]) for ch in "日曰"),
            "AA_has_晶": "晶" in buckets.get("aa",[]),
            "AB_has_明": "明" in buckets.get("ab",[]),
            "VD_has_好": "好" in buckets.get("vd",[]),
        }
    }
    assembly,planning=emit_asm(buckets)
    report.update(planning)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(assembly,encoding="utf-8")
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.strict and (not pinned or not all(report["essential_tests"].values())):
        raise SystemExit("Dictionary generation not verified: "+str(report["essential_tests"]))
    print(json.dumps({k:report[k] for k in ("implementation_status","unique_candidates",
        "distinct_quick_codes","source_chunks","max_candidates_per_code",
        "max_candidate_rows","essential_tests")},ensure_ascii=False))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--charmap",type=Path,default=Path("pokecrystal_cn/constants/charmap_cn.asm"))
    p.add_argument("--dictionary",type=Path,default=None,help="Test fixture only; strict mode requires pinned upstream")
    p.add_argument("--output",type=Path,default=Path("generated/quick_v2_data.asm"))
    p.add_argument("--report",type=Path,default=Path("zh_tw_quick_v2_dictionary_report.json"))
    p.add_argument("--strict",action="store_true")
    run(p.parse_args())
