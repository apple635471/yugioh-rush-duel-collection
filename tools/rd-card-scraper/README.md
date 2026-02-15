# rd-card-scraper

從 [ntucgm.blogspot.com](https://ntucgm.blogspot.com/)（開拓卡研）爬取 Yu-Gi-Oh Rush Duel 卡牌資訊。

## 架構

```
cli.py                  # CLI 進入點 (discover, scrape-all, update, scrape-url, summary)
  │
  ├── discovery.py      # 從 blog listing page 發現卡表文章 (~74 篇)
  │                     # 策略: 標題篩選優先, URL 兜底驗證
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

## Discovery 策略

**「標題優先，內容驗證兜底」** (title first, content fallback)

```
Phase 1: 翻頁爬取 blog listing page (20篇/頁, ~71頁到 2020)
         ↓ 拿到所有文章的 URL + 標題
Phase 2: 標題篩選
         [卡表資料] + RD 關鍵字 → ✓ 直接接受
         [禁限卡表]/Meta/Combo → ✗ 直接排除
         ↓ 無法分類的文章
Phase 3: URL 含 rush-duel/rdgrd → 候選
         ↓
Phase 4: Fetch 驗證內容 (檢查 RD/ 卡號 + 卡片類型關鍵字)
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
--since YEAR        # 只發現指定年份以後的文章 (預設: 2020)
--no-images         # 不下載圖片
--force             # 強制重爬 (忽略 hash)
-v, --verbose       # 詳細日誌

# 範例
uv run python -m rd_card_scraper.cli --since 2025 discover    # 只看 2025 年以後
uv run python -m rd_card_scraper.cli scrape-all --no-images   # 全量但不下載圖片
uv run python -m rd_card_scraper.cli update --force           # 強制全部重爬
```

## 注意事項

- 爬取禮儀：listing page 間隔 1.5s、頁面爬取間隔 1.5s、圖片間隔 0.3s
- 增量更新基於 post-body 的 SHA256 hash，內容沒變就跳過
- 增量更新自動傳入 known_urls，listing page 翻到全部已知就停止
- 圖片只在本地不存在時才下載
