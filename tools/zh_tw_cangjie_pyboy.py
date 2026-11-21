#!/usr/bin/env python3
"""Real GBC controller test: full 1..5-root Cangjie, not Quick first/last.

Tests independent mode5, preserved 8x8 root grid, exact VND->好 /
AAA->晶, safe WRAM candidates, name bytes, correct @ terminator,
and mode 5 -> Pinyin restoration. Images are actual PyBoy frame captures.
"""
from __future__ import annotations
import argparse
from collections import deque
import io
import json
from pathlib import Path

from pyboy import PyBoy

from zh_tw_quick_pyboy import char_code


def test(rom:Path, source:Path, output:Path)->dict:
    output.mkdir(parents=True,exist_ok=True)
    sym=next((p for p in rom.parent.glob("*.sym")
              if "wNamingScreenLetterCase" in p.read_text(errors="ignore")),None)
    if sym is None:raise FileNotFoundError("ROM symbols .sym unavailable")
    gb=PyBoy(str(rom),symbols=str(sym),window="null",sound_emulated=False)
    gb.set_emulation_speed(0)
    labels=("wNamingScreenLetterCase","wIMEPinyin","wIMEMaxLine",
            "wIMEFullCandidateCount","wIMEFullCandidates","wIMEAddr",
            "wIMEBank","wNamingScreenCurNameLength","wPlayerName",
            "wNamingScreenCursorObjectPointer","wTilemap")
    syms={n:gb.symbol_lookup(n) for n in labels}
    entered=[]
    gb.hook_register(None,"NamingScreen",lambda a:a.append(True),entered)
    cases={}
    failures=[]
    def val(label,n=0):
        bank,addr=syms[label]
        return gb.memory[bank,addr+n]
    def button(name,delay=24):
        gb.button_press(name);gb.tick(3,render=True)
        gb.button_release(name);gb.tick(delay,render=True)
    def state():
        with io.BytesIO() as buffer:
            gb.save_state(buffer);return buffer.getvalue()
    def restore(snapshot):
        gb.load_state(io.BytesIO(snapshot));gb.tick(2,render=True)
    def xy():
        ptr=val("wNamingScreenCursorObjectPointer")|(
            val("wNamingScreenCursorObjectPointer",1)<<8)
        return gb.memory[0,ptr+0xC],gb.memory[0,ptr+0xD]
    def frame(name):
        f=output/("zh_tw_cangjie_"+name+".png")
        image=gb.screen.image.copy()
        image.save(f)
        image.resize((640,576),resample=0).save(
            output/("zh_tw_cangjie_"+name+"_4x.png"))
        return f.name
    def type_letter(base,code_byte,index,max_positions=120):
        queue=deque([(base,[])])
        visited=set()
        while queue and len(visited)<max_positions:
            snapshot,steps=queue.popleft()
            restore(snapshot)
            coord=xy()
            if coord in visited:continue
            visited.add(coord)
            if coord[1]<=1:
                button("a",12)
                if val("wIMEPinyin",index)==code_byte:
                    return steps,state()
            for direction in ("left","right","down","up"):
                restore(snapshot);button(direction,10)
                after=xy()
                if after[1]<=1 and after not in visited:
                    queue.append((state(),steps+[direction]))
        raise AssertionError("Can't enter full Cangjie root %02x index %d after %d positions"%
                             (code_byte,index,len(visited)))
    try:
        gb.tick(3600,render=True);button("start",180);button("a",220)
        for _ in range(110):
            button("a",90)
            if entered:break
        if not entered:raise AssertionError("Could not enter actual player naming screen")
        for _ in range(5):button("select",35)
        if val("wNamingScreenLetterCase")!=5:
            raise AssertionError("SELECT did not reach genuine Cangjie mode5")
        name=frame("five_root_mode")
        original=state()
        cases["independent_mode"]={"mode":5,"screen":name}
        root_atlas=(source/"gfx/naming_screen/cangjie_roots.1bpp").read_bytes()
        if len(root_atlas)!=26*8:
            raise AssertionError("26 root glyphs are not 8x8")
        # Each Cangjie code below requires more than one root, so it cannot
        # be implemented by the two-root Quick shortcut.
        for code,character in (("VND","好"),("AAA","晶"),("AB","明")):
            restore(original)
            routes=[]
            for i,ch in enumerate(code):
                path,now=type_letter(state(),0x80+ord(ch)-ord("A"),i)
                restore(now)
                routes.append(path)
            screenshot=frame("typed_"+code)
            if val("wIMEFullCandidateCount")<1 or val("wIMEMaxLine")!=1:
                raise AssertionError("%s missing real full-code Cangjie candidates"%code)
            if val("wIMEBank")!=0xff:
                raise AssertionError("%s must render from bounded WRAM scratch"%code)
            pointer=val("wIMEAddr")|(val("wIMEAddr",1)<<8)
            if pointer!=syms["wIMEFullCandidates"][1]:
                raise AssertionError("%s pointed outside Cangjie candidate buffer"%code)
            expected=char_code(source/"constants/charmap_cn.asm",character)
            count=val("wIMEFullCandidateCount")
            if not 1<=count<=7:
                raise AssertionError("%s candidate count out of range"%code)
            candidates=[[val("wIMEFullCandidates",2*j),
                         val("wIMEFullCandidates",2*j+1)] for j in range(count)]
            if expected not in candidates:
                raise AssertionError("%s does not include %s: %s"%(code,character,candidates))
            if [val("wIMEFullCandidates",count*2),
                val("wIMEFullCandidates",count*2+1)] != [0x50,0x50]:
                raise AssertionError("%s missing bounded double-@ terminator"%code)
            after_composition=state()
            # Controller moves to candidate area; for multiple glyphs
            # test all nearby 8px-key positions without assuming offsets.
            route_options=[
                ("down","down"),
                ("down","down","right","right"),
                ("down","down","right"),
                ("down","down","right","right","right"),
                ("down","down","left"),
                ("down","down","left","left"),
                ("down","down","right","right","right","right")]
            matched=False
            for route in route_options:
                restore(after_composition)
                for direction in route:button(direction,16)
                button("a",40)
                if val("wNamingScreenCurNameLength")==2 and (
                    [val("wPlayerName"),val("wPlayerName",1)]==expected):
                    if val("wPlayerName",2)!=0x50:
                        raise AssertionError("Name terminator overwritten after %s"%code)
                    frame("committed_"+code)
                    cases[code]={"code":code,"selected":character,
                                 "candidate_count":count,
                                 "expected_bytes":expected,
                                 "controller_routes":routes,
                                 "selection_route":route,
                                 "screenshot":screenshot,
                                 "name_terminator_safe":True}
                    matched=True;break
            if not matched:
                raise AssertionError("%s candidate %s exists but cannot select on GBC"%(code,character))
        restore(original)
        button("select",35)
        if val("wNamingScreenLetterCase")!=0:
            raise AssertionError("Cangjie mode does not wrap to Pinyin")
        cases["restore_original_pinyin"]={"passed":True,
                                          "screen":frame("pinyin_restored")}
    except Exception as exc:
        failures.append(type(exc).__name__+": "+str(exc))
    finally:
        gb.stop(save=False)
        result={"passed":not failures and len(cases)==5,
                "test":"real full Cangjie5 VND/AAA/AB code-to-candidate-to-player-name",
                "cases":cases,"failures":failures}
        (output/"zh_tw_cangjie_runtime_report.json").write_text(
            json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"passed":result["passed"],
                          "scenarios":list(cases),"failures":failures},ensure_ascii=False))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("rom",type=Path)
    p.add_argument("--source",type=Path,default=Path("pokecrystal_cn"))
    p.add_argument("--output",type=Path,default=Path("."))
    a=p.parse_args()
    if not test(a.rom,a.source,a.output)["passed"]:
        raise SystemExit(2)
