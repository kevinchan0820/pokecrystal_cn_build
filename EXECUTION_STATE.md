# Crystal 1.x — durable execution state

State: **IN PROGRESS (not a release)**

## Goal and release gate

Implement real Hong Kong **速成 / Quick** and Taiwan **注音 / Bopomofo** in the actual Game Boy Color naming interface, with controller key sequence → composition → candidate(s) → select → committed player/Pokémon name, all verified by real PyBoy + screenshot + SRAM save/load. Preserve 1.0 at branch `work/zh-hant-tw`.

## Last verified reality (do not exaggerate)

- Four earlier modes were: Mandarin Pinyin, English, Taiwan fixed-character grid, Hong Kong fixed-character grid. PyBoy grid-entry worked but is **not** a proper Quick or Zhuyin IME.
- True Quick **prototype code has now been written** in source repo `kevinchan0820/pokecrystal_cn`, branch `feature/zh-hant-tw-hk-1x`:
  - `engine/dfs/ime.asm`: mode 4 dispatch, two-code composer and Quick lookup.
  - `data/ime/ime_quick_twhk.asm`: initial test code table: A→日, AA→晶, AB→明, AD→杲. **Only four codes, not a complete dictionary.**
  - `engine/menus/naming_screen.asm`: fifth SELECT mode `速成(兩碼)`.
- Build repo `kevinchan0820/pokecrystal_cn_build` on same branch:
  - `tools/zh_tw_naming_qa.py`: five-mode SELECT wrap regression.
  - `tools/zh_tw_quick_pyboy.py`: real controller tests AA→晶 and AB→明; verifies ROM Quick code candidate symbol pointer, actual charmap bytes, candidate selection and screenshots. Tests must exit nonzero on failure.
  - `.github/workflows/zh-hant-ci.yml`: mandatory strict Quick PyBoy test **before** generating IPS.
- **Result not yet verified**. Need inspect the latest GitHub Actions run and fix compiler/runner errors before calling it successful.

## Next actions (in order, autonomous)

1. Read **latest** source/build branch SHA and latest GitHub Actions run, avoid relying on the SHA documented here if branch advanced.
2. If build fails: fetch GitHub Actions job logs, locate first error, fix root cause on 1.x branch and rerun, repeat. Do not change 1.0.
3. If PyBoy Quick fails: use screenshot JSON, actual RAM / symbol and button traces, fix real controller flow for A→A/AB. Keep exact expected character bytes `晶`, `明`.
4. Once Quick micro-dictionary passes, expand to broad dictionary with proper license/attribution review and ROM-bank budget, test ambiguous candidates, backspace, paging, full-name commit and persistence.
5. Then implement true Zhuyin using parallel framework and formal test ㄇㄧㄥˊ→明 / ㄚ→阿. Again do not label static char picker as phonetic input.
6. Persist results here and in CI artifacts; ship 1.x release only when `TRUE_IME_ACCEPTANCE.md` gates are satisfied.

## Execution discipline

- Each iteration **inspect → code → build → real PyBoy action → review screenshot/data → fix or record blocker → update next action**.
- At interruption commit the latest reproducible checkpoint and explicit unresolved root cause.
- Never say "still working in the background" unless an actual scheduled automation is active. A scheduled task runs at intervals, not continuously.
- User has enabled a recurring 4-hour ChatGPT automation on 2026-11-21 to continue this branch; do not create duplicate automations.
- Prohibited without user confirmation: merging to 1.0, redistribution of copyrighted ROM, deleting data, overwriting saves, publishing unverified release.
