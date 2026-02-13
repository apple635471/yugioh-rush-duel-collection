---
name: rd-html-parsing
description: Parsing Rush Duel card data from ntucgm blog post HTML. Use when modifying the parser, debugging card extraction, or handling new HTML format variations.
---

# Rush Duel 卡牌資料的 HTML 解析

每篇卡表文章分為兩個區塊:
1. **摘要索引** (文章上半部): 只有卡片編號和名稱，按稀有度分組，用於目錄瀏覽
2. **詳細區塊** (文章下半部): 完整的卡片資訊，包含名稱、類型、屬性、效果、圖片

**判斷摘要 vs 詳細**: 摘要區的卡片 ID 後面緊接下一張卡 ID；詳細區的卡片 ID 後面接的是 stats 行（含有「通常怪獸」「效果怪獸」等關鍵字）。

## HTML 結構隨時間演進

- **2020 (KP01 時期)**: 卡名和 stats 都在 `<b><span style="color:...">` 裡，無圖片
- **2022 (KP09 時期)**: 卡名在 `<b><span>` 裡，stats 在普通 `<div>` 裡，有 `<img>` 圖片
- **2025 (KP23 時期)**: 類似 KP09，圖片在 `<a><img>` wrapper 裡

## 卡片 ID 格式

`RD/{SetID}-JP{Number}` (e.g. `RD/KP01-JP000`)
- 特殊卡片可能用 `JPS00` 格式 (Secret 位)
- Regex: `RD/\w+-JPS?\d{2,3}`

## Stats 行格式

`(中文名)  卡片類型  等級  屬性  種族  攻擊力/守備力`
- 魔法/陷阱卡沒有等級、屬性、種族、ATK/DEF
- 通常怪獸沒有條件和效果文本

## 稀有度標記

在卡片 ID 後的括號中，如 `(UR)`, `(SR/SER)`, `(ORRPBV)`
- 常見稀有度: N, R, SR, UR, RR, SER, ORR, ORRPBV

## 色碼對應 (span color)

- `#bf9000` (金) = 通常怪獸
- `#e69138` (橙) = 效果怪獸
- `#741b47` (紫) = 融合/儀式怪獸
- `#38761d` (綠) = 魔法卡
- `#cc0000` (紅) = 陷阱卡
