# Yu-Gi-Oh Rush Duel Collection

## 專案概述

收集和管理 Yu-Gi-Oh Rush Duel (遊戲王 超速決鬥) 卡牌資訊。資料來源為 ntucgm.blogspot.com（開拓卡研）。

## 專案結構

```
tools/
  rd-card-scraper/          # 卡牌資訊爬取工具 (Python + uv)
    rd_card_scraper/        # 主程式碼
    pyproject.toml
    data/                   # 爬取結果 (gitignore)

apps/
  rd-checklist/             # 收藏管理 Web App
    backend/                # FastAPI + SQLite 後端
      rd_checklist/         # 主程式碼
      pyproject.toml
      data/                 # DB + 使用者圖片 (gitignore)
    frontend/               # Vue 3 + TypeScript + Tailwind CSS
      src/
      package.json
```

## 開發環境

- Python 3.11+, 套件管理用 uv
- Node.js 18+, 前端用 npm

## Scraper 常用指令

```bash
cd tools/rd-card-scraper
uv sync
uv run python -m rd_card_scraper.cli discover       # 發現所有卡表文章
uv run python -m rd_card_scraper.cli scrape-all     # 全量爬取
uv run python -m rd_card_scraper.cli update         # 增量更新
uv run python -m rd_card_scraper.cli scrape-url URL # 爬取單一 URL
uv run python -m rd_card_scraper.cli summary        # 爬取狀態摘要
uv run python -m rd_card_scraper.cli scrape-all --no-images  # 不下載圖片
uv run python -m rd_card_scraper.cli update --force          # 強制重新爬取
uv run python -m rd_card_scraper.cli --since 2025 discover   # 只發現 2025 年以後的文章
```

## Checklist App 常用指令

```bash
# Backend
cd apps/rd-checklist/backend
uv sync
uv run python -m rd_checklist.cli init-db                           # 初始化資料庫
uv run python -m rd_checklist.cli import --scraper-data ../../../tools/rd-card-scraper/data  # 匯入爬取資料
uv run uvicorn rd_checklist.main:app --reload --port 8000           # 啟動後端

# Frontend
cd apps/rd-checklist/frontend
npm install
npm run dev         # 啟動前端 (http://localhost:5173, proxy /api → :8000)
npm run build       # 正式建置
npm run type-check  # TypeScript 檢查
```

## 注意事項

- 爬取時遵守禮儀：頁面間隔 1.5s、圖片間隔 0.3s
- `data/` 目錄已在 .gitignore，不會被 commit
- 增量更新基於 post-body 的 SHA256 hash 比對
- Checklist App 匯入不會覆蓋使用者的 owned_count
- 卡圖直接從 scraper data 目錄讀取，不複製；使用者可上傳覆蓋，存於 data/images/user_uploads/
