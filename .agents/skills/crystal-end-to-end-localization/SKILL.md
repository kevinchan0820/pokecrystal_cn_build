---
name: crystal-end-to-end-localization
description: "Use for Pokémon Crystal 1.x Taiwanese/Hong Kong Traditional Chinese source fixes, pixel-font issues, real input-method work and verified GBC delivery."
---

# Crystal end-to-end localization

Adapted from [obra/superpowers](https://github.com/obra/superpowers) practices; this repo skill does not imply installation into ChatGPT itself.

## Context preflight
1. Read `EXECUTION_STATE.md`, `TRUE_IME_ACCEPTANCE.md`, `SUPERPOWERS_EXECUTION.md`.
2. Read both exact 1.x branch heads; compare latest CI SHA with code SHA. Never modify or merge the 1.0 branch.
3. Extract latest PyBoy screenshots and full CI logs; prioritise the first confirmed failed acceptance criterion.

## Task loop (Superpowers-style)
- **SYSTEMATIC-DEBUGGING:** reproduce exact pixel/code/behavior failure; identify layer (workbook text, ASM, 12×12 DFS bin, PNG tile art, tilemap, runtime).
- **RED (TDD):** write source-specific assertion or real PyBoy button test; run on original and confirm failure.
- **GREEN:** minimally repair the source code or approved pixel art; run targeted check and observe success.
- **REFACTOR:** ensure no overlaps, ROM bank overflow, buffer or save regressions. Avoid broad automatic translation that breaks official names.
- **VERIFY-BEFORE-COMPLETION:** run fresh uncancelled exact-head CI and inspect actual PyBoy screenshots, not just RAM, logs or an artist concept.
- **LEDGER:** write verified SHA, CI URL, observed screenshots, failed/pass tests, blockers and exact next action to `EXECUTION_STATE.md`. Continue to next item without stopping for a status report.

## Mandatory localization surfaces
- `text.zh-TW.xlsx`: all imported workbook text cells.
- `*.asm`: game-visible strings, official Pokémon names, Taiwanese conventions, proper nouns and the planned HK vocabulary.
- Game title bitmap `gfx/title/logo.png`.
- Naming actions `gfx/naming_screen/selection_chinese.png`: **中文符號刪除完成**.
- Naming modes `gfx/naming_screen/mode_labels_zh_hant.png`: **拼音英文臺灣香港速成**.
- Bag pocket `gfx/pack/pack_menu.png` (read `gfx/pack/pack_menu.tilemap`): **精靈球**, never 精灵球.
- Unique/shared Unicode glyphs, especially `好`, should be Taiwan TTC #3 and confirmed using the actual compiled DFS bitmap.
- Additional raster text: inspect all source-referenced graphics (including `gfx/new_game/name_chinese.png`) and log unresolved evidence; no "all fixed" claim while unreviewed.
- Real PyBoy: TITLE, OPTIONS, MENU, naming all modes, Quick code/candidate/commit/backspace, nickname, SRAM reload, bag and text wrap. Test true 注音 separately: not implemented yet.

## Run gates
```bash
source .venv/bin/activate
bash tools/build_zh_tw.sh
python tools/zh_tw_smoke.py build/pokecrystal11.gbc --output .
python tools/zh_tw_quick_pyboy.py build/pokecrystal11.gbc --source pokecrystal_cn --output . --strict
python tools/zh_tw_quick_ui_qa.py build/pokecrystal11.gbc --source pokecrystal_cn --output .
```

The 1.x CI also runs naming regressions, Taiwan font pixel audits, and a patch round-trip check. Never release a copyrighted ROM; only the IPS and source where permitted. A passing set of targeted tests is not proof of a fully reviewed game.

## If CI fails
Do NOT stop at the first red CI. Fetch full job log and screenshot artifact, isolate the first failure, correct the cause, and repeat. If permissions/tools block writes, persist a blocker in the ledger. No fabricated PASS labels.
