# Changelog

## v0.3.2 (2026-02-15)

### 新增

#### 卡組 metadata 編輯與 override 持久化
- **SetMetadataEditor**: 卡組頁可編輯 set_name_jp/zh、product_type、release_date、total_cards、rarity_distribution
- **card_set_overrides 表**: 使用者編輯的欄位存於此表，匯入時不覆蓋有 override 的欄位
- **還原單一欄位**: 刪除 override 後，下次匯入會恢復 scraper 原始值

### 更新

- API: `PATCH /api/card-sets/{set_id}` 編輯卡組、`GET /overrides` 列出 override、`DELETE /overrides/{field}` 還原
- 匯入服務: `_upsert_card_set()` 跳過有 override 的欄位
- 前端 `api/cardSets.ts`: `updateCardSet()`, `fetchCardSetOverrides()`, `deleteCardSetOverride()`

---

## v0.3.1 (2026-02-15)

### 新增

#### 卡圖上傳與還原
- **側邊欄卡圖上傳**: CardDetailPanel 卡圖 hover 顯示上傳 overlay，點擊選擇圖片替換
- **還原為原始圖**: 使用者上傳的卡圖可點「Revert to original」恢復為 scraper 原始圖
- **scraper_image_path 欄位**: 新增 `card_variants.scraper_image_path` 持久保存原始 scraper 路徑，確保即使所有 variant 皆被覆蓋仍能正確還原

### 修復

- **瀏覽器快取問題**: 使用者上傳圖檔回傳 `Cache-Control: no-cache`，前端對 user_upload 圖 URL 加 `?t=...` cache buster 避免顯示舊圖

### 更新

- API: `POST /api/images/card/{card_id}/{rarity}/upload`、`DELETE .../upload` 對應上傳與還原
- 前端 `api/cards.ts`: 新增 `uploadCardImage()`, `revertCardImage()`
- 匯入時寫入 `scraper_image_path`，上傳時保留原始路徑供還原使用

---

## v0.3.0 (2026-02-15)

### 新增

#### 複合卡片類型支援
- Parser 新增複合怪獸類型: `儀式/效果怪獸`, `融合/效果怪獸`, `巨極/效果怪獸`
- Parser 新增魔法子類型: `儀式魔法`
- Regex 排序: 複合類型在簡單類型前匹配，避免 `儀式/效果怪獸` 被截斷為 `效果怪獸`

#### 永續效果 & 召喚條件欄位
- 新增 `continuous_effect` 欄位: 解析 `永續效果:` 標籤，與一般 `效果:` 分開儲存
- 新增 `summon_condition` 欄位: 解析 stats 行與 `條件:` 之間的描述文字 (如「此卡只能用…特殊召喚」)
- 同行多標籤拆分: 處理 `條件:…可以發動效果:…` 連在同一個 HTML element 的情況
- `_LABEL_SPLIT_RE` 使用 negative lookbehind `(?<!永續)` 避免拆斷 `永續效果:`

#### 前端 inline 編輯
- CardDetailPanel 重寫為 inline 編輯模式 (取代獨立的 CardEditForm)
- Card Type 改為下拉選單 (包含所有簡單 + 複合類型)
- 怪獸專屬欄位 (Attribute, Race, Level, ATK, DEF, Summon Condition) 僅在選擇怪獸類型時顯示
- 文字欄位 (Summon Condition, Condition, Effect, Continuous Effect) 無值時收合為 `+` 按鈕，點擊展開

### 修復

- **`--no-images` 遺失圖片路徑**: 新增 `_link_existing_images()` 在不下載時偵測磁碟上已存在的圖片檔，保留 `image_file` 路徑
- **搜尋複合類型**: `card_type` 篩選改用 `ILIKE` 部分比對，搜尋「儀式」可同時匹配 `儀式怪獸` 和 `儀式/效果怪獸`

### 更新

- DB migration: `init-db` 自動 `ALTER TABLE ADD COLUMN` 補新欄位 (safe to run repeatedly)
- 前端 SearchFilters: 補齊所有卡片類型選項
- 刪除 `CardEditForm.vue` (功能已整合至 CardDetailPanel)

---

## v0.2.1 (2026-02-15)

### 修復

#### Discovery 策略重寫

- **問題**: 舊版 discovery 使用 sitemap + URL 模式匹配，漏掉了 ~15 篇使用非標準 URL slug 的卡表文章 (如 `rush-duel-110.html`)
- **新策略**: 「標題優先，內容驗證兜底」
  - Phase 1: 翻頁爬取 blog listing page，每頁 ~20 篇文章含 URL + 標題
  - Phase 2: 標題含 `[卡表資料]` + RD 關鍵字 → 直接接受；含 `禁限卡表`/Meta/Combo → 直接排除
  - Phase 3: URL 含 `rush-duel`/`rdgrd` 但標題無法分類 → 候選
  - Phase 4: 候選文章 fetch 驗證內容 (RD/ 卡號 + 卡片類型關鍵字)
- **結果**: 74 篇 RD 卡表 (比舊版多 15 篇)，0 篇需要逐篇 fetch 驗證
- **效能**: 預設只爬 2020 年以後 (~71 頁 listing page)，增量更新自動早停

### 新增

- CLI `--since YEAR` 參數: 限定只發現指定年份以後的文章 (如 `--since 2025` 只翻 9 頁)
- 增量更新早停: 傳入 known_urls，當整頁都是已知 URL 時停止翻頁
- Pagination cursor 年份截止: 基於 `updated-max` 參數判斷是否繼續翻頁

### 更新

