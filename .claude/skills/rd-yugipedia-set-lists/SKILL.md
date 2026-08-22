---
name: rd-yugipedia-set-lists
description: Reading a set's card list from yugipedia (wikitext format, rarity mapping, alternate artwork, Japanese names). Use when working on the set list comparison feature or debugging its parsing.
---

# yugipedia 卡表解析

用途：拿 yugipedia 的官方卡表跟資料庫比對，找出少列／多列的印刷。
程式在 `apps/rd-checklist/backend/rd_checklist/services/yugipedia.py`。

## 為什麼讀 wikitext 而不是 HTML

MediaWiki API 可以直接拿原始碼，一張卡一行，比渲染後的表格穩定得多：

```
https://yugipedia.com/api.php?action=parse&page=<頁面>&prop=wikitext&format=json
```

## 頁面結構

使用者給的是**卡組主頁**（如 `High-Grade_Collection`），卡表在子頁：

```
Set Card Lists:<卡組名> (OCG-JP)      ← 目前所有 Rush Duel 卡組都是這個後綴
Set Card Lists:<卡組名> (Rush Duel-JP)  ← 備用
Set Card Lists:<卡組名> (JP)            ← 備用
```

主頁的 wikitext 沒有卡表，只有 `{{Set list tabs}}`，所以是直接試上面三個後綴。

## `{{Set list}}` 區塊

```
{{Set list|region=JP|rarities=C|print=New|
RD/KP20-JP001; Insect Knight (Rush Duel); R
RD/KP20-JP002; Silver Red Pulsar
RD/KP20-JP007; Variable Stellarizer; SR, ScR
RD/KP20-JP007; Variable Stellarizer; ScR // description :: (alternate artwork)
}}
```

欄位：`卡號; 英文卡名; 貴罕度(逗號分隔); 備註`

**三個容易踩的坑**：

1. **省略貴罕度的行要吃表頭的 `rarities=` 預設**。上例 JP002 沒寫貴罕度，它是 `C`（Common）。多數行都是這樣，漏掉這條會以為整包只有幾張卡。
2. **貴罕度有縮寫也有全名**，同一個 wiki 不同頁面寫法不同（`ScR` vs `Secret Rare`）。對照表兩種都收。
3. **異圖是同卡號多一行**，通常標 `// description :: (alternate artwork)`。判定用「同卡號的第二行以後就是異圖」，標記當佐證——HC01-JP049 那行只寫 `New artwork` 沒有標記。

## 貴罕度對照

| yugipedia | 我們 | | yugipedia | 我們 |
|---|---|---|---|---|
| `C` / Common | N | | `ORR` / Over Rush Rare | ORR |
| `R` / Rare | R | | `FORR` / Full Over Rush Rare | FORR |
| `SR` / Super Rare | SR | | `ORRBlack` | ORRPBV |
| `UR` / Ultra Rare | UR | | `RR` / Rush Rare | RR |
| `ScR` / Secret Rare | SER | | `GRR` / Gold Rush Rare | GRR |
| `NPR` / Normal Parallel Rare | NPR | | `SPR` / Super Parallel Rare | SPR |
| `UPR` / Ultra Parallel Rare | UPR | | `RUR` | RUR |

對不到的字串會收集到 `unknown_rarities` 回傳給前端顯示，**不會安靜地丟掉**——被丟掉的印刷在比對結果裡看起來就像「資料庫多列」，很難察覺。

## 日文名

卡表只有英文名，建立卡片時要日文名，所以再查一次卡片頁的 `| ja_name =`（一次 50 頁）。三個要處理的狀況：

- **furigana**：`{{Ruby|連|れん}}{{Ruby|撃|げき}}竜ドラギアス` → 取第一個參數 → `連撃竜ドラギアス`
- **`(Rush Duel)` 後綴的頁面常常沒有 `ja_name`**（與本傳同名），去掉括號後綴再查一次本傳頁面
- **`[L]` / `[R]`**（Maximum 怪獸的左右半）共用一個頁面，查本頁再把後綴接回去 → `超銀河王ロード・オブ・ギャラクティカ[L]`，與資料庫的寫法一致

yugipedia 跑的是舊版 MediaWiki：`rvslots` 參數不支援，內容直接在 `revisions[0].content`。

## 比對與套用

- `POST /api/card-sets/{set_id}/compare` — 唯讀，回傳 missing / extra
- `POST /api/card-sets/{set_id}/compare/apply` — 套用勾選的項目

比對單位是 **(卡號, 貴罕度, 是否異圖)**，因為收藏要收的就是這個。建立時只填卡號、日文名、貴罕度（`is_manual=True`），其餘欄位留給爬蟲或使用者。刪除時若那是該卡最後一個 variant，連卡片一起刪——沒有任何 variant 的卡在 UI 上顯示不出來。

## 驗證過的案例

| 卡組 | 結果 |
|------|------|
| HC01 (High-Grade Collection) | 154 種印刷，與資料庫完全一致；日文名 154/154；異圖 JP049 對上 |
| KP20 (Galactica of Eternity) | 106 種，完全一致；5 個異圖都對上 |
| GRP1 (Gold Rush Pack) | 卡表 62 / 資料庫 42，抓出 20 種缺漏（14 個 GRR）|
