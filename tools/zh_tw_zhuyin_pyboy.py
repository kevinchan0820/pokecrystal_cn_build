#!/usr/bin/env python3
"""REAL PyBoy Taiwan Zhuyin keys, tone marks, page switch and name commit.

Test controller input ㄚ→阿 and ㄇㄧㄥˊ→明, not Mandarin Pinyin.
Requires unchanged 26-key cell dimensions, two symbol pages, visible 12px
preedit, candidate selection, no $7f background corruption and name bytes.
"""
from __future__ import annotations
import argparse
import io
import json
from collections import deque
from pathlib import Path

from pyboy import PyBoy
from zh_tw_quick_pyboy import char_code
from zh_tw_zhuyin_full import SYMBOLS

def run(rom:Path,source:Path,output:Path):
    output.mkdir(parents=True,exist_ok=True)
    sym=next((p for p in rom.parent.glob("*.sym")
              if "wNamingScreenLetterCase" in p.read_text(errors="ignore")),None)
    if sym is None:raise FileNotFoundError("No built ROM symbol map")
    gb=PyBoy(str(rom),symbols=str(sym),window="null",sound_emulated=False)
    gb.set_emulation_speed(0)
    wanted=("wNamingScreenLetterCase","wIMEPinyin","wIMEMaxLine",
            "wIMEAddr","wIMEBank","wIMEFullCandidateCount",
            "wNamingScreenCurNameLength","wPlayerName",
            "wNamingScreenCursorObjectPointer","wTilemap")
    addr={n:gb.symbol_lookup(n) for n in wanted}
    entered=[]
    gb.hook_register(None,"NamingScreen",lambda a:a.append(True),entered)
    cases={}
    failures=[]
    def val(name,idx=0):
        bank,p=addr[name]
        return gb.memory[bank,p+idx]
    def key(name,delay=25):
        gb.button_press(name);gb.tick(3,render=True)
        gb.button_release(name);gb.tick(delay,render=True)
    def state():
        with io.BytesIO() as buf:
            gb.save_state(buf)
            return buf.getvalue()
    def restore(data):
        gb.load_state(io.BytesIO(data))
        gb.tick(2,render=True)
    def pos():
        p=val("wNamingScreenCursorObjectPointer")|(
            val("wNamingScreenCursorObjectPointer",1)<<8)
        return gb.memory[0,p+0xC],gb.memory[0,p+0xD]
    def snap(tag):
        png=output/("zh_tw_zhuyin_"+tag+".png")
        im=gb.screen.image.copy()
        im.save(png)
        im.resize((640,576),resample=0).save(
            output/("zh_tw_zhuyin_"+tag+"_4x.png"))
        return png.name
    def letter(base,sym,index):
        char_index=SYMBOLS.index(sym)
        page=char_index//26
        restore(base)
        if val("wIMEFullCandidateCount")!=page:
            key("start",30)
        if val("wIMEFullCandidateCount")!=page:
            raise AssertionError("START didn't change Zhuyin page for "+sym)
        begin=state()
        targets=deque([(begin,[])])
        visited=set()
        while targets and len(visited)<130:
            data,route=targets.popleft()
            restore(data)
            xy=pos()
            if xy in visited:continue
            visited.add(xy)
            if xy[1]<=1:
                key("a",12)
                if val("wIMEPinyin",index)==0x80+char_index:
                    return route,state()
            for direction in ("left","right","down","up"):
                restore(data)
                key(direction,12)
                nxt=pos()
                if nxt[1]<=1 and nxt not in visited:
                    targets.append((state(),route+[direction]))
        raise AssertionError("Zhuyin symbol not typeable with real controller: "+sym)
    try:
        gb.tick(3600,render=True);key("start",180);key("a",220)
        for _ in range(110):
            key("a",95)
            if entered:break
        if not entered:raise AssertionError("Could not reach actual naming scene")
        for _ in range(6):key("select",32)
        if val("wNamingScreenLetterCase")!=6:
            raise AssertionError("Real Zhuyin mode is not selectable via SELECT")
        cases["mode"]={"screen":snap("real_mode7_zhuyin"),"mode":6}
        # Pixel invariant: no blank tile $7f corruption from seventh
        # 3-tile mode label, original 8x8 key size preserved.
        empty=gb.screen.image.convert("RGB").crop((100,8,145,18))
        black=sum(sum(rgb)<420 for rgb in empty.getdata())
        if black>3:
            raise AssertionError("Zhuyin seventh title overwrote blank tile: "+str(black))
        initial=state()
        # Controller-driven visual regression: switching to the second
        # 26-key symbol page must actually redraw keys, and switching back
        # must restore the original pixels without stale tiles. A WRAM-only
        # page flag is insufficient evidence of a usable Zhuyin keyboard.
        page0_pixels=gb.screen.image.convert("RGB").crop((8,32,152,88)).tobytes()
        key("start",30)
        if val("wIMEFullCandidateCount")!=1:
            raise AssertionError("START did not enter second Zhuyin key page")
        page1_pixels=gb.screen.image.convert("RGB").crop((8,32,152,88)).tobytes()
        if page1_pixels==page0_pixels:
            raise AssertionError("Zhuyin page flag changed without redrawing key glyphs")
        page1_png=snap("second_symbol_page")
        key("start",30)
        if val("wIMEFullCandidateCount")!=0:
            raise AssertionError("START did not return to first Zhuyin key page")
        if gb.screen.image.convert("RGB").crop((8,32,152,88)).tobytes()!=page0_pixels:
            raise AssertionError("Zhuyin page toggle left stale keyboard pixels")
        cases["keyboard_page_pixels"]={"second_page_png":page1_png,
                                        "page0_restored":True}
        restore(initial)
        for spelling,expected in (("ㄚ","阿"),("ㄇㄧㄥˊ","明")):
            restore(initial)
            routes=[]
            for index,ch in enumerate(spelling):
                r,st=letter(state(),ch,index)
                restore(st)
                routes.append(r)
            if [val("wIMEPinyin",i) for i in range(len(spelling))]!=[
                    0x80+SYMBOLS.index(ch) for ch in spelling]:
                raise AssertionError("Zhuyin composition bytes wrong: "+spelling)
            if val("wIMEPinyin",len(spelling))!=0x50:
                raise AssertionError("Zhuyin composition overran @ terminator")
            if val("wIMEMaxLine")<=0 or val("wIMEMaxLine")>255:
                raise AssertionError("No phonetic+tone candidates for "+spelling)
            pointer=(val("wIMEBank"),val("wIMEAddr")|(val("wIMEAddr",1)<<8))
            if pointer[0]==0xff:
                raise AssertionError("Zhuyin must point at generated ROMX candidate list")
            page=val("wIMEFullCandidateCount")
            typed_screen=snap("typed_"+str(len(spelling))+"_symbols")
            if spelling=="ㄇㄧㄥˊ":
                if page!=1:raise AssertionError("Tone key didn't change phonetic page")
                cases["real_12px_tone_preview"]={"screen":typed_screen,"symbols":spelling}
            base=state()
            expected_bytes=char_code(source/"constants/charmap_cn.asm",expected)
            # A phonetic symbol may be on any of 41 key positions. The
            # selected key's X coordinate is NOT guaranteed to align with
            # the first candidate. Explore the actual GBC D-pad navigation
            # graph rather than assuming DOWN,DOWN always hits candidate0.
            # Never press A on keyboard rows: that would change the code.
            frontier=deque([(base,[])])
            visited=set()
            found=False
            while frontier and len(visited)<160:
                candidate_state,path=frontier.popleft()
                restore(candidate_state)
                xy=pos()
                if xy in visited:
                    continue
                visited.add(xy)
                if xy[1] in (2,3):
                    key("a",35)
                    if val("wNamingScreenCurNameLength")==2 and [
                            val("wPlayerName"),val("wPlayerName",1)]==expected_bytes:
                        if val("wPlayerName",2)!=0x50:
                            raise AssertionError("Zhuyin name terminator corrupted")
                        cases[spelling]={
                            "name":expected,"actual_code":spelling,
                            "bytes":expected_bytes,"input_routes":routes,
                            "selection_route":list(path),
                            "selected_png":snap("committed_"+str(len(spelling))),
                            "typed_png":typed_screen,
                        }
                        found=True
                        break
                for direction in ("left","right","down","up"):
                    restore(candidate_state)
                    key(direction,12)
                    nxt=pos()
                    if nxt[1]<=3 and nxt not in visited:
                        frontier.append((state(),path+[direction]))
            if not found:
                raise AssertionError(
                    "Zhuyin "+spelling+" code has candidates but cannot commit "+
                    expected+"; visited cursor positions="+str(sorted(visited)))
        restore(initial)
        key("select",35)
        if val("wNamingScreenLetterCase")!=0:
            raise AssertionError("Zhuyin mode does not return to Pinyin")
        cases["mode_exit"]={"pinyin_restored_png":snap("pinyin_restored")}
    except Exception as exc:
        failures.append(type(exc).__name__+": "+str(exc))
    finally:
        gb.stop(save=False)
        result={"passed":not failures and len(cases)==6,
                "cases":cases,"failures":failures,
                "test":"real Taiwan Zhuyin 41-symbol two-page keypress, tones, selection/name"}
        (output/"zh_tw_zhuyin_runtime_report.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"passed":result["passed"],"scenarios":list(cases),
                          "failures":failures},ensure_ascii=False))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("rom",type=Path)
    p.add_argument("--source",type=Path,default=Path("pokecrystal_cn"))
    p.add_argument("--output",type=Path,default=Path("."))
    a=p.parse_args()
    if not run(a.rom,a.source,a.output)["passed"]:
        raise SystemExit(2)
