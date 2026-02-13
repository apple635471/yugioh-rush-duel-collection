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
```

## 開發環境

- Python 3.11+, 套件管理用 uv
- 相依套件: requests, beautifulsoup4, lxml

```bash
cd tools/rd-card-scraper
uv sync
```

## 常用指令

```bash
# 在 tools/rd-card-scraper 目錄下執行
uv run python -m rd_card_scraper.cli discover       # 發現所有卡表文章
uv run python -m rd_card_scraper.cli scrape-all     # 全量爬取
uv run python -m rd_card_scraper.cli update         # 增量更新
uv run python -m rd_card_scraper.cli scrape-url URL # 爬取單一 URL
uv run python -m rd_card_scraper.cli summary        # 爬取狀態摘要
uv run python -m rd_card_scraper.cli scrape-all --no-images  # 不下載圖片
uv run python -m rd_card_scraper.cli update --force          # 強制重新爬取
```

## 注意事項

- 爬取時遵守禮儀：頁面間隔 1.5s、圖片間隔 0.3s
- `data/` 目錄已在 .gitignore，不會被 commit
- 增量更新基於 post-body 的 SHA256 hash 比對
