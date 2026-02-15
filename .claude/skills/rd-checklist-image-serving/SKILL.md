---
name: rd-checklist-image-serving
description: Image serving and upload for rd-checklist. Use when modifying image endpoints, adding upload/revert features, debugging 404 or cache issues, or understanding scraper vs user_upload path resolution.
---

# Checklist App 圖片服務策略

**何時讀此 SKILL**：卡圖不顯示/404、上傳或還原邏輯、改圖片路徑、快取問題。

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
DB card_variants.scraper_image_path = "KP01/images/RD_KP01-JP000.jpg"  # 原始 scraper 路徑，永不覆蓋
完整路徑 = SCRAPER_DATA_DIR / image_path
```

## User Upload (替換卡圖)

```
POST /api/images/card/{card_id}/{rarity}/upload  (multipart/form-data)
  → 存到 data/images/user_uploads/RD_KP01-JP000_UR.jpg
  → 更新 DB: image_source = "user_upload", image_path = user_upload 路徑
  → 若 scraper_image_path 為空，從 image_path 複製保存 (backfill)

DELETE /api/images/card/{card_id}/{rarity}/upload
  → 刪除 user upload 檔案
  → 從 scraper_image_path 恢復 DB: image_source = "scraper", image_path = scraper_image_path
  → scraper_image_path 在匯入與首次上傳時設定，確保還原永遠可用
```

## 快取與 Cache Buster

- **User upload 回應**: `Cache-Control: no-cache, no-store, must-revalidate` 避免瀏覽器快取舊圖
- **前端**: user_upload 圖 URL 加 `?t=1` 或 `?t=${Date.now()}` 作為 cache buster，上傳/還原後強制重載

## 前端使用

```typescript
// api/cards.ts
function getCardImageUrl(cardId: string, rarity: string): string {
  return `/api/images/card/${cardId}/${rarity}`
}
uploadCardImage(cardId, rarity, file)   // POST upload
revertCardImage(cardId, rarity)         // DELETE revert

// CardGridItem.vue / CardDetailPanel.vue
// user_upload 時: base + "?t=1" 或 "?t=" + cacheBuster
<img :src="imageUrl" loading="lazy" />
```

## 環境變數

`SCRAPER_DATA_DIR` 可覆蓋 scraper data 目錄路徑：
```python
SCRAPER_DATA_DIR = Path(os.environ.get("SCRAPER_DATA_DIR",
    str(BACKEND_DIR.parent.parent.parent / "tools" / "rd-card-scraper" / "data")))
```

預設路徑假設 monorepo 結構: `apps/rd-checklist/backend/` → `../../../tools/rd-card-scraper/data/`
