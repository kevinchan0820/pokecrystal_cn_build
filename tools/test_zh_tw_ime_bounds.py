"""Unit tests for safe ROM dictionary bounds and table/key alignment."""
import tempfile
import unittest
from pathlib import Path
from zh_tw_ime_bounds_audit import audit

QUICK = """QuickTB:
    db_w "@@@@@@@"
    db_w "A@@@@@@"
    db_w "AA@@@@@"
    db_w "VD@@@@@"
QuickTBEnd:
QuickTBEntry:
    dbbw 0, BANK(Empty), Empty
    dbbw 1, BANK(A), A
    dbbw 1, BANK(AA), AA
    dbbw 1, BANK(VD), VD
"""
PINYIN = """PinyinTB:
    db_w "@@@@@@@"
    db_w "A@@@@@@"
    db_w "ZI@@@@@"
PinyinTBEnd:
    db_w "111111@"
"""
ENGINE = """.miss
    pop hl
    ld de, $0007
    add hl, de
    inc bc
    cp HIGH(PinyinTBEnd)
    jr z, .exhausted
    cp HIGH(QuickTBEnd)
    jr z, .exhausted
.exhausted
    ld bc, $0000
    ret
.start
    push hl
"""

class RomDictionaryBoundsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for directory in ("engine/dfs", "data/ime"):
            (self.root/directory).mkdir(parents=True,exist_ok=True)
    def tearDown(self):
        self.tmp.cleanup()
    def write(self, engine=ENGINE, quick=QUICK, pinyin=PINYIN):
        (self.root/"engine/dfs/ime.asm").write_text(engine,encoding="utf-8")
        (self.root/"data/ime/ime_quick_twhk.asm").write_text(quick,encoding="utf-8")
        (self.root/"data/ime/ime_entry.asm").write_text(pinyin,encoding="utf-8")
        return audit(self.root)
    def test_bounded_sorted_lookup_and_aligned_pointer_count(self):
        self.assertTrue(self.write()["verified"])
    def test_prevent_runaway_quick_scan(self):
        result=self.write(engine=ENGINE.replace("QuickTBEnd","WrongLabel"))
        self.assertFalse(result["verified"])
        self.assertTrue(any("QuickTBEnd" in e for e in result["errors"]))
    def test_prevent_runaway_pinyin_scan(self):
        result=self.write(pinyin=PINYIN.replace("PinyinTBEnd:",""))
        self.assertFalse(result["verified"])
        self.assertTrue(any("PinyinTBEnd" in e for e in result["errors"]))
    def test_reject_candidate_index_alignment_errors(self):
        result=self.write(quick=QUICK.replace("    dbbw 1, BANK(VD), VD\n",""))
        self.assertFalse(result["verified"])
        self.assertTrue(any("pointer count" in e for e in result["errors"]))
    def test_reject_duplicate_or_unsorted_keys(self):
        result=self.write(quick=QUICK.replace('    db_w "VD@@@@@"','    db_w "AA@@@@@"'))
        self.assertFalse(result["verified"])
        self.assertTrue(any("sorted" in e for e in result["errors"]))

if __name__ == "__main__":
    unittest.main()
