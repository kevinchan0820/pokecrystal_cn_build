"""Regression tests for conservative Chinese artwork reference tracing."""
import tempfile
import unittest
from pathlib import Path

from zh_tw_asset_reference_audit import scan

class AssetReferenceAuditTests(unittest.TestCase):
    def test_direct_asm_and_make_references_are_found(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            png = root / "gfx/new_game/name_chinese.png"
            png.parent.mkdir(parents=True)
            png.write_bytes(b"PNG placeholder, only existence tested")
            (root / "gfx.asm").write_text(
                '; INCBIN "gfx/new_game/name_chinese.2bpp"\n'
                'INCBIN "gfx/trainer_card/card_status.2bpp"\n',
                encoding="utf-8")
            (root / "Makefile").write_text(
                'assets: gfx/new_game/name_chinese.png\n', encoding="utf-8"
            )
            res = scan(root)
            items = res["assets"]
            self.assertEqual(
                [x["file"] for x in items["gfx/new_game/name_chinese.png"]["direct_source_references"]],
                ["Makefile"])
            self.assertTrue(items["gfx/new_game/name_chinese.png"]["source_file_exists"])
            self.assertEqual(len(items["gfx/trainer_card/card_status.png"]["direct_source_references"]), 1)

    def test_unreferenced_does_not_mean_unused(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "symbols.asm").write_text("SECTION \"Main\", ROM0\n", encoding="utf-8")
            res = scan(root)
            item = res["assets"]["gfx/new_game/name_chinese.png"]
            self.assertEqual(item["direct_source_references"], [])
            self.assertFalse(item["runtime_rendering_verified"])
            self.assertIn("NOT PROVEN", item["classification"])

if __name__ == "__main__":
    unittest.main()
