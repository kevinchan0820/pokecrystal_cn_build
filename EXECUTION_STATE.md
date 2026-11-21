# Crystal 1.x — durable execution state

## Verified checkpoint — 2026-11-21: ALL 26 Cangjie root keys now visible in actual PyBoy

- **Latest exact-head success:** [GitHub Actions #44873879766](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44873879766) **SUCCESS**, source `525f6728ec3d04ede5517fe079a462db72670aab`, build code `8ef9e14b5f88640d83e26ce6d1bb8d4d56d12d4f`. Passed full ROM/IPS creation, boot, options, five naming modes, Quick AA→晶 / AB→明 / VD→好, Trainer Card approved 目前狀態 bitmap, five canonical battle strings.
- **Critical false-green corrected:** earlier `zh_tw_quick_ui_quick_radical_keyboard.png` showed first row A-P as Han roots but Q-Z still Latin even though VRAM probes passed. Red screenshot test compared **actual 8x8 screen pixels** to atlas entries for keys Q-Z: all ten FAILED (19–33 differing pixels each). Do not trust VRAM-only glyph checks for UI.
- **Actual root cause:** naming keyboard's second row is **screen tile row 10**, not row 9 (blank spacer). Previous test read row 9 and assumed Q-Z used bank0. The runtime uploaded only first **16** A-P Han glyphs to VRAM bank1. Fix in `engine/menus/naming_screen.asm`: upload **all 26** Cangjie glyphs to both bank0 and bank1 at original A-Z tile codes and 8x8 positions. New CI checks actual screenshot Q-Z pixels, and `zh_tw_quick_ui_report.json` states `passed:true`, `second_row_screen_pixel_audit:[]`. Success also preserved Latin Pinyin mode and real Quick entry.
- **Superseded failed attempts:** [#44873264198](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44873264198) and [#44873583610](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44873583610) confirmed the failure. Simply forcing VBK=0 was insufficient; fix required full 26-tile bank1 copy, plus correcting the test's on-screen tile-row mapping.
- **Source screenshot evidence:** CI artifact `zh_tw_quick_ui_quick_radical_keyboard.png`; same run has `zh_tw_quick_ui_name_HAO.png`. The image is a real 160×144 PyBoy frame, not a mockup.
- **Current blockers unchanged:** legibility of complex 8x8 roots needs human UX review; Quick only tiny test dictionary and full Cangjie/注音 not implemented; actual battle status and Trainer Card page screenshots, save/load, `gfx/new_game/name_chinese.png` and full-game visual sweep not completed. **1.x not ready for release**. 1.0 untouched.
- **Next action:** use PyBoy to reach Trainer Card, Bag and burned battle and inspect visible Taiwan glyphs. Keep strict Q-Z pixel test permanently, improve 8px root readability without changing key dimensions, then implement practical Quick dictionary with paging and real Zhuyin.

## Checkpoint — 2026-11-21 13:55+08:00 — real PyBoy screenshot zoom evidence

- Read current EXECUTION_STATE, SUPERPOWERS_EXECUTION, TRUE_IME_ACCEPTANCE, and .agents/skills/crystal-end-to-end-localization/SKILL.md. Reviewed actual naming PyBoy QA implementation and prior CI artifact #44872657612. The previously green run predates this commit and MUST NOT be counted as exact-head validation.
- Build branch commit `da6fef7d8cd2c66e13436e91b8afbb2575e77c30`: `tools/zh_tw_quick_ui_qa.py` now emits unmodified 160x144 screenshots plus 640x576 nearest-neighbor inspection copies for every snapshot. This is a test-evidence improvement, NOT a root-font fix. It preserves real emulator pixels and permits human review of 日月金木水 and complex roots.
- Observed blocker: 8x8 root tiles (especially complex 難/符) are not yet certified legible. Existing test only verifies byte equality and VRAM bank mapping, which does not prove human readability. A visual acceptance check and approved pixel redesign are required; do not replace keycodes or claim an 8x8 glyph is readable merely because bytes match.
- Environment blocker: local `git ls-remote` cannot resolve github.com. No local ROM compile, PyBoy execution, RED/GREEN raster fix, or new exact-head CI result was obtained in this checkpoint. Existing #44872657612 screenshots are older evidence only.
- Next: inspect new exact-head CI for `da6fef7` (and its source SHA), retrieve generated 4x screenshots, compare every 26 root glyph at native and zoom scales; create failing per-glyph visual/raster acceptance assertions, patch source `gfx/naming_screen/cangjie_roots.png` and .1bpp, rerun ROM+PyBoy; then handle name_chinese.png, bag live screen, full Quick candidate paging, SRAM, nickname, Zhuyin/Cangjie. No ROM redistribution or 1.0 merge.
- Release gate: BLOCKED. Unverified: human legibility of all 26 radicals, live bag and name_chinese raster, candidate paging, full dictionary, save/load, nickname, Zhuyin, Cangjie, all-scene Traditional audit.


## Verified checkpoint — 2026-11-21: Trainer Card raster Traditional, exact CI green

- **Source commit:** `kevinchan0820/pokecrystal_cn@bb2087cfeb9082d0a3e0f1ad887fde9b538112b9` (only `feature/zh-hant-tw-hk-1x`). **Build code commit:** `kevinchan0820/pokecrystal_cn_build@09523558c973dca7dd0eba000d24420e3acd4421`; later docs-only audit `f4c4947524e96f9e0c34ccd746074fefe151cb8c`.
- **Latest verified CI:** [#44872657612](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44872657612) **success** — title/toolbar/pack/trainer-card raster audits, battle-text 5 canonical lines, ROM compile, boot, Options and frame screens, PyBoy naming, real root-key Quick `AA→晶 / AB→明 / VD→好`, new IPS + checksum roundtrip. The GitHub artifact includes `zh_tw_trainer_card_raster_report.json`: `verified=true`, `errors=[]`.
- **New root cause:** User screenshots' battle status text may come from an outdated ROM, but current translation source already contains `敵人的【0】` and `受到了灼傷的傷害！`; do not infer old screenshot's ROM build SHA. Current `zh_tw_battle_audit_report.json` checked **20,735** dialogue cells and 5 canonical entries; still need a real burned-status PyBoy battle screenshot to close visual acceptance.
- **New PNG defect:** `gfx/trainer_card/card_status.png` is a real loaded 48x8 raster via `engine/menus/trainer_card.asm` (`CardStatusGFX`); previous source used simplified `当前状态`. Now contains approved Taiwan 8px `目前狀態` at unchanged dimensions. Initial red test failed all four glyphs; local green test passed all.
- **Testing failure and repair:** [#44872489401](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44872489401) failed 3 of 4 glyph comparisons because CI's installed TTC/Pillow rasterizer differs from the asset-authoring runtime, not because the uploaded image changed. Replaced host-dependent re-rasterization with **per-glyph hashes of approved decoded 12x8 pixels**. Rerun exact-head [#44872657612](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44872657612) green.
- **Inventory**: see [RUNTIME_TRADITIONAL_IMAGE_AUDIT.md](RUNTIME_TRADITIONAL_IMAGE_AUDIT.md), including unverified `gfx/new_game/name_chinese.png`, Trainer Card live screenshot, actual bag page and burned battle.
- **NEXT ACTION, no prompting required:** drive PyBoy into actual Trainer Card, Bag, and battle, capture screenshot and compare on-screen pixel/text against Traditional; if mismatch, add RED test, patch and rerun. Audit 40x8 `gfx/new_game/name_chinese.png` against its real assembly reference. Expand genuine Quick code coverage, full Cangjie and Taiwanese 注音 later; existing 26 root keyboard is already functioning. **Do not mark 1.x release ready** until all UI and gameplay scenarios accepted. Keep 1.0 unchanged.

## Verified checkpoint — 2026-11-21: Rime keyboard RED→GREEN and battle glyphs

- **Exact source head:** `kevinchan0820/pokecrystal_cn@323e789640d5cd1b0f0bcba80162e6ec83d92c0f`. **Exact latest verified build HEAD:** `kevinchan0820/pokecrystal_cn_build@6e128cb20d103ffe42e52502d0bf87900b57a15a`.
- **Green full CI:** [#44870886829](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44870886829) conclusion **success**, 0 failing steps, ROM compiled, boot/menu/naming PyBoy, Quick `AA→晶`, `AB→明`, `VD→好`, visual root keyboard and English alphabet restoration, IPS round-trip all pass.
- **Reference not invented:** [Rime Cangjie5 Express](https://github.com/rime/rime-cangjie/blob/master/cangjie5_express.schema.yaml) and [Rime Quick5](https://github.com/rime/rime-quick/blob/master/quick5.schema.yaml). Canonical 26 letter-to-root mapping: `日月金木水火土竹戈十大中一弓人心手口尸廿山女田難卜符`. `gfx/naming_screen/cangjie_roots.png` / `.1bpp` are 26 source 8×8 root glyph tiles; `engine/menus/naming_screen.asm` shows them in unchanged A–Z key positions in Quick mode and restores Latin on leaving.
- **Superpowers red-green evidence:** Initial test [#44869386179](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44869386179) failed (missing code). After source update, [#44869476820](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44869476820) failed real screenshot: first row still Latin despite root bytes in VRAM bank0. [#44869791899](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44869791899) captured `wAttrmap` first row bank1 and bank0 second row; [#44870098794](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44870098794) showed resetting attributes broke AA/AB input. Final source uploads 8×8 glyphs into **both** VRAM banks, preserves attr/code mapping; [#44870434977](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44870434977) green. This is root-cause, not symptom-level UI substitution.
- **Actual PyBoy screenshots** from #44870434977: `zh_tw_quick_ui_quick_radical_keyboard.png`, `zh_tw_quick_ui_pinyin_latin_restored.png`, `zh_tw_quick_ui_name_HAO.png`. 26 radicals now visible with exact 8×8 key cell sizing. **Human legibility unresolved** for complex radicals like `難／符`: the 8×8 raster is tiny; don't call final UX polished.
- **User-reported battle residual Simplified-looking glyphs**: latest generated `text.zh-TW.xlsx` E cells verified `文3!E2337=受到了灼傷的傷害！`, `文3!E2429=敵人的【0】`, `E2829=擊中了要害！`, `E2837=效果絕佳！`. `tools/zh_tw_battle_audit.py` now checks 5 canonical messages; `tools/zh_tw_glyph_qa.py` now checks additional Taiwanese font glyphs `敵人灼傷害火岩鼠`. [#44870774429](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44870774429) failed because `test_zh_tw_battle_audit.py` had hardcoded 3 checks; changed to `len(CANONICAL)`, now #44870886829 green. **Old Delta screenshot ROM/version unverified; all in-game battle overlays not yet visually accepted**.
- **Not completed / do not claim released:** full Quick dictionary and same-code candidate paging, genuine Traditional Cangjie full-code and Taiwan Zhuyin, improved key glyph legibility / proper 12×12 composition preview, save/load & nicknames, NPC/battle all-scene PyBoy visual check, `gfx/new_game/name_chinese.png` source raster review. 1.0 untouched; 1.x remains a development prototype, no public release claim.
- **Next concrete action:** Audit actual compiled `gfx/new_game/name_chinese.png` and in-game battle/pack frames; add failing asset/display tests on any Simplified glyphs, fix, rerun strict exact-head CI. Then tackle readability of 8×8 roots using established/attributed font practices and Rime-compatible preedit, without changing A–Z cell dimensions or codes. Keep existing hourly automation, never duplicate.

## Execution checkpoint — 2026-11-21 12:51 Asia/Taipei (verification blocked)

- Read current branch versions of EXECUTION_STATE, SUPERPOWERS_EXECUTION, TRUE_IME_ACCEPTANCE, and crystal-end-to-end-localization SKILL. Confirmed workflow triggers on source-code push and ignores Markdown-only changes.
- Investigated `gfx/new_game/name_chinese.png`: source GitHub connector's UTF-8 fetch failed with UnicodeDecodeError at PNG signature (binary PNG, not a text file). **No pixel audit was completed**, no claim that this asset is Traditional or even used in runtime. Next: retrieve as base64, decode PNG, trace assembly reference, inspect pixel raster and actual PyBoy scene; add RED/ GREEN bitmap regression if visibly wrong.
- Existing latest *documented* successful run is #44867512509, but **not verified as latest exact-head run in this execution**. GitHub commit search returned commits without proving branch association. Latest branch head, latest workflow run and artifact screenshots still require branch-scoped verification. A successful historical run is not a release gate.
- Local checkout/build blocked: sandbox git ls-remote returned `Could not resolve host: github.com` for both repositories. No local ROM compile or PyBoy execution occurred in this checkpoint. No code/raster fix, no RED/GREEN evidence; don't call this a successful implementation iteration.
- Remaining release gates: in-game bag pocket screenshot, `name_chinese.png` and other used raster assets, complete Quick vocabulary/ambiguity/paging/SRAM/nickname, genuine Zhuyin and Cangjie, linguistic review and all-scene visual acceptance.
- Exact next action: obtain branch-specific latest head and CI status/artifact; inspect referenced `name_chinese.png` raster in emulator, implement a failing pixel assertion and fix it if necessary; compile and verify with real PyBoy before declaring green. Preserve 1.0 and never distribute ROM.


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

## Checkpoint — 2026-11-21 13:54 Asia/Taipei — naming prompt Traditional source fix

- Read latest branch copies of all three execution documents and .agents skill. Verified source head before change `bb2087cfeb9082d0a3e0f1ad887fde9b538112b9`, build branch head `c2d4851b0c370bf3c5ec27d9bddcce44fb31710c` using GitHub commits API.
- **RED (source-string regression, not a PyBoy test):** `engine/menus/naming_screen.asm` still contained `劲敌的名字？`, `的昵称？`, and `妈妈的名字？` exactly once each. These are visible naming prompts, contrary to Taiwan/HK Traditional parity.
- **Code fix:** Source branch commit `11c47447c62f85c714d1edd20b08583318c69966` replaces these with `勁敵的名字？`, `的暱稱？`, and `媽媽的名字？`. A deterministic text assertion confirmed the old terms absent in the replacement source before upload; **no local build or PyBoy GREEN claimed**.
- **CI reality:** GitHub Actions query returned latest run [#44872657612](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44872657612), success for build code SHA `09523558c973dca7dd0eba000d24420e3acd4421` at 05:49 UTC, **before this source edit**. It does not validate source commit `11c4744`. The newer build HEAD is docs-only; no exact-head CI exists for this edit at checkpoint. Local git checkout remains blocked by `Could not resolve host: github.com`.
- **Asset inspection:** GitHub fetch_file with `encoding=base64` successfully retrieved `gfx/new_game/name_chinese.png` (PNG signature, blob `14ff15dc46f410ca7bb4ecef93d84ad1f73a16c1`, encoded length 289); binary retrieval is **not blocked** anymore. Still need decoded pixel inspection, ASM reference and live scene verification. Do not infer the art is correct.
- **Next exact action:** trigger and inspect a new full CI tied to source `11c4744`, including ROM compilation and PyBoy naming prompts; if any failure fetch job log and repair. Audit `name_chinese.png` pixels and runtime reference, then capture bag/trainer-card/burned-battle screenshots. Full Quick, candidate paging, Zhuyin, Cangjie, nickname and SRAM acceptance remain open. No 1.0 merge, ROM release or dictionary import.
