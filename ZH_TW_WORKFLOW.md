# Pokémon Crystal — Traditional Chinese (Taiwan) work branch

This branch is an **in-progress** adaptation of [SnDream/pokecrystal_cn_build](https://github.com/SnDream/pokecrystal_cn_build). It is **not yet a playable Traditional Chinese release**.

## Sources and GitHub relationship

- Build fork: `kevinchan0820/pokecrystal_cn_build`, branch `work/zh-hant-tw`.
- Source fork: `kevinchan0820/pokecrystal_cn`, branch `work/zh-hant-tw`.
- `.gitmodules` points to the KC source fork and tracks the translation work branch. A Git submodule is normally pinned to a commit even with `branch = ...`; to update it explicitly, use `git submodule update --remote pokecrystal_cn` and commit the resulting pointer in this build repository.
- Upstream main text is `text.xlsx` (kept untouched). The workflow writes `text.zh-TW.xlsx` instead.

## Prepare a candidate workbook

Requires Python 3, `openpyxl`, and `opencc-python-reimplemented`:

```sh
python3 -m pip install openpyxl opencc-python-reimplemented
git clone --recursive --branch work/zh-hant-tw https://github.com/kevinchan0820/pokecrystal_cn_build.git
cd pokecrystal_cn_build
git -C pokecrystal_cn fetch origin work/zh-hant-tw
git -C pokecrystal_cn checkout work/zh-hant-tw

python3 tools/zh_tw_prepare.py --input text.xlsx --output text.zh-TW.xlsx --report zh_tw_report.json
```

The default `s2twp` OpenCC conversion is only a **draft**. Proper names and game terminology require a separate editorial pass against the official Taiwan naming convention. Optional phrase replacements can be supplied as `--overrides path/to/overrides.json` (a JSON object mapping source phrases to translated phrases).

## Check the audit

Read `zh_tw_report.json`. Characters listed in `missing_glyphs` lack a mapping in the existing font character tables. They **cannot safely be shipped as text only**, because the ROM's pre-rendered GB2312-indexed font assets must be updated consistently with the charmap and runtime routines.

Other problems to audit before calling this playable:

1. Font glyph images and runtime mapping: the existing `gfx/dfs/ChineseFonts_*.bin` assets are based on the original Chinese character map.
2. Text layout and byte limits: the upstream importers contain `GB2312`-specific checks (including Pokémon name padding). These are not made Traditional-Chinese-safe by the workbook converter.
3. Other text sources: the translated worksheet does not cover all static or dynamically constructed messages.
4. Chinese input-method character tables may require adaptation for Traditional Chinese naming.
5. Assemble, boot, and emulator-test the game, including name entry, battles, Pokédex, and a complete save/load cycle.

The first milestone is a **candidate + missing-font audit**, not a finished ROM.

## Using the candidate in original importers

The two original importer scripts now support an optional `PMC_TEXT_XLSX` environment variable, so you can test the translated workbook **without overwriting** `text.xlsx`:

```sh
export PMC_TEXT_XLSX=./text.zh-TW.xlsx
```

Do **not** run the full ROM build until missing glyphs, runtime mapping, and length assumptions have been fixed and validated. Keep output ROM files and save files out of Git.
