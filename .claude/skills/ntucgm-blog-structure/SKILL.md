---
name: ntucgm-blog-structure
description: Understanding the ntucgm.blogspot.com blog structure for discovering and classifying Rush Duel card list articles. Use when working with article discovery, URL filtering, or sitemap parsing.
---

# ntucgm 部落格結構

- 來源: `https://ntucgm.blogspot.com/`
- 平台: Google Blogger
- 文章標籤: `[卡表資料]` = 卡表文章, `[禁限卡表]` = 禁止限制表, `[Meta展望]` = 環境分析
- 只有 `[卡表資料]` 標籤的文章包含完整的卡牌資料
- 目前約有 **~74 篇** Rush Duel 卡表文章 (2020~2026)

## 文章發現方式

採用 **blog listing page 翻頁 + 標題篩選** 策略:

1. 透過 `/search?updated-max=...&max-results=20` 翻頁 listing page
2. 每頁包含 ~20 篇文章的 **URL + 標題**
3. 標題含 `[卡表資料]` + RD 關鍵字 → 直接視為卡表
4. 其餘 URL 含 `rush-duel`/`rdgrd` 的文章 → 需 fetch 驗證內容

### 為什麼不用 sitemap？

- Sitemap (`/sitemap.xml`) 只有 URL，沒有標題
- 無法在不 fetch 每篇文章的情況下判斷是否為 RD 卡表
- Listing page 提供標題，可直接分類 ~90% 的文章

## Listing Page 結構

- 文章標題: `h3.post-title > a[href]`
- 文章日期: `a.post-timestamp`
- 下一頁連結: `a.blog-pager-older-link` (或 `#blog-pager a` 中含 `updated-max=` 的)
- 排序: 按最後更新時間遞減 (不是發布時間)
- Blogger 限制: max-results 上限約 20

## URL 命名不一致

Blog 的 URL slug 命名**沒有統一規則**:
- 有些用產品代號: `/rush-duel-kp09-49.html`
- 有些用日期: `/rush-duel-110.html` (2025/11 發售)
- 有些完全無關: `/blog-post.html`, `/2022-vol.html`

因此**不能依賴 URL 模式匹配**來判斷是否為特定產品的卡表。
