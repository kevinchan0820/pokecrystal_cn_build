# Pokémon Crystal — 繁體中文版（台灣用語）Release Candidate

> 狀態：**已成功編譯同產生 IPS 補丁，並通過自動化開機測試；尚未完成全遊戲人工驗收。**
>
> 包含：原始碼、繁體主文本、251 隻寶可夢正式名稱對照、251 招式名稱對照、道具名稱 crosswalk、動態字型重建、測試報告、IPS Patch。

## 下載與使用（Mac / Windows / Linux）

1. 打開 [GitHub Actions](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/workflows/zh-hant-ci.yml)，選最新 **Success** 的 `work/zh-hant-tw` Run。
2. 下載 `zh-hant-translated-text-and-build-reports` ZIP。解壓後有：
   - `Crystal_Traditional_Chinese_v1.1.ips` — 繁體中文補丁
   - `zh_tw_patch_manifest.json` — Patch SHA256、編譯產物 SHA256
   - `text.zh-TW.xlsx` — 可自行編輯嘅繁體腳本
   - `zh_tw_*_report.json` — Font、匯入、開機測試報告
   - `zh_tw_*.png` — 自動截圖
3. 使用你**合法持有及自行備份**的英文《Pokémon Crystal US v1.1》ROM。
4. 將 [`tools/apply_zh_tw_ips.py`](tools/apply_zh_tw_ips.py)、IPS、Manifest 放到同一資料夾，在 Terminal 執行：

```sh
python3 apply_zh_tw_ips.py "你的英文水晶v1.1.gbc" Crystal_Traditional_Chinese_v1.1.ips
```

5. 程式會先檢查原版 SHA1，亦會比對補丁同輸出 ROM 嘅 SHA256；成功後本地產生 `Pokemon_Crystal_zh_TW.gbc`。你可以喺支援 GBC 嘅模擬器開啟。

**原版 ROM 檢查值（SHA1）：**
`f2f52230b536214ef7c9924f483392993e226cfb`

唔符合呢個版本嘅 ROM，程式會拒絕套用，避免錯誤寫入。

## 再編譯

喺 Linux／GitHub Actions 環境可以用 `tools/build_zh_tw.sh`。它會透過 `openpyxl`、OpenCC、Noto Sans CJK TC 字型、RGBDS 0.7 同原有漢化引擎重建遊戲；完整流程見 [`ZH_TW_WORKFLOW.md`](ZH_TW_WORKFLOW.md)。

## 驗收邊界

- **已驗證：** 文字產生、原字型映射覆蓋率、GBC ROM 編譯、PyBoy 開機及渲染、IPS Patch 套用後逐 byte 匹配。
- **未完成：** 遊戲全部關卡、所有 NPC 分支、Trainer/道具/招式逐項人工校對、每個畫面嘅 Overflow 檢查、存檔與交換通訊完整回歸測試。
- **翻譯取捨：** 原中文劇本文本由 SnDream 工程提供（社群漢化）；OpenCC 負責一般簡繁轉換；寶可夢、招式、道具用 PokeAPI zh-Hant crosswalk 作資料依據，再以 [台灣寶可夢官方圖鑑](https://tw.portal-pokemon.com/pokedex/)核對重要專有名詞。PokeAPI 屬社群資料，不能視為全部已經逐項由官方核實。
- **字型授權：** Noto Sans CJK 由 Google / Adobe 等貢獻者按 SIL Open Font License 1.1 發行：<https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE>。工程只保留 12x12 點陣字形輸出及生成程式，不分發原字型檔案。
- **遊戲權利：** 遊戲、名稱及既有資產屬相關權利人。此工程唔會將完整商業遊戲 ROM 放到公開 GitHub，交付係補丁及可重現編譯原始碼。

## 來源與 QA

- [來源權威等級及 Phase Acceptance Gates](ZH_TW_SOURCE_AND_QA.md)
- [翻譯及字型重建流程](ZH_TW_WORKFLOW.md)
- [源碼 Fork](https://github.com/kevinchan0820/pokecrystal_cn/tree/work/zh-hant-tw)
- [Draft Pull Request](https://github.com/kevinchan0820/pokecrystal_cn_build/pull/1)
