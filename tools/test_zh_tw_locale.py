#!/usr/bin/env python3
"""Verify Taiwanese UI replacements don't rewrite other dialogue or comments."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook
from zh_tw_locale import apply


class LocaleRulesTest(unittest.TestCase):
    def test_ui_scoping_idempotence_and_report(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            source = base / "source"
            menu = source / "engine/menus/start_menu.asm"
            menu.parent.mkdir(parents=True)
            menu.write_text(
                '.SaveString: db_w "記錄@" ; "記錄@"\n'
                '.SaveDescription: db_w "請記錄日誌@"\n', encoding="utf-8")
            wb = Workbook()
            wb.active["A1"] = "測試初訓家及記錄"
            workbook = base / "text.xlsx"
            wb.save(workbook)
            settings = base / "rules.json"
            settings.write_text(json.dumps({
                "locale": "zh-Hant-TW",
                "ui_rules": [{"id": "save", "path": "engine/menus/start_menu.asm",
                              "from": "記錄@", "to": "儲存@"}],
                "review_flags": ["初訓家", "記錄"],
            }, ensure_ascii=False), encoding="utf-8")
            report = base / "result.json"
            first = apply(source, workbook, settings, report)
            text = menu.read_text(encoding="utf-8")
            self.assertIn('.SaveString: db_w "儲存@" ; "記錄@"', text)
            self.assertIn('.SaveDescription: db_w "請記錄日誌@"', text)
            self.assertEqual(first["applied_ui_rules"][0]["status"], "replaced")
            self.assertGreaterEqual(first["review_flags"]["初訓家"], 1)
            second = apply(source, workbook, settings, report)
            self.assertEqual(second["applied_ui_rules"][0]["status"], "already-localized")


if __name__ == "__main__":
    unittest.main()
