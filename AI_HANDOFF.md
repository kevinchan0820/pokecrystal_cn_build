# Pokémon Crystal 台港繁體 1.x — AI HANDOFF (canonical entrypoint)

## Verified latest checkpoint — 2026-11-21: real 速成 + 倉頡5, visual $7f corruption fixed

- **Exact complete green CI:** [#44882445971](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44882445971), **SUCCESS**, actual ROM built after game-source commit `e9f8f5057b2031f50ea5f334465f5e452957ceb8`, build-code commit `05c55dcfeb746175488351e00a5bcda5abfb0e32`. IPS and screenshots in artifact `zh-hant-1x-twhk-input-prototype-and-reports`. Source/Build SHA verified by generated `zh_tw_ci_handoff.json`. **1.x IS NOT READY: 台灣注音 absent, SRAM/end-to-end acceptance incomplete.**
- **True Quick functional tests PASS:** full code-glyph mapping from pinned MIT Cangjie5 source in compiled ROM (7,157 Quick candidate pairs, 611 populated code keys), actual D-pad AA→晶, AB→明, VD→好, A→日/曰 select second 曰, ZZ no candidates + B recovers, MM six candidate rows and actual controller paging with visual changes.
- **True full Cangjie5 functional tests PASS:** distinct mode5, real root code composition `VND→好`, `AAA→晶`, `AB→明`, WRAM-bounded 7-candidate scratch with intact double terminator, player name written correctly, invalid input and backspace, mode5→Pinyin restores alphabet. Dynamic full-code dictionary from pinned MIT Cangjie main table: **7,719 full-code character pairs**, **7,520 distinct full codes** (post 9,973-glyph remap), bounded 703 prefix index and 3KB ROMX chunks. Actual 160×144 PyBoy screenshots `zh_tw_cangjie_five_root_mode.png`, `zh_tw_cangjie_typed_VND.png`, `zh_tw_cangjie_committed_VND.png` etc.
- **Real GUI defect found on screenshot AFTER CI green**: adding sixth title loaded tiles $6e..$7f, overwriting GBC blank tile **$7f** and filling empty screen with black garbage. Corrected by keeping 15 resident title tiles $6e..$7c and swapping Cangjie title into safe first three tiles only while mode5; restored Pinyin when leaving. Added PyBoy screen-pixel invariant to BOTH `zh_tw_quick_ui_qa.py` and `zh_tw_cangjie_pyboy.py`: blank name-panel pixel count MUST be zero. [#44882445971](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44882445971) exact green, screenshots visually inspected clean. **This proves why RAM-only, compile-only, candidate-only tests are not enough**.
- **Critical remaining blockers:** genuine Taiwan 注音 symbols & tones + actual GBC keyboard/candidates/commit; human legibility of dense 8x8 Cangjie roots, selected-root composition preview; actual Pokémon nickname and SRAM saving/reloading, bag/trainer-card and battle/burn gameplay screenshots; full Traditional language/bitmap UX review, GBC patch hardware checks. Do not treat current prototype IPS as the final requested patch.
- **NEXT ACTION (execute without KC typing continue):** Implement Taiwan 注音 with actual `ㄇㄧㄥˊ→明` and `ㄚ→阿` via real phonetic symbols, not Pinyin mapping. OpenVanilla [McBopomofo](https://github.com/openvanilla/McBopomofo) is MIT; source `Source/Data/BPMFBase.txt` pinned commit `1b7fbb999a354ba80e5cf20820ddd4093c6ed77e`, blob `6febbf06265bbde71e5234a3e8c52dd3cf636a40`. Plan 41 phonetic symbols/tones, two pages of original 26 8x8 keys, code buffer 4 symbols and phonetic full syllable lookup; ensure keyboard toggling, old modes and blank tile $7f safe; add tests first. Then SRAM and visual acceptance. Deliver the final verified IPS AND matching actual PyBoy PNG only after all gates.
- **Risk control:** user explicitly requires no display crashes, name overflow, incorrect candidate paging, stuck controls, bank overflow, save corruption, English/Pinyin regression or false green. Tests must inspect pixels, ROM pointers, double-byte name terminators and real SRAM.

## Verified checkpoint — 2026-11-21: FULL 速成 code corpus now in actual ROM (NOT final product)

- **Exact successful CI:** [#44880819421](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44880819421), **SUCCESS**, built from game source SHA `04a8387edb303fff9ac6170b6c1ec49ff4a9e5ae`, build code SHA `69f6b985ab3865c6e3fc410882e880373dd49bb7`; canonical `zh_tw_ci_handoff.json` confirms both and current IPS SHA256 `cc558e0c1dbd28c50c39d656a7b7834b68fb06412c053684d5e280def5b8a896`. This is **not a release approval**.
- **New actual implementation:** `engine/dfs/ime.asm` uses a dense 703-index Quick table with a safe ROM0 `GetFarByte` helper; source `data/ime/ime_quick_v2.asm` supplies a 703-entry stub when building the game independently; the build repo's `tools/zh_tw_quick_dictionary_v2.py` replaces it after generating a final Traditional charmap with data from **pinned MIT** `cangjie-system/rime-cangjie-integrated` `dcfba770189078a2f7b347793c8e155c3c39275d`. Avoid collecting external `resources/` files with different licences. See `THIRD_PARTY_LICENSES.md`.
- **Exact new corpus coverage:** 7,157 unique code-to-character candidate pairs; 611 populated Quick code slots (703 possible slots), six 3KB-safe ROMX candidate chunks; up to 45 candidates per key / 6 candidate rows, restricted to 9,973 compiled Traditional glyph mappings. `zh_tw_quick_v2_dictionary_report.json` still has the **stale generator label** `DATA_PREPARED_NOT_LINKED_INTO_ROM`, but the ROM integration is independently confirmed by actual **PyBoy** `QuickV2_*` address and real name writes. Fix that report wording when changing generator, don't use this inconsistency to deny proven runtime behavior.
- **Real controller scenarios PASS:** `AA→晶`, `AB→明`, `VD→好`, `A→日/曰` with second candidate 曰 actually committed to player name and terminator intact, `ZZ` produces no candidates and B recovers without corruption, `MM` displays six candidate rows and real D-pad route **LEFT, DOWN, A** scrolls to second page (`wIMELine=1`) without altering name/keyboard or leaving stale pixels. Evidence: `zh_tw_quick_ui_A_multiple_candidates.png`, `zh_tw_quick_ui_A_selected_YUE.png`, `zh_tw_quick_ui_MM_first_page.png`, `zh_tw_quick_ui_MM_scrolled_page.png`, `zh_tw_quick_ui_name_HAO.png`, `zh_tw_quick_ui_invalid_ZZ_no_candidates.png`, all in #44880819421 artifact and raw/4x versions.
- **Existing source projects:** `1.0` left unchanged. Full Cangjie (up to five roots) and Taiwanese 注音 (symbols + tones) **NOT IMPLEMENTED**. Player/Pokémon SRAM save/reload, gameplay battle/bag/trainer-card frames, human 8x8 root readability and all-scene Traditional editorial audit remain release blockers. **Final IPS+matching real PyBoy PNG for all three IMEs not ready.**
- **NEXT IMMEDIATE ACTION without asking KC:** implement full Cangjie data generator from same pinned MIT source, direct code→candidate with max five code letters and byte-safe scratch, add mode5 with same 8x8 root keyboard; commit RED/GREEN tests and actual PyBoy `VND→好`, `AAA→晶`, `AB→明`; then build Taiwan Zhuyin input with actual ㄇㄧㄥˊ→明 and ㄚ→阿. Add SRAM and UI regression checks, output final legal IPS + same-source PNG only after all mandatory gates.
- **Visual concern:** latest 4x Quick screenshots contain densely rasterized 8x8 glyphs, especially complex roots 難/符. The source pixel identity test does not establish human legibility. Must add a larger composition/selected-root preview or approved 8x8 redesign before final user-facing PNG.

> **給下一個 AI：不要讀完整 ChatGPT 對話才開始。先讀呢份文件，再讀最新 GitHub branch / CI。** 本文件係固定入口，不代表其中時間戳一定係最新狀態。

## 1. Parent goal / Definition of Done

KC 要交付 **可重現構建、完整可玩、台港繁體像素字形正確嘅 Pokémon Crystal 1.x IPS Patch**。香港人可以用真正 **速成及倉頡**，台灣人可以用真正 **注音**，訓練家及寶可夢改名、儲存／讀取、實際遊戲畫面都通過驗收。唔好改動 1.0 原味版。只可以分享有權分發嘅 source + IPS，不可分享 Nintendo ROM。

具體驗收見 [SUPERPOWERS_EXECUTION.md](SUPERPOWERS_EXECUTION.md)（Autonomous completion contract）、[TRUE_IME_ACCEPTANCE.md](TRUE_IME_ACCEPTANCE.md)、[RUNTIME_TRADITIONAL_IMAGE_AUDIT.md](RUNTIME_TRADITIONAL_IMAGE_AUDIT.md)。**CI PASS 只代表 CI 涵蓋嘅子測試通過；唔代表產品完成。**

## 2. Branches and exact provenance

| Purpose | Repository | Only branch |
|---|---|---|
| Game source (ASM, graphics, IME) | [kevinchan0820/pokecrystal_cn](https://github.com/kevinchan0820/pokecrystal_cn/tree/feature/zh-hant-tw-hk-1x) | `feature/zh-hant-tw-hk-1x` |
| Build, QA, reproducible IPS | [kevinchan0820/pokecrystal_cn_build](https://github.com/kevinchan0820/pokecrystal_cn_build/tree/feature/zh-hant-tw-hk-1x) | `feature/zh-hant-tw-hk-1x` |

**Latest verified CI:** [#44878037890](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44878037890), SUCCESS, tested game source `88c39dc044109e3497e90b3659daa8662a886fa4`, workflow build commit `2659ffefc44f48a07baa676d7fc9707982879c00`. Artifact provides `zh_tw_ci_handoff.json`: nine scoped tests pass, four real PyBoy screen references, patch SHA256, `release_ready: false`. Later Markdown-only commits do not retrigger CI. Always re-check live branch heads and the latest Action.

**FIRST ACTION EVERY SESSION:** Read *live* branch heads, latest Action run for the build branch, job logs, downloadable artifact, and current [EXECUTION_STATE.md](EXECUTION_STATE.md). Exact run evidence is more authoritative than old green notes. If current HEAD includes only Markdown changes, CI may not retrigger (`paths-ignore: '**/*.md'`); use latest successful code SHA only if source SHA matches.

The Actions artifact now provides `zh_tw_ci_handoff.json`, `zh_tw_ci_handoff.md`, `zh_tw_source_commit.txt`, PNG screenshots, per-test JSON reports and IPS checksum. These are machine-readable **run evidence**, not release approval.

## 3. Verified functionality, without exaggerating

- **This continuation fixed REAL Simplified inline ASM names:** `data/player_names.asm` had `自己决定／小阳／克丽丝／千瑶` (not workbook strings); corrected to `自己決定／小陽／克麗絲／千瑤`. Source-level test `zh_tw_player_names_report.json` in CI #44878037890 verified true, zero failures. Runtime selection screen still requires visual proof.
- **Source reference discovery:** new `zh_tw_asset_reference_report.json` scanned 2,510 source/build files and proved `gfx/new_game/name_chinese.png` is referenced by `engine/gfx/player_gfx.asm:80` (`PlayerGFX_Name`). The raster is loaded by `ShowPlayerNamingChoices`; **in-game rendering and regional pixel correctness have NOT been visually accepted yet**.
- **Cross-session handoff was exercised:** the existing hourly agent read `AI_HANDOFF.md` and recorded an independent false-positive inline-comment bug fix in `EXECUTION_STATE.md`. Recovery is demonstrated for this step, not a guarantee of indefinite future agent availability.

- 1.x source compiles and boots in PyBoy; initial menus, options, naming flows are exercised in GitHub Actions.
- Quick **tiny prototype dictionary**: real controller `AA → 晶`, `AB → 明`, `VD → 好` with actual candidate selection and named bytes.
- In Quick mode the 26 **日月金木水火土竹戈十大中一弓人心手口尸廿山女田難卜符** roots occupy original A-Z 8x8 key cells; actual Q-Z frame-pixel audit was RED then GREEN after fixing VRAM bank1 copy from 16 to 26. **Human legibility still unapproved**.
- Pixel assets converted and checked: 96x8 `符號／刪除` name action toolbar, Traditional mode headers, title logo checks, `精靈球` bag tilemap, `目前狀態` Trainer Card raster.
- Battle localization **source** audit checks `敵人／灼傷`; original user screenshot may be from earlier patch and has no verified ROM SHA. **No actual burned-battle screenshot pass yet**.

## 4. UNFINISHED — Product is NOT RELEASE READY

1. True practical HK Quick dictionary, multiple candidates, paging, wrong-code/delete, persistent player and Pokémon nicknames.
2. Full HK Cangjie compose and lookup, Taiwan Zhuyin symbol/tones input, 8x8 font UX.
3. Actual PyBoy gameplay screen acceptance: battle/burn status, bag, Trainer Card, credits, overworld, story text, name screen and save/load.
4. `gfx/new_game/name_chinese.png` IS referenced by `engine/gfx/player_gfx.asm:80`; reach `ShowPlayerNamingChoices` in actual PyBoy, capture screen, validate its pixel text and the four newly Traditionalized player-name choices. Do not assume static reference alone proves the rendering.
5. Regional editorial review beyond mechanical OpenCC; no claims of 100% coverage without real verification.

### NEXT EXECUTABLE TASK (do it; don't ask KC to continue)

Read latest GitHub source and build heads and the current `zh_tw_ci_handoff.json` from [#44878037890](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44878037890) or a newer exact-head run. **First independent release gate:** make a real PyBoy screenshot test of `ShowPlayerNamingChoices` showing the approved Traditional choice `自己決定`, presets `小陽／克麗絲／千瑤`, and the real `PlayerGFX_Name` bitmap. If the 40×8 bitmap is non-Taiwan glyph art, create a failing raster test, replace only the sourced asset and rerun CI/PyBoy. Then validate Bag, Trainer Card and burned battle as actual visible scenes; continue to the remaining practical Quick/Cangjie/Zhuyin/save-load blockers.

## 5. Execution rules (trigger on Intent, not magic words)

**Discover → Define → Test (RED) → Implement → Debug → Retest → Real PyBoy Screenshots → Verify → Commit → Next task.**

- Answer straightforward questions directly. For actual goals, execute immediately; don't hand back a plan or expect `continue`.
- Preserve the user's parent goal and Definition of Done; a green subtask is NOT a final release.
- At natural run boundary update [EXECUTION_STATE.md](EXECUTION_STATE.md) and this file (only if necessary), with exact source SHA, build SHA, CI ID and first next actionable task. New model should resume from it without redoing old investigations.
- Check [project Skill](.agents/skills/crystal-end-to-end-localization/SKILL.md) and Superpowers original [skills](https://github.com/obra/superpowers). Project-specific skill in GitHub isn't automatically installed in ChatGPT.
- Do not guess success; use exact-head CI and genuine PyBoy image evidence. If a tool is unavailable (e.g. local git DNS), prefer connected GitHub + cloud Actions; document real blockers.
- Never make irreversible external decisions, release proprietary ROM binaries, or merge into 1.0 without authorization.

## 6. New ChatGPT conversation recovery

The user can open a fresh chat **inside the same E2E Project** and send:

```text
繼續 Pokémon Crystal 1.x。先讀
https://github.com/kevinchan0820/pokecrystal_cn_build/blob/feature/zh-hant-tw-hk-1x/AI_HANDOFF.md
再查兩個分支 HEAD、最新 CI、EXECUTION_STATE.md，按 Project Instructions 自動恢復最後未完成嘅工作；唔使我逐個 Phase 講 continue。
```

This one-line recovery prompt is a fallback, not a requirement to re-describe the goal. A new model still needs live GitHub access, valid connector permissions and access to this branch. The **Project Instructions** supply behavior; **this repo supplies state/evidence**; **a real ongoing automation** is needed for work after chat session ends.
