---
name: rd-scraping-etiquette
description: Rate limiting and scraping etiquette rules for the ntucgm blog. Use when modifying request logic or adding new scraping features.
---

# 部落格爬取禮儀

- Listing page 翻頁間隔: **1.5 秒**
- 頁面請求間隔 (驗證/爬取): **1.5 秒**
- 圖片下載間隔: **0.3 秒**
- 使用自訂 User-Agent: `Mozilla/5.0 (compatible; RD-Card-Scraper/0.1)`
- 不要平行發送多個請求

## 最佳化策略

- **標題優先篩選**: 從 listing page 標題判斷是否為 RD 卡表，避免不必要的 fetch
- **Pagination cursor 截止**: 預設只爬 2020 年以後的 listing page (~71 頁)
- **增量早停**: 傳入 known_urls，當整頁都是已知 URL 時立即停止
- **SHA256 hash 偵測**: 內容沒變就跳過重爬
- **圖片跳過**: 本地已存在的圖片不重複下載
