# Changelog

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
