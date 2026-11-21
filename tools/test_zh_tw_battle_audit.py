#!/usr/bin/env python3
"""Regression tests for official Taiwan Pokémon battle phrases."""
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook

from zh_tw_battle_audit import inspect, CANONICAL


class BattleWordingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "text.zh-TW.xlsx"
        self.book = Workbook()
        sheet = self.book.active
        sheet.title = "文3"
        for (_, position), text in CANONICAL.items():
            sheet[position] = text

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        self.book.save(self.path)

    def test_canonical_battle_messages_pass(self):
        self.save()
        result = inspect(self.path)
        self.assertTrue(result["verified"], result["errors"])
        self.assertEqual(len(result["canonical_battle_checks"]), 3)

    def test_reject_legacy_effectiveness_phrase(self):
        self.book["文3"]["E150"] = "效果拔群！"
        self.save()
        result = inspect(self.path)
        self.assertFalse(result["verified"])
        self.assertEqual(result["legacy_battle_phrases"][0]["term"], "效果拔群")

    def test_reject_changed_canonical_message(self):
        self.book["文3"]["E2837"] = "這非常有效！"
        self.save()
        result = inspect(self.path)
        self.assertFalse(result["verified"])
        self.assertTrue(any("E2837" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
