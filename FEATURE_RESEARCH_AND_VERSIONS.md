# Crystal Traditional Chinese (TW/HK) — release variants and player research

Research checked: **2026-11-21**. This file is a backlog and design record; it does **not** claim any gameplay changes are implemented.

## Product decision: different builds, not unbounded features in the base build

| Build line | Scope | User-visible features | Release gate |
| --- | --- | --- | --- |
| **Vanilla zh-Hant 1.0** | Faithful Crystal gameplay | Taiwan Pokémon names and region-natural wording, Traditional font, title and menus, original rules | Full translation inventory, battle/naming/menu screenshots, cross-map and save/load QA, zero blocking localization defects; **current status: release candidate, incomplete functional QA** |
| **Accessible zh-Hant 1.x** | Naming accessibility, still normal balance | Chinese name entry for TW/HK players, selecting input schemes (Taiwan **注音**, HK **倉頡/速成** and optional **粵拼**, existing English and Mandarin Pinyin), optional in-game rename trainer and own Pokémon; use separate patch until save compatibility is validated | Verify input layouts on actual 160×144 Game Boy Color screens, exact keyboard controls, character coverage, Chinese name-length limits, save/load, trade, OT attribution, GB/GB Color/Delta behavior |
| **Convenience 2.x** | Optional Quality of Life | Running speed, improved PC/box management, reusable TMs, easier trade evolutions, optional easier rematches, shorter repeated animations | Individual toggle or opt-in variant; balance, scripted events, legacy save compatibility, link trading tested |
| **Sandbox 3.x (opt-in)** | Cheats and randomizers (requested by project owner) | Categories such as encounters, experience, money, items, battles; per-feature ON/OFF, defaults OFF and visible active indicators | Detailed testing of flag persistence, game-state safety, overflow, RTC, trainer battles, link interactions and save migration; excluded from vanilla and competitive builds |

## Work completed / real limitations

- The existing naming engine already offers Mandarin Pinyin and English selection with SELECT: `engine/menus/naming_screen.asm`, `engine/dfs/ime.asm`, `data/ime/ime_entry.asm`, `data/ime/ime_table1.asm`, `data/ime/ime_table2.asm`. **Do not describe this as Hong Kong Cangjie or Taiwan Zhuyin support.**
- Player name is chosen in the original intro and Pokémon nicknames are offered in game; changing the player name *after* an existing save starts is different from initial naming. Care is required for trainer display, save checksum and old Pokémon Original Trainer identity. Existing Pokémon nickname rules distinguish owned vs traded monsters.
- A Game Boy Color has a small fixed display and directional-pad navigation; copying a desktop IME into the ROM verbatim is not realistic. Input dictionaries need to be trimmed and compiled into data tables, with clear candidate pagination and optional fallback to manual character selection.
- Source code uses a double-byte Chinese charmap and pre-rendered 12×12 font assets; for user-supplied names test exact glyph availability in both font and IME.
- Saving additional input settings or cheats in `wOptions`/`sOptions` or expanding existing save records can corrupt older saves unless reserved fields and migration logic are proven safe. Original vs enhanced builds must explicitly disclose save compatibility.

## Proposed TW/HK naming interaction — **NOT IMPLEMENTED**

- From initial trainer naming, nickname prompt, and a later optional rename menu, choose input: **注音** / **倉頡** / **速成** / **粵拼** / **拼音** / **英文** / **字表選字** (if ROM/UI budgets allow; staging schemes separately is acceptable).
- **Taiwan:** 注音 (Bopomofo) as default in TW variant; use a gamepad-friendly syllable/candidate UI rather than full PC keyboard. Candidate ordering should prioritise common personal-name characters.
- **Hong Kong:** 倉頡 or 速成 as keyboard-based options; 粵拼 may help phonetic typists. A stroke/character table fallback avoids requiring Latin phonetic conventions from all users.
- **Validation examples**: player name `阿明`, `家豪`, `怡君`; Pokémon nicknames `小火`, `阿寶`, `皮卡` and mixed Latin/Chinese. Verify glyphs, cursor/backspace, page changes, zero-width/unsupported characters, every entry path, and legacy saves.
- For player **rename** after starting, update only the player-facing name by default, preserve prior Pokémon OT identity unless the user explicitly requests migration, and do not silently alter trainer ID or traded Pokémon.

