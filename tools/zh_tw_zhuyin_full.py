#!/usr/bin/env python3
"""Generate a true Taiwan Zhuyin symbol+tone dictionary for Crystal GBC.

Pinned MIT McBopomofo BPMFBase.txt single-character readings.
41 phonetic symbols include 37 ㄅ..ㄦ plus ˊ ˇ ˋ ˙ (implicit first tone).
No Latin Pinyin transliteration. A game-byte $80..$A8 represents one
phonetic symbol. Four-byte syllable keys map to banked Traditional candidates.

DATA GENERATION ONLY: actual game integration and PyBoy tests still required.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path
from opencc import OpenCC
from zh_tw_quick_dictionary_v2 import CHARMAP,ROM_CHUNK_TARGET_BYTES

SOURCE_REPO="openvanilla/McBopomofo"
SOURCE_COMMIT="1b7fbb999a354ba80e5cf20820ddd4093c6ed77e"
SOURCE_PATH="Source/Data/BPMFBase.txt"
SOURCE_BLOB="6febbf06265bbde71e5234a3e8c52dd3cf636a40"
SOURCE_URL=("https://raw.githubusercontent.com/"+SOURCE_REPO+"/"+
            SOURCE_COMMIT+"/"+SOURCE_PATH)
SYMBOLS="ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦˊˇˋ˙"
assert len(SYMBOLS)==41 and len(set(SYMBOLS))==41
CODE={ch:0x80+i for i,ch in enumerate(SYMBOLS)}
SOURCE_ENTRY=re.compile(r'^(\S+)\s+(\S+)\s+(\S+)\s+')
PREFERRED={"ㄇㄧㄥˊ":"明","ㄚ":"阿"}

def verify_source(data):
    blob=b"blob "+str(len(data)).encode()+b"\0"+data
    digest=hashlib.sha1(blob).hexdigest()
    if digest!=SOURCE_BLOB:raise ValueError("McBopomofo source not pinned: "+digest)

def charmap(path):
    data=path.read_text(encoding="utf-8")
    chars={m.group(1):(int(m.group(2),16),int(m.group(3),16))
           for m in CHARMAP.finditer(data)}
    if len(chars)<100:raise ValueError("GBC charmap truncated")
    return chars

def collect(readings,glyphs,convert=None):
    if convert is None:convert=OpenCC("s2tw").convert
    syllables=defaultdict(list)
    seen=set()
    scanned=unmapped=simplified=oversized=0
    for line in readings.splitlines():
        match=SOURCE_ENTRY.match(line)
        if not match:continue
        char,reading,_=match.groups()
        if len(char)!=1 or not reading or any(sym not in CODE for sym in reading):
            continue
        scanned+=1
        if len(reading)>4:
            oversized+=1
            continue
        if char not in glyphs:
            unmapped+=1
            continue
        if convert(char)!=char:
            simplified+=1
            continue
        if (reading,char) in seen:
            continue
        seen.add((reading,char))
        syllables[reading].append(char)
    if not syllables:raise ValueError("No usable Zhuyin glyphs")
    for reading,preferred in PREFERRED.items():
        if preferred in syllables[reading]:
            syllables[reading].remove(preferred)
            syllables[reading].insert(0,preferred)
    for reading,items in syllables.items():
        if len(items)>8*255:raise ValueError("8-bit page count overflow: "+reading)
    return syllables,{
        "source_rows":scanned,"excluded_missing_glyph":unmapped,
        "excluded_simplified":simplified,"excluded_long_reading":oversized,
        "distinct_syllable_codes":len(syllables),
        "distinct_reading_candidate_pairs":len(seen),
        "max_candidates_per_syllable":max(map(len,syllables.values())),
    }

def record_label(reading):
    return "ZhuyinRead_"+"_".join(str(CODE[c]-0x80) for c in reading)

def emit_asm(syllables):
    by_first=defaultdict(list)
    for reading in sorted(syllables,key=lambda s:tuple(CODE[c] for c in s)):
        by_first[reading[0]].append(reading)
    index=["PUSHS",'SECTION "Zhuyin 41 First Index", ROMX',
           "; Each first symbol points to a group of fixed 8-byte syllable records",
           "ZhuyinFirstIndex:"]
    for i,ch in enumerate(SYMBOLS):
        rows=by_first[ch]
        if len(rows)>255:raise ValueError("Too many syllables for initial "+ch)
        label="ZhuyinNoReadings" if not rows else "ZhuyinFirst_"+str(i)
        index.append("\tdbbw "+str(len(rows))+", BANK("+label+"), "+label)
    index.append("POPS")
    chunks=[]
    current=[]
    used=0
    count=-1
    def new_chunk(kind):
        nonlocal used,current,count
        if current:
            current.append("POPS")
            chunks.extend(current)
        count+=1
        current=["PUSHS",'SECTION "Zhuyin '+kind+' '+format(count,'02d')+'", ROMX']
        used=0
    new_chunk("records")
    current.extend(["ZhuyinNoReadings:",'\tdb "@@@@", 0, BANK(ZhuyinEmpty), LOW(ZhuyinEmpty), HIGH(ZhuyinEmpty)'])
    used+=8
    for i,ch in enumerate(SYMBOLS):
        rows=by_first[ch]
        if not rows:continue
        required=len(rows)*8
        if required>ROM_CHUNK_TARGET_BYTES:raise ValueError("Huge initial: "+ch)
        if used+required>ROM_CHUNK_TARGET_BYTES:new_chunk("records")
        current.append("ZhuyinFirst_"+str(i)+":")
        for reading in rows:
            key=[CODE[c] for c in reading]+[0x50]*(4-len(reading))
            name=record_label(reading)
            pages=(len(syllables[reading])+7)//8
            nums=", ".join("$"+format(c,"02x") for c in key)
            current.append("\tdb "+nums+", "+str(pages)+", BANK("+name+
                           "), LOW("+name+"), HIGH("+name+")")
        used+=required
    current.append("POPS")
    chunks.extend(current)
    # Add separate candidate chunks.
    out=[]
    cur=[]
    used=0
    candidate_chunk=-1
    def new_candidate_chunk():
        nonlocal cur,used,candidate_chunk
        if cur:
            cur.append("POPS")
            out.extend(cur)
        candidate_chunk+=1
        cur=["PUSHS",'SECTION "Zhuyin candidates '+format(candidate_chunk,'02d')+'", ROMX']
        used=0
    new_candidate_chunk()
    cur.extend(["ZhuyinEmpty:",'\tdb_w "@@"'])
    used+=2
    for reading in sorted(syllables,key=lambda s:tuple(CODE[c] for c in s)):
        chars=syllables[reading]
        size=len(chars)*2+2
        if size>ROM_CHUNK_TARGET_BYTES:
            raise ValueError("One syllable exceeds ROM candidate bank: "+reading)
        if used+size>ROM_CHUNK_TARGET_BYTES:new_candidate_chunk()
        cur.append(record_label(reading)+":")
        for i in range(0,len(chars),64):
            cur.append('\tdb_w "'+"".join(chars[i:i+64])+'"')
        cur.append('\tdb_w "@@"')
        used+=size
    cur.append("POPS")
    out.extend(cur)
    return "\n".join(index+[""]+chunks+[""]+out)+"\n",{
        "first_index_bytes":41*4,
        "syllable_record_bytes":sum(len(v)*8 for v in by_first.values())+8,
        "candidate_bytes":sum(len(v)*2+2 for v in syllables.values())+2,
        "candidate_chunks":candidate_chunk+1,
        "record_chunks":count+1,
        "max_first_group":max(map(len,by_first.values())),
        "max_candidate_rows":max((len(v)+7)//8 for v in syllables.values()),
    }

def emit_symbol_map(glyphs):
    missing=[ch for ch in SYMBOLS if ch not in glyphs]
    if missing:raise ValueError("Font missing phonetic symbols: "+"".join(missing))
    lines=["; generated after glyph remap, 41 symbols x two DFS code bytes",
           "PUSHS",'SECTION "Zhuyin 12px symbol codes", ROMX',
           "ZhuyinSymbolCodes:"]
    for ch in SYMBOLS:
        hi,lo=glyphs[ch]
        lines.append("\tdb $"+format(hi,"02x")+", $"+format(lo,"02x")+" ; "+ch)
    return "\n".join(lines+["POPS",""])

def run(args):
    glyphs=charmap(args.charmap)
    if args.dictionary:
        raw=args.dictionary.read_bytes();pinned=False
    else:
        with urllib.request.urlopen(SOURCE_URL,timeout=50) as f:raw=f.read()
        verify_source(raw);pinned=True
    entries,stats=collect(raw.decode("utf-8-sig"),glyphs)
    asm,layout=emit_asm(entries)
    report={"stage":"DICTIONARY_GENERATED, GAMEPLAY UNVERIFIED",
            "source_url":SOURCE_URL,"commit":SOURCE_COMMIT,
            "git_blob_sha1":SOURCE_BLOB if pinned else None,"pinned":pinned,
            "licence":"MIT OpenVanilla McBopomofo",
            "symbols":"".join(SYMBOLS),
            "all_symbols_available":all(c in glyphs for c in SYMBOLS),
            "acceptance":{"明":"明" in entries.get("ㄇㄧㄥˊ",[]),
                          "阿":"阿" in entries.get("ㄚ",[])},**stats,**layout}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(asm,encoding="utf-8")
    if args.symbol_map:
        args.symbol_map.parent.mkdir(parents=True,exist_ok=True)
        args.symbol_map.write_text(emit_symbol_map(glyphs),encoding="utf-8")
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.strict and (not pinned or not all(report["acceptance"].values())
                        or not report["all_symbols_available"]):
        raise SystemExit("Zhuyin corpus strict acceptance failed")
    print(json.dumps({k:report[k] for k in ("stage","distinct_syllable_codes",
        "distinct_reading_candidate_pairs","candidate_chunks",
        "max_candidate_rows","acceptance")},ensure_ascii=False))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dictionary",type=Path,default=None)
    p.add_argument("--charmap",type=Path,default=Path("pokecrystal_cn/constants/charmap_cn.asm"))
    p.add_argument("--output",type=Path,default=Path("generated/zhuyin_v1_data.asm"))
    p.add_argument("--symbol-map",type=Path,default=None)
    p.add_argument("--report",type=Path,default=Path("zh_tw_zhuyin_v1_report.json"))
    p.add_argument("--strict",action="store_true")
    run(p.parse_args())
