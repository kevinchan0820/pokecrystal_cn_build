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
            dialogue = wb.create_sheet("文7")
            dialogue["E2"] = "我要多一點零花錢。"
            wb.active["A1"] = "測試初訓家及記錄"
            workbook = base / "text.xlsx"
            wb.save(workbook)
            settings = base / "rules.json"
            settings.write_text(json.dumps({
                "locale": "zh-Hant-TW",
                "ui_rules": [{"id": "save", "path": "engine/menus/start_menu.asm",
                              "from": "記錄@", "to": "儲存@"}],
                "workbook_phrase_rules": [
                    {"id": "allowance", "scope": "dialogue",
                     "from": "零花錢", "to": "零用錢"}
                ],
                "review_flags": ["初訓家", "記錄"],
            }, ensure_ascii=False), encoding="utf-8")
            report = base / "result.json"
            first = apply(source, workbook, settings, report)
            text = menu.read_text(encoding="utf-8")
            self.assertIn('.SaveString: db_w "儲存@" ; "記錄@"', text)
            self.assertIn('.SaveDescription: db_w "請記錄日誌@"', text)
            self.assertEqual(first["applied_ui_rules"][0]["status"], "replaced")
            self.assertGreaterEqual(first["review_flags"]["初訓家"], 1)
            self.assertEqual(first["applied_dialogue_rules"][0]["count"], 1)
            modified = __import__("openpyxl").load_workbook(workbook, data_only=True)
            self.assertEqual(modified["文7"]["E2"].value, "我要多一點零用錢。")
            modified.close()
            second = apply(source, workbook, settings, report)
            self.assertEqual(second["applied_ui_rules"][0]["status"], "already-localized")


if __name__ == "__main__":
    unittest.main()
