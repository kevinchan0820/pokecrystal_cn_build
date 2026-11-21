# 1.x 真正輸入法 Priority & Release Gate

**Status as of 2026-11-21: ALL THREE REAL IME CONTROLLER SMOKE TESTS PASS, FULL RELEASE GATES BLOCKED.** Exact-head [Actions #44888027824](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44888027824) **success**, source `94dcb27736a633598970d21c96e59263a283c32e`, build `9c6765581897e23c60c8c6de2a5e8a8f283a7ca0`, machine artifact `14700816438`. Actual PyBoy D-pad: real 速成 `AA→晶`, `AB→明`, `VD→好`, invalid `ZZ`, candidate paging; genuine full-code 倉頡 `VND→好`, `AAA→晶`, `AB→明`, invalid backspace; genuine 41-symbol Taiwan 注音 `ㄚ→阿` and `ㄇㄧㄥˊ→明`, keyboard-page transition and name bytes. All three methods display real raw 160×144 PyBoy screenshots, not mockups. The four-code Quick prototype described in older entries below is **historical and superseded**. Save/reload of SRAM, Pokémon nickname flow, full region-wide raster/editorial visual acceptance, error/stress matrix and human readability of 8×8 input glyphs **are not yet accepted**. Never label 1.x RELEASE_READY from this scoped CI green alone.

## Regional priority

1. Taiwan: **注音 / Bopomofo** (compose phonetic symbols and tones, then choose a candidate)
2. Hong Kong: **速成 / Quick** (type first/last Cangjie Latin codes, then choose a candidate)
3. Hong Kong: **倉頡 / Cangjie** (full character-root codes), after Quick
4. Keep English and Mandarin Pinyin as fallback. Common-character picker remains a fallback, not a replacement. Jyutping as an optional later mode.

This is a supported product priority, **not a verified 2026 market-share ranking**. Historical government survey period Jan–Mar 2000: HK Quick 37.9%, Cangjie 34% of those who knew an input method; academic Taiwan research identifies Zhuyin among its most popular methods.

## Definition of Done — REAL PyBoy button presses required

- **Quick test**: navigate to *Quick*, compose `A` then `B`; verify on-screen composition `AB` produces candidate `明` (Cangjie `ab`). Compose `AA`; verify `晶` (Cangjie `aaa`, Quick first+last `aa`). Select candidate; verify displayed player name AND actual committed name bytes.
- **Zhuyin test**: navigate to *注音*, compose `ㄇㄧㄥˊ`; verify candidate `明`. Also `ㄚ` -> candidate `阿`. Select and verify result in the player's actual name.
- **Cangjie test**: verify genuine full-code lookup (not Quick abbreviations); current VND/AAA/AB scenarios pass, wider acceptance still required.
- For all modes test wrong code/no result, candidate paging, backspace during composition and after commit, multiple characters, maximum name length, player naming and Pokémon nicknames, save/reload and emulator screenshot evidence.
- **Block CI and release if code-to-candidate-to-name is unproven.** Compile success, a menu screenshot or static charset coverage is insufficient.
- Real screenshots must come from actual PyBoy game frames, never mockups. Document test ROM commit, input trace, screenshot, output buffers, expected vs actual.

## Upstream and licensing

- Rime Quick: https://github.com/rime/rime-quick : “速成取倉頡碼的首尾二碼”
- Cangjie5: https://github.com/rime/rime-cangjie/blob/master/cangjie5.base.dict.yaml , examples `明 ab` and `晶 aaa`. Dictionary header says **GPL** — review rights and distribution conditions before bundling or modifying the table.
- Bopomofo: https://github.com/rime/rime-bopomofo/blob/master/bopomofo.schema.yaml (standard Bopomofo keyboard).
- HK government household survey (data Jan–Mar 2000, **not current**): https://www.statistics.gov.hk/pub/B11302022000XXXXB0100.pdf
- Taiwan academic background (2003, **not current**): https://academic.oup.com/jcmc/article/9/1/JCMC912/4614467

Historical baseline research from 2026-11-21 (not implementation status). Current verified implementation status is recorded at the TOP of this document and in live CI's `zh_tw_ci_handoff.json`.
