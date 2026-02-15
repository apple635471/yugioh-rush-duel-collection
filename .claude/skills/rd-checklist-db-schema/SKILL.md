---
name: rd-checklist-db-schema
description: Database schema design for the rd-checklist app. Use when modifying DB models, adding new tables/columns, or understanding the card-variant relationship.
---

# Checklist App 資料庫設計

SQLite + SQLAlchemy ORM，WAL mode，foreign keys enabled。

## 表結構

### card_sets
- `set_id` (PK, str): 如 "KP01", "ST01"
- `set_name_jp`, `set_name_zh`: 日文/中文名
- `product_type` (indexed): booster, starter, character_pack, ...
- `release_date`: "2020/4/11" 格式
- `post_url`: 來源文章 URL
- `total_cards`: 卡片總數
- `rarity_distribution`: JSON 字串 `{"UR": 4, "SR": 6, ...}`

### cards
- `card_id` (PK, str): 如 "RD/KP01-JP000"
- `set_id` (FK → card_sets): 所屬卡組
- `name_jp`, `name_zh`, `card_type` (indexed), `attribute`, `monster_type`
- `level`, `atk`, `defense`
- `summon_condition`: 召喚條件 (如「此卡只能用…特殊召喚」)
- `condition`: 發動條件
- `effect`: 效果說明
- `continuous_effect`: 永續效果 (與一般效果分開)
- `is_legend` (bool), `original_rarity_string`: 原始稀有度字串 "UR/SER"

### card_variants ★核心
- `id` (PK, auto), `card_id` (FK → cards), `rarity`
- `UNIQUE(card_id, rarity)`: 每張卡每個稀有度只一筆
- `owned_count` ★使用者持有數（匯入時永不覆蓋）
- `image_source`: "scraper" | "user_upload" | null
- `image_path`: 相對路徑如 "KP01/images/RD_KP01-JP000.jpg"
- `sort_order`: 同一卡內的稀有度排序

### card_edits (歷史記錄)
- `card_id`, `field_name`, `old_value`, `new_value`, `edited_at`

## 關鍵設計

- **一卡多版**: scraper 輸出 `"UR/SER"` → 匯入時拆為 2 筆 variant，各自獨立追蹤 `owned_count`
- **匯入安全**: `_upsert_variant()` 只在 variant 不存在時 INSERT，已存在的只更新 image 欄位，永不碰 `owned_count`
- **Eager loading**: `CardModel.variants` 使用 `lazy="selectin"`，查詢卡組時一次載入所有 variants 避免 N+1
- **編輯歷史**: PATCH /api/cards/ 時自動記錄每個欄位的 old/new value 到 card_edits
- **Auto-migration**: `init-db` 自動執行 `ALTER TABLE ADD COLUMN` 補新欄位，用 try/except 跳過已存在的欄位 (safe to run repeatedly)
