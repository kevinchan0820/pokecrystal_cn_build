#!/usr/bin/env python3
"""Build full-code Cangjie5 GBC 7-byte records grouped by 703 Quick prefixes.

DATA STAGING ONLY until real GBC ROM implementation and PyBoy verify it.
Requires pinned MIT upstream main table; never imports resources/ data.
Each record = five A-Z game bytes padded '@', then two charmap bytes.
"""
import argparse
import json
import urllib.request
from pathlib import Path
from collections import defaultdict
from opencc import OpenCC
from zh_tw_quick_dictionary_v2 import (
    KEYS, ROM_CHUNK_TARGET_BYTES, UPSTREAM_URL, UPSTREAM_COMMIT,
    UPSTREAM_GIT_BLOB_SHA1, verify_source_bytes, SOURCE_ENTRY, CHARMAP)

def read_charmap(path):
    glyphs={m.group(1):(int(m.group(2),16),int(m.group(3),16))
            for m in CHARMAP.finditer(path.read_text(encoding="utf-8"))}
    if len(glyphs)<10:raise ValueError("Broken two-byte glyph map")
    return glyphs

def make_buckets(raw_text,glyphs,convert=None):
    if convert is None: convert=OpenCC("s2tw").convert
    groups=defaultdict(list)
    seen=set()
    scanned=excluded_unmapped=excluded_nontraditional=0
    exact=defaultdict(set)
    for line in raw_text.splitlines():
        m=SOURCE_ENTRY.match(line)
        if not m:continue
        code,char=m.groups()
        if len(char)!=1:continue
        scanned+=1
        if char not in glyphs:
            excluded_unmapped+=1
            continue
        if convert(char)!=char:
            excluded_nontraditional+=1
            continue
        if (code,char) in seen:continue
        seen.add((code,char))
        prefix=code if len(code)==1 else code[0]+code[-1]
        groups[prefix].append((code,glyphs[char],char))
        exact[code].add(char)
    for items in groups.values():
        items.sort(key=lambda entry:entry[0])
        if len(items)>255:raise ValueError("Cangjie prefix >255 entries")
    return groups,{
        "rows_scanned":scanned,"excluded_unmapped":excluded_unmapped,
        "excluded_nontraditional":excluded_nontraditional,
        "usable_fullcode_glyph_pairs":len(seen),
        "populated_prefix_buckets":len(groups),
        "distinct_full_codes":len(exact),
        "max_records_per_prefix":max(map(len,groups.values()),default=0),
        "max_same_full_code_candidates":max(map(len,exact.values()),default=0),
    }

def generate_asm(groups):
    index=["PUSHS",'SECTION "Cangjie v1 Prefix Index", ROMX',
           "; 703 key slots as in Quick: empty, A..Z, AA..ZZ.",
           "CangjieV1RootIndex:"]
    for key in KEYS:
        vals=groups.get(key,[])
        label="CangjieV1EmptyRecords" if not vals else "CangjieV1_"+key.upper()
        index.append("\tdbbw "+str(len(vals))+", BANK("+label+"), "+label+" ; "+(key or "(empty)"))
    index.append("POPS")
    records=[]
    chunk=-1
    this=[]
    bytecount=0
    def begin():
        nonlocal chunk,this,bytecount
        if this:
            this.append("POPS")
            records.extend(this)
        chunk+=1
        this=["PUSHS",'SECTION "Cangjie v1 Records '+format(chunk,'02d')+'", ROMX']
        bytecount=0
    begin()
    this.extend(["CangjieV1EmptyRecords:",'\tdb "@@@@@", $50, $50'])
    bytecount+=7
    for prefix in KEYS:
        vals=groups.get(prefix,[])
        if not vals:continue
        group_size=len(vals)*7
        if group_size>ROM_CHUNK_TARGET_BYTES:
            raise ValueError("Cangjie group too big for bank: "+prefix)
        if bytecount+group_size>ROM_CHUNK_TARGET_BYTES:begin()
        this.append("CangjieV1_"+prefix.upper()+":")
        for code,(hi,lo),char in vals:
            padded=code.upper().ljust(5,"@")
            this.append('\tdb "'+padded+'", $'+format(hi,'02x')+
                        ', $'+format(lo,'02x')+' ; '+char)
        bytecount+=group_size
    this.append("POPS")
    records.extend(this)
    return "\n".join(index+[""]+records)+"\n",{
        "index_slots":len(KEYS),"index_bytes":len(KEYS)*4,
        "record_bytes":sum(len(v)*7 for v in groups.values())+7,
        "romx_record_chunks":chunk+1,
        "max_group_bytes":max((len(v)*7 for v in groups.values()),default=0),
    }

def run(args):
    glyphs=read_charmap(args.charmap)
    if args.dictionary:
        raw=args.dictionary.read_bytes()
        pinned=False
    else:
        with urllib.request.urlopen(UPSTREAM_URL,timeout=40) as req:raw=req.read()
        verify_source_bytes(raw)
        pinned=True
    groups,stats=make_buckets(raw.decode("utf-8-sig"),glyphs)
    asm,layout=generate_asm(groups)
    examples={
        "VND_is_好":any(code=="vnd" and ch=="好" for code,_,ch in groups.get("vd",[])),
        "AAA_is_晶":any(code=="aaa" and ch=="晶" for code,_,ch in groups.get("aa",[])),
        "AB_is_明":any(code=="ab" and ch=="明" for code,_,ch in groups.get("ab",[])),
        "A_has_日曰":set("日曰").issubset({ch for code,_,ch in groups.get("a",[]) if code=="a"}),
    }
    report={"implementation_status":"STAGED; NOT VERIFIED IN GAME",
            "upstream":UPSTREAM_URL,"upstream_commit":UPSTREAM_COMMIT,
            "upstream_git_blob_sha1":UPSTREAM_GIT_BLOB_SHA1 if pinned else None,
            "upstream_license":"MIT root table only","pinned":pinned,
            "font_charmap_glyphs":len(glyphs),"acceptance_examples":examples,
            **stats,**layout}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(asm,encoding="utf-8")
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.strict and (not pinned or not all(examples.values())):
        raise SystemExit("Full Cangjie data gate failed")
    print(json.dumps({k:report[k] for k in ("implementation_status",
        "usable_fullcode_glyph_pairs","distinct_full_codes",
        "max_records_per_prefix","romx_record_chunks")},ensure_ascii=False))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--charmap",type=Path,default=Path("pokecrystal_cn/constants/charmap_cn.asm"))
    p.add_argument("--dictionary",type=Path,default=None)
    p.add_argument("--output",type=Path,default=Path("generated/cangjie_v1_data.asm"))
    p.add_argument("--report",type=Path,default=Path("zh_tw_cangjie_v1_dictionary_report.json"))
    p.add_argument("--strict",action="store_true")
    run(p.parse_args())
