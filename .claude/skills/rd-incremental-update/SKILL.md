---
name: rd-incremental-update
description: Incremental update strategy for the card scraper. Use when modifying update logic, debugging state management, or optimizing scrape performance.
---

# 增量更新策略

- 使用 `scrape_state.json` 追蹤每篇文章的 URL、內容 hash、上次爬取時間
- 內容 hash 基於 post-body HTML 的 SHA256 前 16 字元
- 更新流程: 發現 URL → 取得頁面 → 計算 hash → 比對 → 有變更才重新解析
- 這避免了每次都重新下載全部 ~60 篇文章和數千張圖片
- 圖片只在檔案不存在時才下載，已存在的會跳過 (除非 `--force`)
