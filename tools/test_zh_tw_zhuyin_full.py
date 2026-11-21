"""Tests for genuine Taiwan 注音 symbols + tones, no Pinyin shortcut."""
import unittest
from pathlib import Path
from zh_tw_zhuyin_full import SYMBOLS,CODE,collect,emit_asm,emit_symbol_map

class ZhuyinFullTests(unittest.TestCase):
    def test_41_symbols_and_two_page_codes(self):
        self.assertEqual(len(SYMBOLS),41)
        self.assertEqual(len(CODE),41)
        self.assertEqual(CODE["ㄇ"],0x82)
        self.assertEqual(CODE["ㄚ"],0x98)
        self.assertEqual(CODE["ˊ"],0xa5)
        self.assertEqual(CODE["˙"],0xa8)
    def test_reading_with_tone_is_not_pinyin(self):
        rows=("明 ㄇㄧㄥˊ ming2 -6 big5\n阿 ㄚ a - big5\n"
              "冥 ㄇㄧㄥˊ ming2 -6 big5\n明 ㄇㄧㄥˊ ming2 -6 big5\n"
              "明 ㄇㄧㄥˇ ming3 -6 big5\n简 ㄐㄧㄢˇ jian3 -6 utf8\n")
        chars=set("明阿冥简")
        d,report=collect(rows,chars,lambda c:"簡" if c=="简" else c)
        self.assertEqual(d["ㄇㄧㄥˊ"],["明","冥"])
        self.assertEqual(d["ㄚ"],["阿"])
        self.assertEqual(d["ㄇㄧㄥˇ"],["明"])
        self.assertNotIn("ㄐㄧㄢˇ",d)
        self.assertEqual(report["excluded_simplified"],1)
        asm,layout=emit_asm(d)
        self.assertIn("ZhuyinFirstIndex:",asm)
        self.assertEqual(layout["first_index_bytes"],164)
        self.assertEqual(asm.count("\tdbbw "),41)
        self.assertIn("ZhuyinRead_2_21_35_37",asm)
    def test_symbol_map_and_bank_sections(self):
        glyphs={ch:(2,i+1) for i,ch in enumerate(SYMBOLS)}
        text=emit_symbol_map(glyphs)
        self.assertEqual(text.count("\tdb $"),41)
        self.assertIn("ZhuyinSymbolCodes:",text)
        self.assertRaises(ValueError,emit_symbol_map,{})
    def test_no_false_pinyin_fallback(self):
        rows="明 ming2 ming2 - big5\n阿 ㄚ a - big5\n"
        out,_=collect(rows,set("明阿"),lambda ch:ch)
        self.assertNotIn("ming2",out)
        self.assertEqual(out["ㄚ"],["阿"])

    def test_tone_marks_cannot_begin_name_syllable(self):
        # Failing PyBoy red: #44888474953 accepted a lone ˊ.
        # A legitimate ㄇㄧㄥˊ must remain possible: only the initial
        # symbol is restricted to 37 Bopomofo letters, not four tones.
        src=(Path(__file__).resolve().parents[1]/
             "pokecrystal_cn/engine/dfs/zhuyin_lookup.asm").read_text(
                 encoding="utf-8")
        dispatch=src.split("ZhuyinLookup::",1)[1].split("ld c, a",1)[0]
        instructions=[line.strip() for line in dispatch.splitlines()
                      if line.strip() and not line.strip().startswith(";")]
        adjacent=list(zip(instructions,instructions[1:]))
        self.assertIn(('sub "A"','jp c, .no_result'),adjacent)
        self.assertIn(('cp 37','jp nc, .no_result'),adjacent)

if __name__=="__main__":
    unittest.main()
