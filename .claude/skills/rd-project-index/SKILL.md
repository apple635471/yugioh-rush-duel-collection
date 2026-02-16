---
name: rd-project-index
description: Navigation hub for Yu-Gi-Oh Rush Duel Collection. Read this first when asking logic questions, opening features, modifying code, or debugging bugs in rd-checklist or rd-card-scraper. Maps tasks to specific skills to avoid crawling all code.
---

# 專案 SKILL 導航

**開始任何邏輯問題、開 feature、修 bug、了解架構前，先讀此 SKILL 決定要讀哪些細部 SKILL。**

## rd-checklist (收藏管理 App)

| 任務 | 讀此 SKILL |
|-----|-----------|
| 加/改 API endpoint、debug 後端請求、response schema | `rd-checklist-api` |
| 加/改 DB 表/欄位、理解 card-variant 關係、migration | `rd-checklist-db-schema` |
| 加/改前端元件、debug UI、Pinia store、路由 | `rd-checklist-frontend-arch` |
| 圖片來源、上傳、還原、404、路徑、快取 | `rd-checklist-image-serving` |
| 匯入邏輯、owned_count 被覆蓋、多稀有度拆分 | `rd-checklist-data-import` |

## rd-card-scraper (爬蟲)

| 任務 | 讀此 SKILL |
|-----|-----------|
| 改 parser、HTML 解析、新卡表格式、卡片欄位 | `rd-html-parsing` |
| 改 discovery、URL 篩選、sitemap、標題分類 | `ntucgm-blog-structure`, `rd-banlist-exclusion` |
| 增量更新、hash 比對、重複爬取 | `rd-incremental-update` |
| 圖片下載、URL、尺寸參數 | `rd-image-urls` |
| 產品類型、set_id 前綴、篩選 | `rd-product-types` |
| 卡片類型/屬性/種族關鍵字、regex | `rd-card-keywords` |
| 爬取間隔、禮儀 | `rd-scraping-etiquette` |

## 修改程式碼後

| 任務 | 讀此 SKILL |
|-----|-----------|
| 架構/schema/API/元件變更後需同步文件 | `rd-docs-sync` |
| feature/fix/refactor 後需更新 CHANGELOG | `rd-changelog-reminder` |
