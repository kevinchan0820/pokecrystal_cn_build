#!/usr/bin/env python3
"""Protect the naming-screen controller dispatch from RGBDS JR range overflow.

A real CI link failed at naming_screen.asm lines 595, 601, 607, 611 after
mode 6 / Taiwan Zhuyin grew the dispatch's branches past +/-127 bytes.
This regression guards source intent; the ROM linker remains authoritative.
"""
import re
import unittest
from pathlib import Path


class NamingJoypadDispatchTest(unittest.TestCase):
    def test_dispatch_uses_absolute_conditional_jumps(self):
        source = (Path(__file__).resolve().parents[1]
                  / "pokecrystal_cn/engine/menus/naming_screen.asm").read_text(
                      encoding="utf-8")
        self.assertIn(".ReadButtons:", source)
        dispatch = source.split(".ReadButtons:", 1)[1].split("\n.a\n", 1)[0]
        for button, target in (("A_BUTTON", ".a"), ("B_BUTTON", ".b"),
                               ("START", ".start"), ("SELECT", ".select")):
            with self.subTest(button=button):
                expr = (r"and\s+" + button + r"\s*\n\s*jp\s+nz,\s*"
                        + re.escape(target) + r"\b")
                self.assertRegex(dispatch, expr)
        self.assertNotRegex(dispatch, r"(?m)^\s*jr\s+nz,\s*\.(?:a|b|start|select)\b")
        # A-button destinations now span more than +/-127 bytes too.
        a_handler = source.split("\n.a\n", 1)[1].split("\n.start\n", 1)[0]
        for condition, target in (("z", ".select"), ("z", ".b"),
                                  ("z", ".end"), ("c", ".start_normal")):
            with self.subTest(a_target=target):
                self.assertRegex(a_handler,
                    r"(?m)^\s*jp\s+" + condition + r",\s*" +
                    re.escape(target) + r"\b")
        self.assertNotRegex(a_handler, r"(?m)^\s*jr\s+[cz],\s*\.(?:select|b|end|start_normal)\b")


if __name__ == "__main__":
    unittest.main()
