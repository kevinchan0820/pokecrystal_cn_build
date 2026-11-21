"""Cangjie5 five-root dictionary generator and ROM-bank regression tests."""
import unittest
from zh_tw_cangjie_full import make_buckets,generate_asm
from zh_tw_quick_dictionary_v2 import KEYS

class CangjieV1Tests(unittest.TestCase):
    def setUp(self):
        self.glyphs={ch:(4,i+9) for i,ch in enumerate("日曰晶明好簡昌")}
        self.rows="a\t日\na\t曰\naaa\t晶\nab\t明\nvnd\t好\naa\t昌\nax\t简\n"

    def test_exact_five_code_not_just_quick_first_last(self):
        groups,stats=make_buckets(self.rows,self.glyphs,
                                  convert=lambda ch:"簡" if ch=="简" else ch)
        self.assertEqual([entry[0] for entry in groups["a"]],["a","a"])
        self.assertEqual([entry[0] for entry in groups["aa"]],["aa","aaa"])
        self.assertEqual([entry[0] for entry in groups["ab"]],["ab"])
        self.assertEqual([entry[0] for entry in groups["vd"]],["vnd"])
        self.assertEqual(stats["usable_fullcode_glyph_pairs"],6)
        self.assertEqual(stats["distinct_full_codes"],5)

    def test_fixed_703_prefixes_and_exact_7_byte_record(self):
        groups,_=make_buckets(self.rows,self.glyphs,lambda ch:ch)
        asm,info=generate_asm(groups)
        self.assertEqual(len(KEYS),703)
        self.assertEqual(info["index_bytes"],2812)
        self.assertEqual(asm.count("\tdbbw "),703)
        self.assertIn('SECTION "Cangjie v1 Prefix Index", ROMX',asm)
        self.assertIn('db "VND@@", $04, $0d ; 好',asm)
        self.assertEqual(asm.count("PUSHS"),asm.count("POPS"))

    def test_duplicate_code_candidates_remain_distinct(self):
        groups,info=make_buckets(self.rows,self.glyphs,lambda ch:ch)
        self.assertEqual(info["max_same_full_code_candidates"],2)
        asm,_=generate_asm(groups)
        self.assertIn('db "A@@@@", $04, $09 ; 日',asm)
        self.assertIn('db "A@@@@", $04, $0a ; 曰',asm)

    def test_group_entry_count_limited_to_one_byte(self):
        pairs=[(str(i), (1,1), str(i)) for i in range(256)]
        self.assertRaises(ValueError,generate_asm,{"aa":pairs*20})

if __name__=="__main__":
    unittest.main()
