#!/usr/bin/env bash
# Produce a ROM locally without committing Nintendo-owned binaries to Git.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f text.xlsx ]]; then
  echo "text.xlsx is missing (original workbook is required)" >&2
  exit 1
fi
if [[ ! -f pokecrystal_cn/constants/charmap_cn.asm ]]; then
  git submodule update --init --recursive
fi

FONT_FILE="$(printenv ZH_TW_FONT || true)"
if [[ -z "$FONT_FILE" ]]; then
  FONT_FILE=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc
fi
if [[ ! -f "$FONT_FILE" ]]; then
  echo "No Traditional-Chinese font. Set ZH_TW_FONT to a font .ttc/.otf file" >&2
  exit 1
fi

# Keep the original text.xlsx and original fork branches untouched.
# The submodule is normally pinned; select the translation work branch explicitly.
# The 1.x branch builds from its own source fork, never the vanilla 1.0 head.
SOURCE_BRANCH="${ZH_TW_SOURCE_BRANCH:-feature/zh-hant-tw-hk-1x}"
git -C pokecrystal_cn fetch origin "$SOURCE_BRANCH"
git -C pokecrystal_cn checkout --detach FETCH_HEAD
echo "Using 1.x source: $SOURCE_BRANCH ($(git -C pokecrystal_cn rev-parse --short HEAD))"
# Fail before building if the original Simplified title graphic is still present.
python3 tools/zh_tw_title_check.py
python3 tools/zh_tw_prepare.py \
  --input text.xlsx \
  --output text.zh-TW.xlsx \
  --report zh_tw_report.json \
  --species data/pokemon_zh_hant_251.json
python3 tools/zh_tw_static.py \
  --source pokecrystal_cn \
  --report zh_tw_static_report.json
# Context-scoped editorial wording applied AFTER OpenCC, BEFORE font generation.
python3 tools/zh_tw_locale.py \
  --source pokecrystal_cn \
  --workbook text.zh-TW.xlsx \
  --rules data/zh_tw_locale.json \
  --report zh_tw_locale_report.json
# A complete audit: every game dialogue entry and every recognized ASM string.
# Do this BEFORE font generation; newly added Han characters will be allocated
# by zh_tw_font.py after the wording and references are finalized.
python3 tools/zh_tw_complete_text_audit.py \
  --source pokecrystal_cn \
  --workbook text.zh-TW.xlsx \
  --report zh_tw_complete_text_audit_report.json \
  --strict
python3 tools/zh_tw_ui_gates.py \
  --source pokecrystal_cn \
  --report zh_tw_ui_terminology_report.json
# Verify the canonical Taiwanese battle message identities before compiling.
python3 tools/zh_tw_battle_audit.py \
  --workbook text.zh-TW.xlsx \
  --report zh_tw_battle_audit_report.json
python3 tools/zh_tw_font.py \
  --source pokecrystal_cn \
  --workbook text.zh-TW.xlsx \
  --extra-text cn_credits.diff \
  --font "$FONT_FILE" \
  --report zh_tw_font_report.json
# Check whether common Taiwan/Hong Kong names can be entered via the current
# Mandarin-Pinyin candidate tables; this is NOT a Taiwan Zhuyin/HK Cangjie IME.
python3 tools/zh_tw_naming_audit.py \
  --source pokecrystal_cn \
  --report zh_tw_naming_audit_report.json \
  --strict
# Validate the final workbook against the REMAPPED charmap before building.
python3 tools/zh_tw_prepare.py \
  --input text.zh-TW.xlsx \
  --charmap pokecrystal_cn/constants/charmap_cn.asm \
  --species data/pokemon_zh_hant_251.json \
  --report zh_tw_postfont_report.json \
  --audit-only \
  --strict

# The importer does not automatically know which sheet is the translated draft.
export PMC_TEXT_XLSX="./text.zh-TW.xlsx"
# shellcheck disable=SC1091
export PATH_EXPORTED=''
source ./env-setup
pmc_isys
pmc_init
pmc_itext
# Assert that compiled menu text (including inline-label db_w) is Traditional.
python3 tools/zh_tw_menu_audit.py --source build --report zh_tw_menu_audit_report.json
pmc_build
echo "Build completed; review all zh_tw_*_report.json and test gameplay in emulator."
