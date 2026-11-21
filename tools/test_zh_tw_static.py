#!/usr/bin/env python3
"""Regression tests for inline-label Chinese menu translation."""
import tempfile
import unittest
from pathlib import Path

from zh_tw_static import rewrite, separate_comment, DISPLAY_LINE


class StaticMenuTests(unittest.TestCase):
    def test_recognizes_labelled_and_unlabelled_display_strings(self):
        self.assertIsNotNone(DISPLAY_LINE.match('.PokedexString: db_w "图鉴@"'))
        self.assertIsNotNone(DISPLAY_LINE.match('MainMenu:: text "宝可梦"'))
        self.assertIsNotNone(DISPLAY_LINE.match('\tli "旧道具"'))
        self.assertIsNotNone(DISPLAY_LINE.match('.health  db_w "体力@"'))
        self.assertIsNotNone(DISPLAY_LINE.match('npctrade A, B, "直树@@@@", 12'))
        self.assertIsNotNone(DISPLAY_LINE.match('getchar_w "宝"'))
        self.assertIsNone(DISPLAY_LINE.match('; .PokedexString: db_w "图鉴@"'))
        self.assertIsNone(DISPLAY_LINE.match('\tld a, "图"'))

    def test_quoted_semicolon_is_not_a_comment(self):
        body, comment = separate_comment('db_w "项;目@" ; "不应改变"')
        self.assertEqual(body, 'db_w "项;目@" ')
        self.assertEqual(comment, '; "不应改变"')

    def test_convert_inline_labels_and_preserve_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "engine/menus/start_menu.asm"
            target.parent.mkdir(parents=True)
            target.write_text(
                '.PokedexString: db_w "图鉴@" ; "这是注释"\n'
                '.PartyString: db_w "宝可梦@"\n'
                '\ttext "<PLAYER>的电脑"\n'
                '\t; db_w "简体"\n'
                '\tld a, "简"\n', encoding="utf-8")
            summary = rewrite(root, "s2twp")
            self.assertEqual(summary, {"engine/menus/start_menu.asm": 3})
            result = target.read_text(encoding="utf-8")
            self.assertIn('.PokedexString: db_w "圖鑑@" ; "这是注释"', result)
            self.assertIn('.PartyString: db_w "寶可夢@"', result)
            self.assertIn('<PLAYER>的電腦', result)
            self.assertIn('; db_w "简体"', result)
            self.assertIn('\tld a, "简"', result)


    def test_trade_stat_and_radio_macro_text_get_localized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {
                "data/events/npc_trades.asm": 'npctrade A, B, "直树@@@@", 12\n',
                "engine/items/item_effects.asm": '.health  db_w "体力@"\n',
                "engine/pokegear/radio.asm": '\tgetchar_w "宝"\n',
            }
            for path, text in files.items():
                file = root / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(text, encoding="utf-8")
            changed = rewrite(root, "s2twp")
            self.assertEqual(sum(changed.values()), 3)
            self.assertIn('"直樹@@@@",', (root / "data/events/npc_trades.asm").read_text())
            self.assertIn('"體力@"', (root / "engine/items/item_effects.asm").read_text())
            self.assertIn('"寶"', (root / "engine/pokegear/radio.asm").read_text())


if __name__ == "__main__":
    unittest.main()
