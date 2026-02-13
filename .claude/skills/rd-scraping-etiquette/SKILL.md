---
name: rd-scraping-etiquette
description: Rate limiting and scraping etiquette rules for the ntucgm blog. Use when modifying request logic or adding new scraping features.
---

# 部落格爬取禮儀

- 頁面請求間隔至少 **1.5 秒**
- 圖片下載間隔至少 **0.3 秒**
- Sitemap 請求間隔 **0.5 秒**
- 使用自訂 User-Agent: `Mozilla/5.0 (compatible; RD-Card-Scraper/0.1)`
- 透過增量更新減少不必要的請求
- 不要平行發送多個請求
