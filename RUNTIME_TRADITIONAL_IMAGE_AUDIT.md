# 1.x 繁體化 — 遊戲可見圖像資源驗收

範圍：僅限 `feature/zh-hant-tw-hk-1x`；1.0 原味分支不變。
原則：文字／圖片／字型都要驗收；未經 PyBoy 真實畫面檢查，不准說「全遊戲繁體化完成」。

| 來源 | 遊戲顯示部位 | 已驗證範圍 | 待驗收 |
| --- | --- | --- | --- |
| `gfx/title/logo.png` | 開頭遊戲標誌 | 現有 title 資產檢查 | 長時間開機切換與實體/Delta 屏幕 |
| `gfx/naming_screen/selection_chinese.png` | 命名底部按鈕 | `符號／刪除` 台灣字形像素及 PyBoy | 所有命名模式 |
| `gfx/naming_screen/mode_labels_zh_hant.png` | `拼音／英文／臺灣／香港／速成` | 8px 像素、PyBoy 命名畫面 | 多模式長時間切換 |
| `gfx/naming_screen/cangjie_roots.png` | 速成 A-Z 原鍵位 → 日月金木等 | 26 個字根；PyBoy Real quick type AA/AB/VD | 密集 8px 字根人眼易讀度，完整倉頡 |
| `gfx/pack/pack_menu.png` + `.tilemap` | 背包欄目 | 重組圖塊證明已為 `精靈球` | **PyBoy 真背包畫面** |
| `gfx/trainer_card/card_status.png` | 訓練家卡狀態標題 | **本次修改**：原 `当前状态` → 台灣 `目前狀態`；12x8 四字核准像素 Red/Green | **PyBoy 真訓練家卡畫面** |
| `gfx/new_game/name_chinese.png` | 新遊戲命名相關預載圖 | 已讀取源 PNG（40x8），內容尚待結合引用現場辨認 | 確認引用與可見文字繁體 |
| `gfx/font/font_battle_extra.png` | 戰鬥 UI HP / icon | 已檢視來源圖形，以拉丁圖元和框線為主 | PyBoy 戰鬥 HUD |
| 戰鬥來源 `text.zh-TW.xlsx` | `敵人的／灼傷／效果絕佳` | `zh_tw_battle_audit.py` 5 條 Canonical、font glyph `敵人灼傷` | **實際灼傷戰鬥，對照用家舊 Delta 圖片；來源 ROM 版本未能確認** |

## 已驗證的舊圖 Bug（這輪）

- 訓練家卡的 `gfx/trainer_card/card_status.png` 被引擎 `engine/menus/trainer_card.asm` 引用（`CardStatusGFX INCBIN`），不是文字 importer 產物。
- 舊源顯示 `当前状态`，非台港繁體用語；核准改作 `目前狀態`，仍是 48x8 的原本尺寸。
- Red：舊 PNG 與四個核准 glyph 像素比對均 Fail；Green：新 PNG 均 Pass。
- 一開始 CI 在 Noto 字型 raster 逐機重建時因 runner 字型版本不同而誤判 Fail，已改成**固定核准解碼像素 SHA256**，阻止不同 font/Pillow 版本造成假陰性；未經人工核准不更新 SHA。
- 最終 CI 須等最新 Run 及真遊戲 Screenshot 才可作整體聲稱。

## 後續優先順序

1. 實際 PyBoy 走入訓練家卡／背包，直接截圖比對中文字，不再只比來源 PNG。
2. 追蹤 `name_chinese.png` 係咪已被 Game Boy 原程式引用，解讀 8px 特製字形。
3. 製作可重播的實際戰鬥狀態測試：`敵人`、`灼傷`；與用家截圖比較。若 ROM 版本不同，需要記錄並向下相容。
4. 完整速成多候選字／字庫、倉頡、注音、儲存讀檔；目前只係可操作原型。

不許因某次成功 CI 就將整張表標成「全部通過」。跨版本必須核對 source SHA、build SHA 同實際 PyBoy 畫面。
