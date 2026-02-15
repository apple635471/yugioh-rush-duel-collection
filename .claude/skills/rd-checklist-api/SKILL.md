---
name: rd-checklist-api
description: API endpoints and data flow for rd-checklist backend. Use when adding/modifying endpoints, debugging API requests or responses, understanding request/response schemas, or tracing backend data flow.
---

# Checklist App API 端點與資料流

**何時讀此 SKILL**：加/改 API endpoint、debug 後端請求、改 response schema、理解前後端資料流。

Backend: FastAPI on port 8000, CORS 允許 localhost:5173。

## 端點一覽

### 卡組 `/api/card-sets`
- `GET /product-types` → `ProductTypeOut[]` — 產品類型 + display_name + set_count
- `GET /?product_type=booster` → `CardSetOut[]` — 卡組列表 (order by release_date DESC)
- `GET /{set_id}` → `CardSetWithCardsOut` — 含所有 cards + variants (eager loaded)

### 卡片 `/api/cards`
- `GET /{card_id:path}` → `CardOut` — 單卡 (card_id 含斜線，用 path converter)
- `PATCH /{card_id:path}` body: `CardUpdate` → `CardOut` — 編輯，自動記錄 card_edits

### 持有數 `/api/ownership`
- `PATCH /{card_id:path}/{rarity}` body: `{owned_count: int}` → `CardVariantOut`
- `PATCH /batch` body: `{updates: [{card_id, rarity, owned_count}]}` → `CardVariantOut[]`
- `GET /stats` → `OwnershipStatsOut` — 全局統計
- `GET /stats/{set_id}` → `OwnershipStatsOut` — 單組統計

### 搜尋 `/api/search`
- `GET /?q=青眼&card_type=通常怪獸&attribute=光&level=8&rarity=UR&owned=missing&limit=200&offset=0`
- `q` 搜尋: ILIKE on name_jp, name_zh, card_id
- `card_type` 篩選: 使用 `ILIKE %value%` 部分比對，搜尋「儀式」可同時匹配 `儀式怪獸` 和 `儀式/效果怪獸`
- `owned`: "owned" = owned_count > 0, "missing" = NOT IN (owned > 0)

### 圖片 `/api/images`
- `GET /card/{card_id:path}/{rarity}` → FileResponse
  - 優先順序: user_upload > scraper > 404
  - user_upload 回傳 `Cache-Control: no-cache` 避免快取
- `POST /card/{card_id:path}/{rarity}/upload` body: multipart file → `CardVariantOut`
  - 上傳替換圖，存於 `data/images/user_uploads/`，更新 `image_source`/`image_path`，保留 `scraper_image_path`
- `DELETE /card/{card_id:path}/{rarity}/upload` → `CardVariantOut`
  - 刪除 user upload，從 `scraper_image_path` 恢復原始圖
- `GET /{set_id}/{filename}` → 直接讀 scraper data 目錄

## 資料流

```
Frontend → axios GET /api/card-sets/KP01
  → Backend query CardSetModel + eager CardModel + CardVariantModel
  → JSON: { set_id, set_name_zh, cards: [{ card_id, variants: [...] }] }

Frontend → PATCH /api/ownership/RD/KP01-JP000/UR  { owned_count: 1 }
  → Backend: variant.owned_count = max(0, 1), commit
  → JSON: { id, card_id, rarity, owned_count: 1 }
```

## 注意事項

- card_id 含有斜線 (`RD/KP01-JP000`)，路由需用 `{card_id:path}`
- PRODUCT_TYPE_LABELS dict 在 card_sets.py 中定義中文顯示名
- 搜尋的 owned filter 需要 subquery join card_variants
