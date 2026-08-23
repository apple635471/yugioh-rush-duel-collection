---
name: rd-product-types
description: Identifying Rush Duel product types from set ID prefixes. Use when classifying card sets, filtering by product line, or adding support for new product types.
---

# Rush Duel 產品類型辨識

**單一事實來源**：`apps/rd-checklist/backend/rd_checklist/product_types.py`
（scraper 的 `parser.py` 有一份鏡像 `PRODUCT_TYPE_MAP` / `guess_product_type`，
兩邊要一起改；匯入時 backend 會重新推導，所以 backend 那份才是最終決定者。）

**前端還有第三份鏡像**：`frontend/src/constants/productTypes.ts` 的 `PRODUCT_TYPES`
（顯示用的標籤與時間軸配色）。改動類型清單時三份一起改。
側邊欄的標籤是 API 給的（`/product-types` 用 `PRODUCT_TYPE_LABELS`）。

## 分類是唯讀的，只看規則

**set_id 決定一切**：沒有手動編輯（UI 只顯示 `Product Type: Other (由 set_id 決定)`）、
沒有 override（`_OVERRIDABLE_FIELDS` 不含 `product_type`，`CardSetUpdate` / `CardSetCreate`
也不收）、匯入不看 scraper 的猜測（它用的是同一套規則）。要調整某個卡組的分類，
就是**改這裡的規則**，然後跑 `reclassify-product-types`。

這是 2026-08 定下的：三份鏡像加上「編輯任何欄位都會寫 override」，讓分類飄成四種說法
（DB 值、override 值、scraper 值、下拉選項），前端顯示與側邊欄對不起來。現在只有一個來源。

## set_id → 產品類型

| 前綴 | 類型 | 側邊欄分組 | 顯示名稱 |
|------|------|-----------|---------|
| `KP` | `booster` | 補充包系列 | Booster Pack / 補充包 |
| `AP` | `advanced_pack` | 補充包系列 | Advanced Pack / 上級包 |
| `MAX` | `maximum_pack` | 補充包系列 | Maximum Pack / 巨極包 |
| `ORP` | `over_rush_pack` | 補充包系列 | Over Rush Pack / 超越超速包 |
| `LGP` | `legend_pack` | 補充包系列 | Legend Pack / 傳說包 |
| `TB` | `triple_build_pack` | 補充包系列 | Triple Build Pack / 三重構築包 |
| `SBD` `SD` `ST` `GRD` | `structure_deck` | 預組 | Structure Deck / 預組 |
| `B0` `B2` `S2` | `battle_pack` | 其他 | Battle Pack / 戰鬥包 |
| `711` `ECG` `SJMP` `VJMP` `WJMP` `PROMO` `P0` `G0` | `promo` | 其他 | Promo |
| `\d{2}PR`（23PR、24PR…，regex 非前綴） | `promo` | 其他 | Promo |
| 以上皆非 | `other` | 其他 | Other |

比對時**長前綴優先**（`SBD` 先於 `SD`、`SJMP` 先於 `S2`）。

### 為什麼有些產品線沒有自己的類型

`CP`（角色包）、`GRC`（Go Rush 角色包）、`EXT`（Extra 包）、`VSP`（VS 包）
各自只有一兩個 set，給它們獨立的側邊欄項目只是讓導覽變長。這些前綴**刻意不列在
map 裡**，會落到 `other`。要恢復就是把前綴加回 map + 在 `PRODUCT_TYPE_LABELS`
補標籤 + 在前端 `ProductTypeSidebar` 的 `SECTIONS` 決定要放哪一組。

### `S2` → battle_pack 的來由

戰鬥包成對發行、共用一個編號（B251/S251），S 半是**獨立的 set**（見
`rd-html-parsing`：卡號不同就是不同 set），所以 `S251`、`S23P` 這些也要歸到
`battle_pack`——`S2` 前綴就是為此。

## 已退役的類型

已經不需要對應表了——分類只看 set_id，舊值不會有機會被讀進來。這張表留著當紀錄：

| 舊值 | 現值 | 說明 |
|------|------|------|
| `unknown` | `other` | 舊的 fallback |
| `character_pack` | `other` | CP01 一個 set 不值得獨立分類 |
| `go_rush_character` | `other` | 同上 |
| `extra_pack` | `other` | 同上 |
| `vs_pack` | `other` | 同上 |
| `tournament_pack` | `triple_build_pack` | 原本就是誤譯（大會包 → 三重構築包）|

## 判定順序

`canonical_product_type(set_id)`：set_id 有規則就用規則，沒有就 `other`。就這樣。

## 既有資料遷移

```bash
cd apps/rd-checklist/backend
uv run python -m rd_checklist.cli reclassify-product-types   # idempotent
```

會**刪掉**所有 `product_type` override——現在沒有任何路徑會產生它們，留著只會讓
下次讀 override 表的人困惑。
