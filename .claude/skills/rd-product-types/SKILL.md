---
name: rd-product-types
description: Identifying Rush Duel product types from set IDs. The rules live in the database and are edited in the UI. Use when classifying card sets, filtering by product line, adding a product type, or touching anything that reads a set's product_type.
---

# Rush Duel 產品類型辨識

**規則存在資料庫裡，不在程式碼裡。**

- `product_types`：一個產品線一列（代號、英文名、中文名、側邊欄分組、時間軸顏色、順序、是否 fallback）
- `product_type_rules`：一列一條正規表示式，屬於某個產品線

卡組**不存自己的分類**——`card_sets` 沒有 `product_type` 欄位。它是算出來的：
`services/product_type_service.classify_set(set_id)`。所以改一條規則就等於把所有
卡組重新分類一次，沒有東西需要遷移、不用重新匯入。

## 誰在讀這份規則

| 來源 | 怎麼讀 |
|------|--------|
| Backend | `classify_set()`，規則編譯後放在 module-level 快取，任何寫入後 `invalidate()` |
| `CardSetModel.product_type` | Python property（不是欄位），所以 response schema 照舊 |
| Frontend | `GET /api/product-types` → `cardSets` store；側邊欄分組、時間軸配色、顯示名稱都從這來 |
| Scraper | 同一個端點（`rd_card_scraper/product_types.py`），抓到的結果快取在 `data/product_types.json`，後端沒開就用快取 |

## 比對語意

`re.search(pattern, set_id, re.IGNORECASE)`：

- 沒加 `^` `$` 就是「包含」——`JMP` 抓得到 SJMP / VJMP / WJMP
- 加了就是固定形狀——`^\d{2}PR$` 只抓 23PR、24PR…
- 順序：產品線的 `sort_order`，再看規則的 `sort_order`，**第一個命中的勝出**
- 都沒命中 → fallback 那一列（預設 `other`，沒有規則、不能刪）

## 預設規則（`DEFAULT_PRODUCT_TYPES`）

只在表是空的時候種進去（新環境或初次遷移），之後使用者怎麼改都不會被蓋回來。

| 產品線 | 規則 |
|--------|------|
| `booster` 補充包 | `^KP\d` |
| `advanced_pack` 上級包 | `^AP\d` |
| `maximum_pack` 巨極包 | `^MAX\d` |
| `over_rush_pack` 超越超速包 | `^ORP\d` |
| `legend_pack` 傳說包 | `^LGP\d` |
| `triple_build_pack` 三重構築包 | `^TB\d` |
| `structure_deck` 預組 | `^SBD` `^SD` `^ST\d` `^GRD` |
| `battle_pack` 戰鬥包 | `^B0\d` `^B2\d` `^S2` |
| `promo` | `^711` `^\d{2}PR$` `JMP` `^P\d` `^G\d` `^PROMO` `^ECG\d` |
| `other` | （fallback，沒有規則）|

`^S2` 的來由：戰鬥包成對發行、共用編號（B251/S251），S 半是獨立的 set
（見 `rd-html-parsing`：卡號不同就是不同 set）。

## 要改分類時

**改 UI，不要改程式**：首頁左側分類清單最下面的「編輯分類規則」。可以改代號、
中英文名、分組、顏色、規則，可以新增／刪除分類、調整順序，存檔前可以「試算」
看某組規則會抓到哪些卡組、其中哪些已經被排在前面的分類認領走。

代號改名不用遷移任何資料（卡組沒有存分類），只有 `/sets/<code>` 這個網址會變。

API（`routers/product_types.py`）：

```
GET    /api/product-types            # 清單 + 規則 + 各自的卡組數
POST   /api/product-types            # 新增
PATCH  /api/product-types/{code}     # 改欄位／改代號／整組換掉 rules
DELETE /api/product-types/{code}     # 刪除（fallback 不能刪）
PUT    /api/product-types/order      # 重新排序（也就是規則的比對順序）
POST   /api/product-types/preview    # 試算：這些 pattern 會抓到哪些卡組
```

寫入端點都回傳**整份最新清單**，因為改一條規則會改到所有分類的卡組數。

## 遷移

```bash
cd apps/rd-checklist/backend
uv run python -m rd_checklist.cli migrate-product-types   # idempotent
```

種預設規則 → 報告有哪些卡組的分類因此改變 → 丟掉 `card_sets.product_type` 欄位
與殘留的 `product_type` override。`init-db` 與後端啟動時也會做同樣的事（表空了才種）。

2026-09 從寫死的前綴表搬過來時：117 個卡組**分類完全不變**。
