# Crystal 1.x — durable execution state

## Newest checkpoint — 2026-11-21, Traditional raster UI and pocket glyphs

**Product definition:** All user-visible text/glyphs must be Taiwanese/Hong Kong Traditional; actual GBC raster images are as important as Unicode text. Follow [SUPERPOWERS_EXECUTION.md](SUPERPOWERS_EXECUTION.md) and do not stop after a fix until red/green tests, ROM compile, real PyBoy visual review, and a persistent next-action report.

### Completed source changes, only on 1.x (not 1.0)
- `gfx/naming_screen/selection_chinese.png`: old Simplified `符号／删除` was a bitmap, not editable by OpenCC. Replaced 96×8 art with Taiwan-variant raster `中文符號刪除完成`; proved original 308 changed pixels vs approved TC, now 0 mismatch.
- `gfx/naming_screen/mode_labels_zh_hant.png`: 120×8 bitmap with five Traditional headers `拼音／英文／臺灣／香港／速成`; previous English QUICK was only a temporary fix for clipped Han text.
- `engine/menus/naming_screen.asm`: use 15 dedicated tiles at $6e..$7c for real Traditional headers, in a separate auto-placed ROMX section (`PUSHS/SECTION/POPS`). Original placement overflowed debug bank4 by two bytes; root cause fixed.
- `gfx/pack/pack_menu.png`: discovered with real `gfx/pack/pack_menu.tilemap` reconstruction that pocket title was Simplified `精灵球`. Changed the 12 unique atlas tiles for that title to Taiwan-variant `精靈球` using face3 at 16px. Original tilemap reconstructor reproduces failure, corrected image passes exactly.
- `tools/zh_tw_toolbar_bitmap_audit.py`: compares both naming bitmaps char-by-char against NotoSansCJK-Regular TTC Taiwan face #3.
- `tools/zh_tw_pack_pocket_qa.py`: reassembles the **actual** pack tilemap and rejects any non-approved `精靈球` glyph pixels.
- `tools/build_zh_tw.sh`: checks title logo, toolbar, mode labels, and pocket image before the costly ROM compilation.
- `tools/zh_tw_quick_ui_qa.py`: PyBoy test expects actual Traditional `速成` tile IDs (0x7a..7c), keeps code→candidate→name test `VD→好` and keyboard integrity.

