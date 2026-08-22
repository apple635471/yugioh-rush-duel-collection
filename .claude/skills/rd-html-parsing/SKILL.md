---
name: rd-html-parsing
description: Parsing Rush Duel card data from ntucgm blog post HTML. Use when modifying the parser, debugging card extraction, or handling new HTML format variations.
---

# Rush Duel 卡牌資料的 HTML 解析

每篇卡表文章分為兩個區塊:
1. **摘要索引** (文章上半部): 只有卡片編號和名稱，按稀有度分組，用於目錄瀏覽
2. **詳細區塊** (文章下半部): 完整的卡片資訊，包含名稱、類型、屬性、效果、圖片

**判斷摘要 vs 詳細**: 摘要區的卡片 ID 後面緊接下一張卡 ID；詳細區的卡片 ID 後面接的是 stats 行（含有「通常怪獸」「效果怪獸」等關鍵字，或符合緊湊格式）。

## HTML 結構隨時間演進

- **2020 (KP01 時期)**: 卡名和 stats 都在 `<b><span style="color:...">` 裡，無圖片
- **2022 (KP09 時期)**: 卡名在 `<b><span>` 裡，stats 在普通 `<div>` 裡，有 `<img>` 圖片
- **2025 (KP23 時期)**: 類似 KP09，圖片在 `<a><img>` wrapper 裡
- **緊湊格式 (部分文章)**: 某些卡片使用單行格式，stats 可跨多個相鄰 chunk（取決於作者編輯方式，非版本限定）

## 卡片 ID 格式

`RD/{SetID}-JP{Number}` (e.g. `RD/KP01-JP000`)
- 特殊卡片可能用 `JPS00` 格式 (Secret 位)
- Regex: `RD/\w+-JPS?\d{2,3}`

## Stats 行格式

### 標準格式 (KP/ST/CP 系列)
`(中文名)  卡片類型  等級  屬性  種族  攻擊力/守備力`
- 魔法/陷阱卡沒有等級、屬性、種族、ATK/DEF
- 通常怪獸沒有條件和效果文本

### 緊湊格式 (部分文章，依作者編輯習慣)
`JP名(中文名) 屬性 N星 類型縮寫[/種族縮寫] ATK DEF`
- ATK 和 DEF 以空格分隔（非 `/`）
- 類型縮寫: `儀式` → 儀式怪獸、`效果` → 效果怪獸、`融合` → 融合怪獸 等
- 若只有一個字段且不在類型表中（如 `魔法使`、`戰士`），視為種族、卡種預設為通常怪獸
- Stats 可能分散在多個相鄰 chunk；Parser 將 header + 後續 chunks 合併後再用 regex 匹配
- 多行文字塊（同一 leaf element 含 `\n`）會在解析前先按 `\n` 拆分

## 卡片文字欄位解析

Stats 行之後的文字區塊會被解析為多個欄位:

1. **stats 行和 `條件:` 之間那段** —— 依卡種分流：
   - 怪獸 → **summon_condition**（融合素材、召喚限制，如「此卡只能用…特殊召喚」）
   - 魔法˙陷阱 → **description**（如「手牌或墓地此卡卡名視為…」）
2. **condition** (發動條件): `條件:` 或 `條件：` 標籤後的文字
3. **effect** (效果): `效果:` 或 `可以發動效果:` 標籤後的文字
   - **`選擇效果:` 連標籤一起存進 effect**（`CHOICE_EFFECT_RE`）。後面的 ● 是「擇一」而不是「全部都做」，把標籤拿掉語意就變了
4. **continuous_effect** (永續效果): `永續效果:` 標籤後的文字，與一般 `效果:` 分開儲存

文章段落結尾的分隔線（`------` 之類）由 `_SEPARATOR_RE` 濾掉，不會被當成內容。

### 同行多標籤問題

有些文章中 `條件:…效果:…` 連在同一個 HTML element 裡。Parser 使用 `_LABEL_SPLIT_RE` 拆分:
```python
_LABEL_SPLIT_RE = re.compile(
    r"(?=(?:條件|永續效果|選擇效果|(?<!永續)(?<!選擇)效果)[:：])"
)
```
- 使用 lookahead 在標籤前切割
- 兩個 negative lookbehind 避免 `永續效果:` / `選擇效果:` 被拆斷成 `永續`＋`效果:`

