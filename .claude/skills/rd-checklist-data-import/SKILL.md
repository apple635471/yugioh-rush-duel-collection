---
name: rd-checklist-data-import
description: Data import flow and safety rules for importing scraper data into the checklist DB. Use when modifying import logic or debugging import issues.
---

# Checklist App 資料匯入流程

從 scraper 的 `data/` 目錄匯入到 SQLite。

## 指令

```bash
uv run python -m rd_checklist.cli import --scraper-data PATH
uv run python -m rd_checklist.cli import --scraper-data PATH --force  # 強制重建
```

## 匯入流程

```
data/
  KP01/cards.json
  KP09/cards.json
  ...
     │
     ▼ import_scraper_data(scraper_data_dir, force=False)
     │
     ├─ 掃描所有 */cards.json
     ├─ 每個 json: _upsert_card_set() → card_sets 表
     ├─ 每張卡: _upsert_card() → cards 表 (全欄位更新)
     └─ 每個 rarity: _upsert_variant() → card_variants 表
```

## 多稀有度拆分

Scraper 輸出 `"rarity": "UR/SER"`，匯入時:
1. `rarity.split("/")` → `["UR", "SER"]`
2. 為每個稀有度建立獨立的 `card_variants` row
3. `sort_order` = 拆分後的 index (0, 1, ...)

## ★ 安全規則

`_upsert_variant()` 的核心保護:

```python
existing = db.query(CardVariantModel).filter_by(card_id=card_id, rarity=rarity).first()
if existing:
    # 只更新 image 相關欄位，NEVER touch owned_count
    existing.image_source = ...
    existing.image_path = ...
else:
    # 新建時 owned_count 預設為 0
    db.add(CardVariantModel(card_id=card_id, rarity=rarity, owned_count=0, ...))
```

這確保使用者辛苦標記的持有數量在重新匯入時不會被覆蓋。

## 圖片路徑映射

Scraper 的 `image_file`: `"images/RD_KP01-JP001.jpg"`
→ 匯入後 `image_path`: `"KP01/images/RD_KP01-JP001.jpg"` (加上 set_id 前綴)
→ Backend 讀取時組合: `SCRAPER_DATA_DIR / image_path`

## 匯入結果 (截至 2026-02)

- 54 sets, 2,210 cards, 2,522 variants
- 305 張卡有多稀有度版本 (2,522 - 2,210 = 312 額外 variants)
