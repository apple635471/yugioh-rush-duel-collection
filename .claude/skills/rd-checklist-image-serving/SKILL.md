---
name: rd-checklist-image-serving
description: Image serving strategy for the rd-checklist app. Use when modifying image endpoints, adding upload support, or debugging image loading issues.
---

# Checklist App 圖片服務策略

## 設計原則

**圖片不複製** — Backend 直接從 scraper data 目錄讀取，不複製到自己的 data/ 下。這避免了重複儲存 2500+ 張圖片。

## 圖片來源優先順序

`GET /api/images/card/{card_id}/{rarity}`:

1. 查 DB `card_variants.image_source`
2. 如果 `"user_upload"` → 讀取 `data/images/user_uploads/{safe_filename}.jpg`
3. 如果 `"scraper"` 或 null → 讀取 `SCRAPER_DATA_DIR/{image_path}`
4. 都找不到 → 404

## 路徑解析

```
SCRAPER_DATA_DIR (預設: tools/rd-card-scraper/data/)
  └── KP01/images/RD_KP01-JP000.jpg

DB card_variants.image_path = "KP01/images/RD_KP01-JP000.jpg"
完整路徑 = SCRAPER_DATA_DIR / image_path
```

## User Upload (替換卡圖)

```
POST /api/images/card/{card_id}/{rarity}/upload  (multipart/form-data)
  → 存到 data/images/user_uploads/RD_KP01-JP000_UR.jpg
  → 更新 DB: image_source = "user_upload", image_path = ...

DELETE /api/images/card/{card_id}/{rarity}/upload
  → 刪除 user upload 檔案
  → 恢復 DB: image_source = "scraper"
```

## 前端使用

```typescript
// api/cards.ts
function getCardImageUrl(cardId: string, rarity: string): string {
  return `/api/images/card/${cardId}/${rarity}`
}

// CardGridItem.vue
<img :src="imageUrl" loading="lazy" />
```

## 環境變數

`SCRAPER_DATA_DIR` 可覆蓋 scraper data 目錄路徑：
```python
SCRAPER_DATA_DIR = Path(os.environ.get("SCRAPER_DATA_DIR",
    str(BACKEND_DIR.parent.parent.parent / "tools" / "rd-card-scraper" / "data")))
```

預設路徑假設 monorepo 結構: `apps/rd-checklist/backend/` → `../../../tools/rd-card-scraper/data/`
