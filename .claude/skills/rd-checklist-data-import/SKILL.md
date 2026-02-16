---
name: rd-checklist-data-import
description: Import flow from scraper data into checklist DB. Use when modifying import logic, debugging owned_count being overwritten, adding multi-rarity handling, or understanding scraper→DB mapping.
---

# Checklist App 資料匯入流程

**何時讀此 SKILL**：改匯入邏輯、owned_count 被覆蓋、多稀有度拆分、scraper 欄位對應 DB。

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
     ├─ 每張卡: _upsert_card() → cards 表 (含 summon_condition, condition, effect, continuous_effect)
     └─ 每個 rarity: _upsert_variant() → card_variants 表
```

## 多稀有度拆分

Scraper 輸出 `"rarity": "UR/SER"`，匯入時:
1. `rarity.split("/")` → `["UR", "SER"]`
2. 為每個稀有度建立獨立的 `card_variants` row
3. `sort_order` = 拆分後的 index (0, 1, ...)

## ★ 安全規則

### Card Set Override 保護

`_import_one_set()` 匯入卡組時會先查詢 `card_set_overrides` 表:

```python
overrides = {o.field_name: o.value for o in db.query(CardSetOverrideModel).filter_by(set_id=set_id)}
# 有 override 的欄位 → 使用 override 值
# 無 override 的欄位 → 使用 scraper 值
```

可被 override 的欄位: `set_name_jp`, `set_name_zh`, `product_type`, `release_date`, `total_cards`, `rarity_distribution`
不可被 override 的欄位: `post_url` (永遠用 scraper 值)

Override 透過 `PATCH /api/card-sets/{set_id}` 自動建立；刪除 override 後下次匯入恢復 scraper 值。

### Variant owned_count 保護

`_upsert_variant()` 的核心保護:

```python
existing = db.query(CardVariantModel).filter_by(card_id=card_id, rarity=rarity).first()
if existing:
    # 只更新 image 相關欄位，NEVER touch owned_count
    existing.sort_order = sort_order
    if image_file:
        existing.scraper_image_path = image_file  # 永遠保持 scraper 路徑最新
    if existing.image_source != "user_upload":    # 使用者上傳的不覆蓋
        existing.image_source = "scraper" if image_file else None
        existing.image_path = image_file
else:
    # 新建時 owned_count 預設為 0，scraper_image_path = image_file
    db.add(CardVariantModel(card_id=card_id, rarity=rarity, owned_count=0,
           scraper_image_path=image_file, ...))
```

這確保使用者辛苦標記的持有數量在重新匯入時不會被覆蓋；`scraper_image_path` 供還原功能使用。

## 圖片路徑映射

Scraper 的 `image_file`: `"images/RD_KP01-JP001.jpg"`
→ 匯入後 `image_path`: `"KP01/images/RD_KP01-JP001.jpg"` (加上 set_id 前綴)
→ 匯入後 `scraper_image_path`: 同上，供還原時使用，匯入與首次上傳時寫入
→ Backend 讀取時組合: `SCRAPER_DATA_DIR / image_path`

## 匯入結果 (截至 2026-02)

- 54 sets, 2,210 cards, 2,522 variants
- 305 張卡有多稀有度版本 (2,522 - 2,210 = 312 額外 variants)
