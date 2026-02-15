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

## 卡片文字欄位解析

Stats 行之後的文字區塊會被解析為多個欄位:

1. **summon_condition** (召喚條件): 位於 stats 行和 `條件:` 標籤之間的描述文字 (如「此卡只能用…特殊召喚」)
2. **condition** (發動條件): `條件:` 或 `條件：` 標籤後的文字
3. **effect** (效果): `效果:` 或 `可以發動效果:` 標籤後的文字
4. **continuous_effect** (永續效果): `永續效果:` 標籤後的文字，與一般 `效果:` 分開儲存

### 同行多標籤問題

有些文章中 `條件:…效果:…` 連在同一個 HTML element 裡。Parser 使用 `_LABEL_SPLIT_RE` 拆分:
```python
_LABEL_SPLIT_RE = re.compile(r"(?=(?:條件|永續效果|(?<!永續)效果)[:：])")
```
- 使用 lookahead 在標籤前切割
- `(?<!永續)` negative lookbehind 避免 `永續效果:` 被拆斷為 `永續` + `效果:`

## 稀有度標記

在卡片 ID 後的括號中，如 `(UR)`, `(SR/SER)`, `(ORRPBV)`
- 常見稀有度: N, R, SR, UR, RR, SER, ORR, ORRPBV

## 色碼對應 (span color)

- `#bf9000` (金) = 通常怪獸
- `#e69138` (橙) = 效果怪獸
- `#741b47` (紫) = 融合/儀式怪獸
- `#38761d` (綠) = 魔法卡
- `#cc0000` (紅) = 陷阱卡