### 詳細條目的判定

同一個卡號在文章裡通常出現兩次（上方索引 + 下方詳細）。`_is_detail_entry()` 的判準是
**在遇到下一個卡號之前有沒有出現 stats 行**——索引區的下一個 chunk 一定是另一個卡號，
詳細區則會先遇到 stats。

前瞻視窗要夠寬：稀有度標記常被 inline 標籤切碎，例如 `(SR` / `/SER` / `)卡名` 佔掉三個
chunk，stats 行排在第四個之後。視窗太窄會讓整張卡被當成索引條目而漏掉。

## 種族正規化

部落格對同一個種族有多種寫法，`monster_types.py` 的 `normalize_monster_type()` 在解析時
收斂（backend 匯入時會再做一次，舊 JSON 不必重爬就自癒）：

| 來源寫法 | 正規名 |
|---------|--------|
| 歐米茄超能族 / 奧米茄超能族 / 奧米加超能族 | `omega 超能族` |
| 炎 | 炎族 |
| 爬蟲族 | 爬蟲類族 |
| 魔法族 | 魔法使族 |

## 改了 parser 之後

`scrape-url` / `update` 是比對文章 content hash，**頁面沒變就不會重新解析**。改完 parser
要讓既有資料套用新規則，得用 `uv run python -m rd_card_scraper.cli update --force`
（重爬全部）。

## 稀有度標記

在卡片 ID 後的括號中，如 `(UR)`, `(SR/SER)`, `(ORRPBV)`
- 常見稀有度: N, R, SR, UR, RR, SER, ORR, ORRPBV

## 色碼對應 (span color)

- `#bf9000` (金) = 通常怪獸
- `#e69138` (橙) = 效果怪獸
- `#741b47` (紫) = 融合/儀式怪獸
- `#38761d` (綠) = 魔法卡
- `#cc0000` (紅) = 陷阱卡

## 一篇文章多個卡組

**卡號決定 set，沒有白名單。** 卡號格式是 `RD/{set_id}-{編號}`，`parse_post_multi()`
一律依卡號裡的 set id 分組，一組產生一個 `CardSet`：

- 一般文章只有一種卡號 → 一個 CardSet（跟以前一樣）
- 整年份活動包、結構卡組合輯 → 依卡號拆成多個（B261/S261/B262/S262/26S1…）
- 戰鬥包文章裡夾帶的特典卡（`RD/S23P-*`）→ 自己成一個 set，不會被歸到那期戰鬥包

同一篇拆出來的 set 共用文章的名稱、發行日、post_url；`total_cards` 各算各的。

> 以前這件事是靠 `MULTI_DECK_URLS` 白名單控制的（已移除）。白名單的問題是只擋得住
> 已知的文章，新的一篇又要再加一次；而且它只處理「整篇有多個卡包」，處理不了
> 「一張特典卡混在單一卡包文章裡」。

**既有 DB 的補救**：重新匯入**不會**把舊卡搬家（`_import_one_card` 刻意不改既有卡的
`set_id`）。用 checklist backend 掃一遍：

```bash
uv run python -m rd_checklist.cli resplit-set --all --dry-run   # 先看會搬什麼
uv run python -m rd_checklist.cli resplit-set --all             # 實際搬
```

依卡號搬過去，缺的 set 會自動建立（沿用來源 set 的名稱／日期／post_url），
override / 編輯紀錄 / 上傳圖 / 持有數都跟著卡片走。

**例外一：某個卡號永遠不該獨立成 set** —— 寫在 `set_service.SET_ID_HOMES`：

```python
SET_ID_HOMES = {"21CC": "PROMO"}   # 卡號 → 它該待的 set
```

這是**針對卡號的規則**，之後匯入進來的同卡號卡片也一樣：`resplit-set` 不會幫它建
set，而是把卡放進指定的 set（該 set 不存在時就原地不動）。

**例外二：只針對某一張卡的一次性決定**：

```bash
uv run python -m rd_checklist.cli merge-set 21CC --into PROMO
```

卡片搬進目標 set，並在 `card_overrides` 寫一筆 `set_id` 記號**釘住**——之後
`resplit-set` 掃到會跳過，重新匯入也不會動（`_import_one_card` 本來就不改既有卡的
set_id）。搬空的來源 set 會刪掉（手動建立的除外）。
