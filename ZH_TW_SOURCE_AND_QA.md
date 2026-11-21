# Pokémon Crystal zh-Hant-TW — source policy and Phase acceptance gates

Status: research and acceptance criteria only. Updated 2026-11-21. This document **does not claim the game is translated or playable**.

## Source-of-truth hierarchy

1. **Official Taiwan Pokémon Pokédex** — https://tw.portal-pokemon.com/pokedex/ . Use National Dex No. 0001–0251 as the stable key, not fuzzy Simplified-Chinese name matching. For example: No. 0158 小鋸鱷 — https://tw.portal-pokemon.com/pokedex/0158/ .
2. **Official Traditional-Chinese game materials** — terminology for game systems, moves, items, trainer classes where available, and coherent game-era usage. Example official site: https://tw.portal-pokemon.com/special/pika_vee/tc/20180712/ . A newer game's descriptions are *terminology examples*, not evidence that its gameplay rules match Generation II. Official Crystal reference: https://tw.portal-pokemon.com/topics/post_4/ .
3. **OpenCC** — https://github.com/BYVoid/OpenCC/blob/master/data/config/s2twp.json . The `s2twp` mode handles standard Taiwan character and phrase conversion. **Not an authority on proper nouns or gameplay text**; possible context errors require review.
4. **Secondary wiki** — https://wiki.52poke.com/zh-hant/ and https://bulbapedia.bulbagarden.net/wiki/List_of_Chinese_Pok%C3%A9mon_names . Use only to identify aliases or unresolved cases, never to supersede a verified official name.
5. **Upstream fan-made localization** — https://github.com/SnDream/pokecrystal_cn_build and https://github.com/SnDream/pokecrystal_cn . The supplied `text.xlsx` is the working dialogue base, **not an official Taiwan script**.

## Recording each translation decision

For names, moves, items, people, places and key UX strings, record:
`category | source_id (dex number or in-game ID) | simplified_original | zh-Hant-TW | source_url | evidence_level (official/secondary/provisional) | reviewed | notes`.

This record must live next to the project and support automated diffs. Do not treat an OpenCC result without a reference as officially confirmed. For the 251 species, preserve index order, including historical variant names; disambiguate by official National Dex ID.

## Phase gates

| Phase | Complete only after | Known missing/blocker as of 2026-11-21 |
| --- | --- | --- |
| 1. Repository setup | Source and build forks writable, work branches exist, reproducible submodule checkout proven | Submodule URL is changed, but gitlink remains pinned until explicitly updated and tested |
| 2. Translation and references | Inventory ALL text sources; convert `text.xlsx` to separately saved candidate; match all 251 names by Dex ID; review items, moves, locations, trainers and all dialogue; diff unconverted and unsupported tokens; preserve control codes | `tools/zh_tw_prepare.py` is committed but candidate file not yet generated or fully reviewed; no source-based terminology database yet; text exists beyond the spreadsheet |
| 3. Glyph/encoding | Audit every emitted Unicode codepoint against `constants/charmap_cn.asm` and *actual* `gfx/dfs/ChineseFonts_*.bin` glyph; assign collision-free codepoints; update font tiles, IME, byte-length and wrapping logic; render screenshot tests | Current font assets map the original GB2312-ordered glyph table. Byte sizing still uses GB2312; conversion alone cannot fix rendering |
| 4. Build and QA | Fresh recursive checkout, import, assemble with RGBDS, boot-test intro, new-game naming, dialogue, encounters, battles, menus, Pokédex, save/reload, Hall of Fame; evidence/logs attached and no blocking errors | No reproducible built ROM and no emulator execution verification |
| 5. Delivery | Diff and attribution reviewed; reproducible instructions, open-issues list, source links, test matrix; private work product separated from upstream; no ROM committed | Not reached |

**Gate rule:** A Phase can be labeled *done* only when measurable proof exists. Failures become documented issues and remain open, rather than being described as completed by default.

## Source-code-specific audit findings

- `tools/text_import_sys.py` imports main game names using the sheets `宝`, `训`, `类`, `城`, `道`, `招`, and `图`.
- `tools/text_import_text.py` reads dialogue from `文1` through `文9`, using column E for the original Chinese text and other columns for control metadata. Blind conversion of other columns risks breaking control mapping.
- The original system imports and checks text length using `gb2312`; any unsupported Traditional glyph can fail a name padding operation or show as invalid rendering.
- `constants/charmap_cn.asm` is organized around GB2312 and `gfx/dfs/ChineseFonts_*.bin` stores pre-rendered glyph tiles, so a Unicode character being in an OpenCC output is **not** sufficient proof it can display.
- The existing `zh_tw_prepare.py` checks charmap entries but cannot prove that mapped font tiles display the correct Traditional form. Font glyph audit and in-game rendering tests are essential.
- `.gitmodules` currently tracks the owner's source fork and requests branch `work/zh-hant-tw`, but changing `branch` does not automatically change the pinned Git submodule commit.
- The Taiwan official site provides names and general game terminology; **no complete official Chinese script for the 2000 GBC Crystal edition has been confirmed publicly available**. Any translated dialogue requires independent checking.

## References and short confirmations (retrieved 2026-11-21)

- Taiwan Pokémon official Pokédex: https://tw.portal-pokemon.com/pokedex/ — “No.0001妙蛙種子”.
- Taiwan official No.0158 page: https://tw.portal-pokemon.com/pokedex/0158/ — “小鋸鱷”.
- Official Crystal page: https://tw.portal-pokemon.com/topics/post_4/ — “寶可夢 水晶版”.
- Official Let's Go site: https://tw.portal-pokemon.com/special/pika_vee/tc/20180712/ — “招式學習器”.
- OpenCC `s2twp.json`: https://github.com/BYVoid/OpenCC/blob/master/data/config/s2twp.json — “Taiwan Standard, with Taiwan Phrases”.
