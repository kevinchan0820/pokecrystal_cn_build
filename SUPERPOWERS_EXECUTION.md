# Crystal 1.x — Superpowers execution discipline

This is a project-specific adoption of [obra/superpowers](https://github.com/obra/superpowers), **not a claim that the external Skill was installed in ChatGPT**.

## Binding rules for an executing agent

1. Before changing code, read `EXECUTION_STATE.md`, `TRUE_IME_ACCEPTANCE.md`, both `feature/zh-hant-tw-hk-1x` branch heads, the latest CI logs, and last actual PyBoy screenshot. **Never change 1.0.**
2. Follow Superpowers' `systematic-debugging`: reproduce → locate the exact source layer (workbook / ASM / title raster / toolbar PNG / glyph bitmap / emulator renderer) → identify root cause → fix the source. Don't assume OpenCC changes PNG files.
3. Follow `test-driven-development`: new regression test must fail on the original bug, then pass after the minimal repair. Record both expected and observed results in the execution ledger. For binary glyphs, check exact 2D pixel data and later the game screen.
4. Follow `verification-before-completion`: run the latest **uncancelled, exact-head** GitHub Action; read every test failure and compile status; inspect real PyBoy screenshots, not only text/RAM. **Never use an older green run as evidence for new edits**.
5. Check release acceptance **across every surface**:
   - `text.zh-TW.xlsx`: all actual imported game-display cells, terminology and official Pokémon naming
   - Displayed quoted ASM: all visible menus/dialogue; preserve intentional code words and original proper nouns
   - Rasterized Chinese: title art, 96×8 naming action strip, 120×8 naming mode strip, any newly discovered visible bitmap
   - DFS glyphs: Traditional Taiwan face used for both unique and shared Unicode characters (e.g. **好**), no original Simplified bitmaps
   - PyBoy: opening/title/menu, player naming, every existing mode and code entry, candidate choice, deletion, backspace, complete name and save/load, nickname entry/exit, screen wrapping/overlap
6. If one check fails, don't package or release a 1.x IPS as ready. Find first failure, fix, rerun. The public-facing result is **BLOCKED** until every criterion passes. Compile-only success is not release acceptance.
7. At any interruption, update `EXECUTION_STATE.md` with latest head SHA, CI run id and result, bug/reproduction, changed files, screenshots, failing tests, next specific action, and a list of unverified surfaces. Don't reset or duplicate the hourly scheduled task.
8. Preserve copyright/legal boundaries: source code and IPS only, no Nintendo ROM redistributions; verify external dictionary licences before importing full Quick/注音 data.

## Current priority

**Traditional Chinese UI parity first**: replace old Simplified naming bitmap `符号／删除` with Traditional `符號／刪除`, replace English `QUICK` with raster `速成`, verify actual screenshots and the Taiwan glyph of `好`, audit other user-provided Simplified screen text.

Then expand true Quick dictionary and real Zhuyin input with GBC controller tests. No static common-character picker may be advertised as a complete IME.

### Source skills

- https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md
