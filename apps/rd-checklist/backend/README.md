# rd-checklist Backend

FastAPI + SQLite 後端，提供卡牌瀏覽、搜尋、持有數追蹤、卡片編輯 API。

## 架構

```
main.py                     # FastAPI app, CORS, 註冊 routers
  │
  ├── routers/
  │   ├── card_sets.py      # GET /api/card-sets, /product-types, /{set_id}
  │   ├── cards.py          # GET/PATCH /api/cards/{card_id}
  │   ├── ownership.py      # PATCH /api/ownership/{card_id}/{rarity}, /batch, GET /stats
  │   ├── search.py         # GET /api/search?q=&card_type=&attribute=&level=&rarity=&owned=
  │   └── images.py         # GET /api/images/card/{card_id}/{rarity}, POST upload, DELETE revert
  │
  ├── services/
  │   ├── import_service.py # 從 scraper data 匯入 DB (拆分多稀有度)
  │   └── image_service.py  # 圖片路徑解析 (scraper data vs user uploads)
  │
  ├── models.py             # SQLAlchemy ORM (card_sets, cards, card_variants, card_edits)
  ├── schemas.py            # Pydantic request/response models
  ├── database.py           # Engine setup (WAL mode), get_db dependency
  ├── config.py             # 路徑設定 (DB, scraper data, user uploads)
  └── cli.py                # CLI: init-db, import
```

## 資料庫 Schema

```
card_sets  ◄──1:N──  cards  ◄──1:N──  card_variants
  │                    │                   │
  set_id (PK)         card_id (PK)        id (PK)
  set_name_jp         set_id (FK)         card_id (FK)
  set_name_zh         name_jp/name_zh     rarity
  product_type        card_type           owned_count ★使用者資料
  release_date        attribute/level     image_source (scraper/user)
  total_cards         atk/defense         image_path
  rarity_distribution effect/condition    UNIQUE(card_id, rarity)
                      is_legend

card_edits (歷史記錄)
  card_id, field_name, old_value, new_value, edited_at
```

**關鍵設計**：同一張卡的不同稀有度 (如 UR/SER) 拆為獨立 `card_variants`，各自追蹤 `owned_count`。

## 指令

```bash
uv sync
uv run python -m rd_checklist.cli init-db
uv run python -m rd_checklist.cli import --scraper-data ../../../tools/rd-card-scraper/data
uv run uvicorn rd_checklist.main:app --reload --port 8000
```

## API 一覽

| Method | Path | 用途 |
|--------|------|------|
| GET | `/api/card-sets/product-types` | 產品類型 + 數量 |
| GET | `/api/card-sets?product_type=` | 卡組列表 |
| GET | `/api/card-sets/{set_id}` | 卡組 + 所有卡片 (eager load variants) |
| GET | `/api/cards/{card_id}` | 單卡詳情 |
| PATCH | `/api/cards/{card_id}` | 編輯卡片 (記錄 card_edits) |
| PATCH | `/api/ownership/{card_id}/{rarity}` | 更新持有數 |
| PATCH | `/api/ownership/batch` | 批次更新 |
| GET | `/api/ownership/stats[/{set_id}]` | 收藏統計 |
| GET | `/api/search?q=&...` | 多條件搜尋 |
| GET | `/api/images/card/{card_id}/{rarity}` | 卡圖 (優先 user upload) |

## 注意事項

- 匯入永不覆蓋 `owned_count`，可安全重新匯入
- SQLAlchemy `lazy="selectin"` 避免 N+1 查詢
- CORS 允許 localhost:5173 (前端 dev server)