- discovery.py: 完全重寫 (移除 sitemap 方式，改用 listing page 翻頁 + 標題篩選)
- scraper.py: 支援 `**discover_kwargs` 透傳參數 (since_year 等)
- cli.py: 新增 `--since` 參數，discover 指令顯示標題
- 3 個 SKILL 更新: ntucgm-blog-structure, rd-banlist-exclusion, rd-scraping-etiquette
- tools/rd-card-scraper/README.md: 更新架構圖與 discovery 策略說明

---

## v0.2.0 (2026-02-14)

### 新增

#### rd-checklist 收藏管理 Web App

**Backend (FastAPI + SQLite)**
- 資料庫設計: `card_sets`, `cards`, `card_variants` (每個稀有度一筆), `card_edits` (編輯歷史)
- 匯入服務: 從 scraper 的 `cards.json` 匯入，自動拆分多稀有度 (如 `UR/SER` → 兩筆 variant)
- 匯入安全: 重新匯入時絕不覆蓋使用者的 `owned_count`
- API 端點:
  - `GET /api/card-sets` — 列出所有卡組，可依產品類型篩選
  - `GET /api/card-sets/product-types` — 產品類型列表 (含中文顯示名)
  - `GET /api/card-sets/{set_id}` — 卡組詳情含所有卡片
  - `GET/PATCH /api/cards/{card_id}` — 卡片詳情與編輯
  - `PATCH /api/ownership/{card_id}/{rarity}` — 更新持有數量
  - `PATCH /api/ownership/batch` — 批次更新
  - `GET /api/ownership/stats[/{set_id}]` — 收藏統計
  - `GET /api/search` — 搜尋 (支援名稱/ID/效果/類型/屬性/等級/稀有度/持有狀態)
  - `GET /api/images/card/{card_id}/{rarity}` — 卡圖 (直接讀取 scraper data)
- CLI: `init-db`, `import --scraper-data PATH [--force]`
- 匯入結果: 54 sets, 2210 cards, 2522 variants (305 多稀有度卡)

**Frontend (Vue 3 + TypeScript + Tailwind CSS)**
- 深色主題 UI
- 首頁: 產品類型篩選 pill + 卡組列表 grid
- 卡組頁: 收藏進度條、Card View (圖片 grid) / Table View 切換
- 卡片 Grid: 卡圖 + 稀有度 tabs + 持有數 +/- 控制、未持有卡片灰階顯示
- 卡片 Table: 排列 ID/名稱/類型/LV/ATK/DEF/稀有度/持有數，未持有行半透明
- 卡片詳情側邊欄: 大圖、完整卡片資訊、效果文字、編輯表單
- 搜尋頁: 即時搜尋 (300ms debounce) + 類型/屬性/等級/稀有度/持有狀態 filter
- 麵包屑導航、Esc 關閉側邊欄
- Vite proxy `/api` → backend

### 更新

- CLAUDE.md: 加入 Checklist App 指令與結構說明
- .gitignore: 加入 backend/data/、frontend/node_modules/、frontend/dist/

---

## v0.1.0 (2026-02-13)

### 新增

#### rd-card-scraper 卡牌爬取工具
- **文章發現** (`discovery.py`): 從 sitemap 自動發現 ~59 篇 Rush Duel 卡表文章，透過 URL 模式比對區分卡表 vs 禁限卡表
- **HTML 解析** (`parser.py`): 支援 2020~2025 三個不同時期的部落格 HTML 結構
  - 2020 (KP01 時期): 卡名和 stats 都在 `<b><span>` 中，無圖片
  - 2022 (KP09 時期): stats 在普通 `<div>` 中，有 `<img>` 圖片
  - 2025 (KP23 時期): 圖片在 `<a><img>` wrapper 中
- **圖片下載** (`downloader.py`): 從 blogger.googleusercontent.com 下載卡牌圖片，支援尺寸參數調整
- **增量更新** (`scraper.py`): 基於 post-body 的 SHA256 hash 偵測內容變更，避免重複爬取
- **CLI** (`cli.py`): 支援 `discover`, `scrape-all`, `update`, `scrape-url`, `summary` 等指令

#### 每張卡片記錄的欄位
- 卡片編號 (`RD/{SetID}-JP{Number}`)
- 日文名、中文名
- 卡片類型 (怪獸/魔法/陷阱及子類型)
- 屬性、種族、等級、ATK/DEF
- 發動條件、效果說明
- 卡圖 URL 及本地圖片路徑
- 稀有度、Legend 標記

#### 專案基礎建設
- CLAUDE.md: 專案概述、開發指令
- `.claude/skills/`: 8 個 SKILL.md 檔案，記錄部落格結構、解析心法、產品類型等領域知識
- `.gitignore`: 排除 data/、.venv/、.claude/settings.local.json

### 開發筆記

#### 網站結構探索過程
1. 透過 sitemap.xml 取得所有文章 URL
2. 發現禁限卡表 URL (`rush-duel-20234.html`) 與卡表 URL 容易混淆，需要排除規則
3. 確認卡表文章有「摘要索引 + 詳細區塊」雙重結構，卡片 ID 會出現兩次

#### Parser 迭代過程
- **v1 嘗試**: 以 bold (`<b>`) 元素作為卡片邊界 → 失敗，因為 KP01 時期的 stats 行也是 bold
- **v2 (最終)**: 改用 chunk-based 方法 — 將 HTML 扁平化為 text/image chunks，用「是否有 stats 關鍵字在附近」判斷是摘要還是詳細區塊

#### 測試結果
| 彈數 | 年份 | 預期張數 | 解析張數 | 圖片 |
|------|------|----------|----------|------|
| KP01 | 2020 | 51 | 48 | 無 (文章無圖) |
| KP09 | 2022 | 66 | 66 ✓ | 66 ✓ |
| KP23 | 2025 | 68 | 63 | 63 |
