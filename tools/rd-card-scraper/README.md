# rd-card-scraper

從 [ntucgm.blogspot.com](https://ntucgm.blogspot.com/)（開拓卡研）爬取 Yu-Gi-Oh Rush Duel 卡牌資訊。

## 架構

```
cli.py                  # CLI 進入點 (discover, scrape-all, update, scrape-url, summary)
  │
  ├── discovery.py      # 從 sitemap 發現卡表文章 URL (~59 篇)
  │                     # 排除禁限卡表等非卡表文章
  │
  ├── scraper.py        # 爬取協調器
  │   │                 # 管理 scrape_state.json (SHA256 hash 偵測變更)
  │   │
  │   ├── parser.py     # HTML → CardSet + Card[]
  │   │                 # chunk-based 解析，支援 2020~2025 三種 HTML 結構
  │   │
  │   └── downloader.py # 下載卡圖 (rate-limited: 0.3s/張)
  │
  └── models.py         # 資料模型 (Card, CardSet, ScrapeState)
```

## 輸出格式

```
data/
  ├── KP01/
  │   ├── cards.json      # 卡片資料陣列
  │   └── images/         # RD_KP01-JP000.jpg, ...
  ├── KP09/
  │   ├── cards.json
  │   └── images/
  └── scrape_state.json   # 增量更新狀態
```

每張卡片的 JSON 包含：`card_id`, `rarity`, `name_jp`, `name_zh`, `card_type`, `attribute`, `monster_type`, `level`, `atk`, `defense`, `condition`, `effect`, `image_url`, `image_file`, `is_legend`。

## 指令

```bash
uv sync                                          # 安裝相依套件
uv run python -m rd_card_scraper.cli discover     # 發現所有卡表文章
uv run python -m rd_card_scraper.cli scrape-all   # 全量爬取
uv run python -m rd_card_scraper.cli update       # 增量更新 (只爬新/變更的)
uv run python -m rd_card_scraper.cli scrape-url URL  # 爬取單一文章
uv run python -m rd_card_scraper.cli summary      # 爬取狀態摘要

# 選項
uv run python -m rd_card_scraper.cli scrape-all --no-images  # 不下載圖片
uv run python -m rd_card_scraper.cli update --force          # 強制重爬
```

## 注意事項

- 爬取禮儀：頁面間隔 1.5s、圖片間隔 0.3s、sitemap 間隔 0.5s
- 增量更新基於 post-body 的 SHA256 hash，內容沒變就跳過
- 圖片只在本地不存在時才下載
