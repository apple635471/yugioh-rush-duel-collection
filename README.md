# Yu-Gi-Oh Rush Duel Collection

收集和管理遊戲王 Rush Duel (超速決鬥) 卡牌資訊的工具組合。

## 系統架構

```
Browser (:5173)                          Backend (:8000)
┌─────────────────────────┐    HTTP     ┌──────────────────────────┐
│  Vue 3 + TS + Tailwind  │────/api───▶│  FastAPI                 │
│                         │            │                          │
│  Pinia Stores           │            │  Routers                 │
│  ├ cardSets (列表/詳情)  │◀───JSON────│  ├ /api/card-sets/*      │
│  └ ui (viewMode/sidebar)│            │  ├ /api/cards/*          │
│                         │            │  ├ /api/ownership/*      │
│  Router                 │            │  ├ /api/search           │
│  ├ / ─ HomeView         │            │  └ /api/images/*         │
│  ├ /sets/:type          │            │                          │
│  ├ /set/:id ─ SetView   │            │  SQLAlchemy ORM          │
│  └ /search              │            │  ├ card_sets             │
│                         │            │  ├ cards                 │
│  Vite Dev Proxy         │            │  ├ card_variants ★owned  │
│  :5173/api → :8000      │            │  └ card_edits (history)  │
└─────────────────────────┘            └─────────┬────────────────┘
                                                 │
                                    ┌────────────┼────────────────┐
                                    │            │                │
                               ┌────┴────┐  ┌───┴──────┐  ┌─────┴─────┐
                               │ SQLite  │  │ Scraper  │  │  User     │
                               │ WAL DB  │  │ Data     │  │  Uploads  │
                               │ (R/W)   │  │ (R only) │  │  (R/W)    │
                               └─────────┘  └──────────┘  └───────────┘
```

## 資料流

```
ntucgm.blogspot.com ──HTTP──▶ rd-card-scraper ──JSON+Images──▶ data/
                                                                 │
                              CLI: import --scraper-data ─────────┘
                                       │
                                       ▼
                              SQLite (card_sets → cards → card_variants)
                                       │
                              FastAPI ──┘──▶ Vue Frontend ──▶ 使用者
                                                    │
                              PATCH /ownership ◀────┘ (持有數 +/-)
```

## 專案結構

```
tools/
  rd-card-scraper/              # 卡牌爬取工具 (Python + uv)
    rd_card_scraper/            # discovery, parser, downloader, scraper, cli
    data/                       # 爬取結果: {SetID}/cards.json + images/ (gitignore)

apps/
  rd-checklist/                 # 收藏管理 Web App
    backend/                    # FastAPI + SQLite
      rd_checklist/             # config, database, models, schemas, routers, services, cli
      data/                     # rd_checklist.db + user uploads (gitignore)
    frontend/                   # Vue 3 + TypeScript + Tailwind CSS
      src/
        views/                  # HomeView, SetView, SearchView
        components/
          layout/               # AppHeader, BreadcrumbBar, ViewToggle
          navigation/           # ProductTypeNav, SetList
          cards/                # CardGrid, CardTable, RarityTabs, OwnershipControl
          detail/               # AppSidebar, CardDetailPanel, CardEditForm
          search/               # SearchFilters
        stores/                 # Pinia: cardSets, ui
        api/                    # Axios: cardSets, cards
        types/                  # TypeScript interfaces

.claude/skills/                 # 領域知識 (SKILL.md 格式)
```

## 快速開始

### 1. 爬取卡牌資料

```bash
cd tools/rd-card-scraper
uv sync
uv run python -m rd_card_scraper.cli scrape-all
```

### 2. 啟動 Checklist App

```bash
# Terminal 1: Backend
cd apps/rd-checklist/backend
uv sync
uv run python -m rd_checklist.cli init-db
uv run python -m rd_checklist.cli import --scraper-data ../../../tools/rd-card-scraper/data
uv run uvicorn rd_checklist.main:app --reload --port 8000

# Terminal 2: Frontend
cd apps/rd-checklist/frontend
npm install
npm run dev
# → http://localhost:5173
```

### 3. 增量更新

```bash
cd tools/rd-card-scraper
uv run python -m rd_card_scraper.cli update          # 只爬新/變更的文章

cd apps/rd-checklist/backend
uv run python -m rd_checklist.cli import --scraper-data ../../../tools/rd-card-scraper/data
# ★ 重新匯入不會覆蓋使用者的持有數量 (owned_count)
```

## 開發環境

- Python 3.11+, 套件管理用 [uv](https://github.com/astral-sh/uv)
- Node.js 18+, 前端用 npm
- SQLite 3 (WAL mode, 內建於 Python)

## 資料規模 (截至 2026-02)

- 54 個卡組 (card sets)
- 2,210 張卡片 (cards)
- 2,522 個稀有度版本 (card variants)
- 其中 305 張卡有多稀有度版本