### Last verified / latest activity
- **Previously verified exact-head run**: [#44867251486](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44867251486), **success** after fixing bank4 overflow, with real PyBoy showing the new Traditional toolbar, mode text and code `VD→好`.
- **LATEST VERIFIED exact-code CI**: [#44867512509](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44867512509), **success**, Source commit `a697ef71b379a9dfa6a186906d7c96c4e96b0bb3`, Build code commit `c29146fad887411474a618f5222ec349f7ea6a2b`. All strict PyBoy Quick/naming tests, image bitmap audits, 1.x ROM compile, IPS generation and checksums passed with no failed CI steps. Artifact `zh-hant-1x-twhk-input-prototype-and-reports` includes `zh_tw_pack_pocket_audit_report.json`, `zh_tw_toolbar_bitmap_audit_report.json`, `zh_tw_quick_ui_report.json`, plus real screenshots; all report `verified/passed: true`, empty errors. Verified source `精靈球` by tilemap reconstruction (not yet live bag screenshot).
- Prior complete text audit scanned 22,422 translated workbook strings, 4,130 displayed ASM strings across 2,471 ASM files; mechanical Simplified detection pass but `editorial_qa_complete: false`. Also 27 OpenCC non-idempotent proper terms requiring nuanced human linguistic review, not blind auto-conversion.

- **Font/coverage counts from #44867512509:** 6,819 required Han glyphs; 4,465 existing glyphs rerendered with Taiwan TTC face, 2,354 added glyph mappings, 0 missing. Complete text audit covered 22,422 workbook entries and 4,130 displayed ASM strings across 2,471 ASM files, `passes_mechanical_translation: true`, but `editorial_qa_complete: false`. OpenCC non-idempotence 27 is a *review list*, not automatic simplified proof; official names such as 尼多后 and 大岩蛇 should not be mass-changed. 
- **Real input proof:** PyBoy typed `VD` with controller and selected `好`; compiled name bytes [9, 13] match expected charmap, candidate/keyboard/header passes. The '好' Unicode itself is shared by simplified/traditional: Taiwan **shape** is verified via font bitmap, not by conversion alone. 

### What remains / next action (important)
1. On each future development commit, check the **new latest exact-head** CI run (not past success). If failed, read job logs and fix the cause. Today's raster fixes and #44867512509 CI are verified; do not misrepresent as whole-game completion.
2. Inspect latest **real PyBoy** screenshot for labels, name `好` and any clipping. Bag `精靈球` so far passes tilemap pixel reconstruction, but actual **in-game bag page** still needs PyBoy screenshot acceptance.
3. Review `gfx/new_game/name_chinese.png` and any other referenced text-bearing PNG, classify used vs unused. Do not claim all pictures are localized before this inspection and multi-scene gameplay QA.
4. Continue proper Quick vocabulary (not just five test codes), multiple candidates, paging, save/load, Pokémon nickname, and then genuine Taiwan Zhuyin. Release gate remains **BLOCKED** until full functional, visual and linguistic acceptance.
5. Keep existing hourly automation, do not create duplicates or merge to 1.0.

State: **IN PROGRESS (not a release)**

## Latest verified checkpoint — 2026-11-21, UI repaired but NOT release-ready

- **Latest verified source**: `kevinchan0820/pokecrystal_cn` `feature/zh-hant-tw-hk-1x`, source commit `693aaf0cb85701c9361b33e13acf8fc829d996e1`.
- **Latest successful CI build commit**: `0159fded425ef77d99d7dc33b8de771b47a78f34`, [GitHub Actions #44865660773](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44865660773), conclusion **success**.
- PyBoy strict regressions passed: `AA → 晶`, `AB → 明`, and real D-pad `VD → 好`; candidate picked and actual player name bytes `[9,13]` match `好` in compiled charmap. Actual status/keyboard tile integrity check passed; no overlap across keyboard rows, and after entering two valid codes the cursor auto-focuses first candidate. 1.x ROM and patch generated from that run, but **not a public release**.
- Real screenshots: CI artifact `zh_tw_quick_ui_quick_initial.png`, `zh_tw_quick_ui_typed_VD.png`, `zh_tw_quick_ui_name_HAO.png`; local user-facing real-screen comparison `Crystal_1x_Quick_Real_PyBoy_UI_Validated.png`. These are PyBoy-rendered game frames, not concept mockups. The user initially rejected previous UI due overlaps and garbled/simplified-looking text.
- Binary 12x12 Han bitmap QA uses **NotoSansCJK-Regular TTC Taiwan face #3**, including `好`; shared Unicode `好` alone cannot certify regional form. 1.x keeps a temporary single-row **English** mode header `QUICK` because 12px Chinese headers previously rendered clipped, not yet Taiwan/HK-quality native header text.
- **KNOWN RELEASE BLOCKERS** verified by visual screenshot: bottom action labels still show old Chinese-region raster `符号` / `删除` from `gfx/naming_screen/selection_chinese.png` (96×8 glyph strip), and mode header is English. Prototype layout is not the earlier illustrated tabbed mockup. Do NOT call localization or UX finished; do not reuse old promotional concept images as real screenshots. Must replace bottom labels with legible TC controls (`模式`, `刪除` etc) in a GBC-compatible pixel format and verify on real game frames. Avoid blindly squeezing complex Traditional glyphs into 8px: visual experiments showed unreadable characters.
- Quick dictionary remains tiny: `A` `AA` `AB` `AD` `VD` only; no full HK Quick, no TW Zhuyin, no full Cangjie/Jyutping, no trainers' in-game rename, no save/load test for finished names.
- **NEXT ACTION**: design and implement legible Traditional mode/action toolbar in the 160×144 GBC screen (not clipped 8px bitmap and not speculative tabs); compare actual screenshots; then scale Quick dictionary with rights review and add candidate paging/multiple matches/invalid code/reliable saving; then genuine Zhuyin code-to-character UI. Keep strict CI PyBoy tests (keyboard preserved, VD->好, mode wrap, name commit).
- Incident debug: [#44864411700](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44864411700) failed auto cursor landing on page arrow; [#44864938624](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44864938624) failed choosing glyph; fixed candidate cursor to VAR1=2 (full two-tile Chinese entry), row VAR2=2. [#44865381312](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44865381312) failed a **buggy QA comparison** that sampled Q/U from wrong keyboard tile coordinates; fixed assertion to use compiled ASCII charmap tile codes `[0x90,0x94,0x88,0x82,0x8A]`. Latest #44865660773 passed both real selection and visual tile integrity.
- **Don't create another hourly automation**: existing hourly task already resumes this branch. Every run inspect current GitHub state, code+test+persist exact failure and next action; never assume no visual defects merely because RAM/CI is green.

## Goal and release gate

Implement real Hong Kong **速成 / Quick** and Taiwan **注音 / Bopomofo** in the actual Game Boy Color naming interface, with controller key sequence → composition → candidate(s) → select → committed player/Pokémon name, all verified by real PyBoy + screenshot + SRAM save/load. Preserve 1.0 at branch `work/zh-hant-tw`.

## Last verified reality (do not exaggerate)

- Four earlier modes were: Mandarin Pinyin, English, Taiwan fixed-character grid, Hong Kong fixed-character grid. PyBoy grid-entry worked but is **not** a proper Quick or Zhuyin IME.
- True Quick **prototype code has now been written** in source repo `kevinchan0820/pokecrystal_cn`, branch `feature/zh-hant-tw-hk-1x`:
  - `engine/dfs/ime.asm`: mode 4 dispatch, two-code composer and Quick lookup.
  - Fixed include order: Quick key/index table must be compiled *before* the TW/HK common table's separate ROMX SECTION, so CPU lookup reads the correct bank.
  - `data/ime/ime_quick_twhk.asm`: initial test code table: A→日, AA→晶, AB→明, AD→杲. **Only four codes, not a complete dictionary.**
  - `engine/menus/naming_screen.asm`: fifth SELECT mode `速成(兩碼)`.
- Build repo `kevinchan0820/pokecrystal_cn_build` on same branch:
  - `tools/zh_tw_naming_qa.py`: five-mode SELECT wrap regression.
  - `tools/zh_tw_quick_pyboy.py`: real controller tests AA→晶 and AB→明; verifies ROM Quick code candidate symbol pointer, actual charmap bytes, candidate selection and screenshots. Tests must exit nonzero on failure.
  - `.github/workflows/zh-hant-ci.yml`: mandatory strict Quick PyBoy test **before** generating IPS.
- **VERIFIED 2026-11-21:** GitHub Actions https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44863353708 completed **success**. Both REAL PyBoy controller scenarios passed:
  - `A`, `A` → lookup QuickCandidatesAA → candidate `晶` → select with D-pad/A → player name bytes `[10, 161]`.
  - `A`, RIGHT, `A` → lookup QuickCandidatesAB → candidate `明` → select with D-pad/A → player name bytes `[13, 7]`.
  - Report `zh_tw_quick_pyboy_report.json` recorded `passed: true`, `failures: []`; screenshots in CI artifact `zh-hant-1x-twhk-input-prototype-and-reports`. All earlier naming, ROM compile, patch, and smoke steps also passed.
  - **SCOPE:** This is a four-code real Quick *proof of concept*, **NOT** a real-world complete Quick dictionary. No saved-game reloading or ambiguity/page navigation for Quick specifically tested yet. Zhuyin/Cangjie remain unimplemented.

## Next actions (in order, autonomous)

1. Read **latest** source/build branch SHA and latest GitHub Actions run, avoid relying on the SHA documented here if branch advanced. The current micro-dictionary code-to-character PyBoy test is green; do not regress it.
2. If build fails: fetch GitHub Actions job logs, locate first error, fix root cause on 1.x branch and rerun, repeat. Do not change 1.0.
3. If PyBoy Quick fails: use screenshot JSON, actual RAM / symbol and button traces, fix real controller flow for A→A/AB. Keep exact expected character bytes `晶`, `明`.
4. **NEXT PRIORITY NOW:** expand Quick micro-dictionary to a genuinely useful dictionary with proper license/attribution review and ROM-bank budget; test ambiguity, candidate paging, invalid codes, backspace, multi-character full-name commit and save/reload before saying Quick is finished.
5. Then implement true Zhuyin using parallel framework and formal test ㄇㄧㄥˊ→明 / ㄚ→阿. Again do not label static char picker as phonetic input.
6. Persist results here and in CI artifacts; ship 1.x release only when `TRUE_IME_ACCEPTANCE.md` gates are satisfied.

## Execution discipline

- Each iteration **inspect → code → build → real PyBoy action → review screenshot/data → fix or record blocker → update next action**.
- At interruption commit the latest reproducible checkpoint and explicit unresolved root cause.
- Never say "still working in the background" unless an actual scheduled automation is active. A scheduled task runs at intervals, not continuously.
- User has enabled a recurring **hourly** ChatGPT automation on 2026-11-21 to continue this branch; do not create duplicate automations.
- Prohibited without user confirmation: merging to 1.0, redistribution of copyrighted ROM, deleting data, overwriting saves, publishing unverified release.
