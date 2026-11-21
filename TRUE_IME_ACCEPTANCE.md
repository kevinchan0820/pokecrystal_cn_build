# 1.x 真正輸入法 Priority & Release Gate

**Status: PARTIAL PROOF OF CONCEPT — NOT A RELEASE.** The existing Pinyin, English, Taiwan and Hong Kong common-character pickers are *not* genuine regional IMEs. A fifth **Quick/速成** mode now performs actual code-to-candidate lookup for a **four-code test dictionary**: in GitHub Actions run [44863353708](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44863353708), real PyBoy controller input **AA → 晶** and **AB → 明** both passed with matching compiled charmap/name bytes and screenshots. Quick dictionary breadth, invalid-code handling, candidate ambiguity/paging, saving/reloading, Pokémon nickname flow and all Zhuyin/Cangjie work remain unverified or unimplemented. Do not release 1.x or call the small dictionary a complete IME.

## Regional priority

1. Taiwan: **注音 / Bopomofo** (compose phonetic symbols and tones, then choose a candidate)
2. Hong Kong: **速成 / Quick** (type first/last Cangjie Latin codes, then choose a candidate)
3. Hong Kong: **倉頡 / Cangjie** (full character-root codes), after Quick
4. Keep English and Mandarin Pinyin as fallback. Common-character picker remains a fallback, not a replacement. Jyutping as an optional later mode.

This is a supported product priority, **not a verified 2026 market-share ranking**. Historical government survey period Jan–Mar 2000: HK Quick 37.9%, Cangjie 34% of those who knew an input method; academic Taiwan research identifies Zhuyin among its most popular methods.

## Definition of Done — REAL PyBoy button presses required

- **Quick test**: navigate to *Quick*, compose `A` then `B`; verify on-screen composition `AB` produces candidate `明` (Cangjie `ab`). Compose `AA`; verify `晶` (Cangjie `aaa`, Quick first+last `aa`). Select candidate; verify displayed player name AND actual committed name bytes.
- **Zhuyin test**: navigate to *注音*, compose `ㄇㄧㄥˊ`; verify candidate `明`. Also `ㄚ` -> candidate `阿`. Select and verify result in the player's actual name.
- **Cangjie test**: after implementation, verify full-code lookup (not Quick abbreviations).
- For all modes test wrong code/no result, candidate paging, backspace during composition and after commit, multiple characters, maximum name length, player naming and Pokémon nicknames, save/reload and emulator screenshot evidence.
- **Block CI and release if code-to-candidate-to-name is unproven.** Compile success, a menu screenshot or static charset coverage is insufficient.
- Real screenshots must come from actual PyBoy game frames, never mockups. Document test ROM commit, input trace, screenshot, output buffers, expected vs actual.

## Upstream and licensing

- Rime Quick: https://github.com/rime/rime-quick : “速成取倉頡碼的首尾二碼”
- Cangjie5: https://github.com/rime/rime-cangjie/blob/master/cangjie5.base.dict.yaml , examples `明 ab` and `晶 aaa`. Dictionary header says **GPL** — review rights and distribution conditions before bundling or modifying the table.
- Bopomofo: https://github.com/rime/rime-bopomofo/blob/master/bopomofo.schema.yaml (standard Bopomofo keyboard).
- HK government household survey (data Jan–Mar 2000, **not current**): https://www.statistics.gov.hk/pub/B11302022000XXXXB0100.pdf
- Taiwan academic background (2003, **not current**): https://academic.oup.com/jcmc/article/9/1/JCMC912/4614467

Verified research 2026-11-21. Implementation status as of this document is *NOT STARTED* for true Quick, Zhuyin, Cangjie.
