"""Budget, input-data, and license-pin regression tests for future full Quick IME."""
import unittest
from zh_tw_quick_dictionary_v2 import (
    build_buckets,emit_asm,verify_source_bytes,KEYS,MAX_QUICK_CANDIDATES,
)

class QuickV2DictionaryTests(unittest.TestCase):
    def test_same_code_ambiguity_and_full_cangjie_to_quick(self):
        rows=("a\t日\na\t曰\na\t曰\naa\t昌\naaa\t晶\n"
              "ab\t明\nvnd\t好\naaa\t鹂\n")
        supported=set("日曰昌晶明好鹂")
        groups,stats=build_buckets(rows,supported,lambda ch:"鸝" if ch=="鹂" else ch)
        self.assertEqual(groups["a"], ["日","曰"])
        self.assertEqual(groups["aa"], ["昌","晶"])
        self.assertEqual(groups["ab"], ["明"])
        self.assertEqual(groups["vd"], ["好"])
        self.assertNotIn("鹂",groups["aa"])
        self.assertEqual(stats["excluded_nontraditional"],1)
        self.assertEqual(stats["unique_candidates"],6)

    def test_generated_index_has_stable_703_slots_and_banked_chunks(self):
        asm,report=emit_asm({"a":["日","曰"],"aa":["昌","晶"],"vd":["好"]})
        self.assertEqual(len(KEYS),703)
        self.assertEqual(report["entry_slots"],703)
        self.assertEqual(report["index_bytes"],2812)
        self.assertIn('SECTION "Quick v2 Index", ROMX',asm)
        self.assertIn('QuickV2Entry:',asm)
        self.assertIn('QuickV2_VD:',asm)
        self.assertIn('db_w "好"',asm)
        self.assertEqual(asm.count("PUSHS"),asm.count("POPS"))
        self.assertEqual(asm.count("\tdbbw "),703)

    def test_rows_pages_and_hard_bank_boundaries(self):
        chars=[chr(0x4E00+i) for i in range(17)]
        _,report=emit_asm({"aa":chars})
        self.assertEqual(report["max_candidate_rows"],3)
        self.assertRaises(ValueError,emit_asm,{"aa":chars*100})

    def test_reject_unpinned_upstream_data(self):
        with self.assertRaises(ValueError):
            verify_source_bytes(b"malicious unpinned dictionary")

if __name__=="__main__":
    unittest.main()