## Battle text and local phrasing — verified source

- **Use `效果絕佳！`, not `效果拔群`.** Official Taiwan Pokémon site gives an effectiveness example using exactly “效果絕佳”. Source: https://tw.portal-pokemon.com/special/pika_vee/tc/20180712/ (section: type effectiveness).
- Current localized workbook at `文3!E2837` has `效果絕佳！`, and at `文3!E2829` has `擊中了要害！`. These were **observed in the 2026-11-21 workbook**, not independently verified in every emulator battle.
- Avoid bulk substitutions for context-dependent words such as `記錄` (can mean keeping a record), `初訓家` (Original Trainer / OT, a historically used game term), or `拼音排序` (cannot call it 注音排序 unless sorting behavior changes).
- Existing Taiwan UI editorial rules: `data/zh_tw_locale.json`; reports: `zh_tw_locale_report.json`; battle regressions should be automated separately.

## Public community signals: concrete features, not population estimates

1. **Pokémon Modern Crystal**: optional starting randomizers, reusable TMs, XP multiplier, trainer rematches, fast movement, stats pages, self-trade NPC; the project demonstrates a menu-first customization architecture, not automatic source compatibility: https://github.com/AmmonRoberts/PokemonModernCrystal
2. **Polished Crystal**: configurable abilities/natures, storage redesign, 60fps movement, running shoes, continuous repel, unlimited TMs and richer Pokédex. Much of this changes vanilla balance; reference design only: https://github.com/Rangi42/polishedcrystal
3. **Reddit faithful-Crystal discussion (2026-01)**: users value compatibility with original hardware and a way to obtain all original 251, rematch trainers, quicker healing and early trade-evolutions, but caution against overexpansion: https://www.reddit.com/r/pokemoncrystal/comments/1qq589g/rom_hack_features/
4. **Reddit QoL preferences (2026-04)**: independent comments highlight HMs integrated with Pokégear, reusable TMs, rematches and convenient training, while noting that Polished Crystal can exceed a “faithful” scope: https://www.reddit.com/r/pokemoncrystal/comments/1saglad/whats_the_best_rom_for_only_quality_of_life/
5. **Cross-hack preferences (2024)**: repels, time adjustment, expanded TM access, easy training, optional challenge modes; the discussion is not specific to this project's TW/HK player base: https://www.reddit.com/r/PokemonROMhacks/comments/1dwvetc/what_are_your_must_have_features_for_rom_hacks_in/

These discussions are *qualitative evidence*, not a scientifically representative Taiwan/Hong Kong survey. No player-count or demand-share claim is made.

## Input dictionary research and license caveats

- Taiwan 注音: https://github.com/rime/rime-bopomofo (LGPL-3.0; game integration would need licensing review and adaptation).
- Hong Kong 粵拼: https://github.com/rime/rime-cantonese (CC BY 4.0 / ODbL 1.0; dictionary/map-file rights vary).
- 倉頡/速成 and other IMEs: https://github.com/rime/plum (index of schemas; check each upstream license separately).
- Do **not** import any Rime dictionary or code verbatim into this ROM before verifying attribution/license compatibility, font coverage, ROM bank capacity, candidate performance and gamepad UI.

## Prioritization of feature versions

**1.0 Vanilla**: finish translation and game screenshots, title/menu, battle text, naming and save/RTC. No in-game cheats and no gameplay rebalance.

**1.x Accessible naming**: implement and test TW/HK IMEs, followed by explicit trainer/monster rename capability; exact feature allocation depends on verified ROM and SRAM resources. Keep separate from original until compatibility is proven.

**2.x Convenience**: selected frequent QoL requests as independently switchable features, default OFF when gameplay or balance changes.

**3.x Sandbox/Cheats**: opt-in and categorized: money/items, experience, encounter control, party/battle, utility. Document features as cheats, include an all-OFF reset, don't pretend they are vanilla, and test save integrity and exploits. No silent gameplay change.

## Build and release criteria

- Have **separate** variant source branches and patch filenames/manifest hashes, not a runtime switch in the original release.
- Review each improvement against source code and CI-generated screenshots; where automated boot tests are insufficient, mark manual test pending.
- Source changes must not silently redistribute copyrighted base ROM binaries. Ship patches/instructions and evidence artifacts.
- Do not claim the advanced input method or cheat menu exists until the actual ROM and emulator tests prove it.
