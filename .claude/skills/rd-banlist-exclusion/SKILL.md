---
name: rd-banlist-exclusion
description: Rules for excluding ban list URLs that look like card list posts. Use when modifying URL discovery/filtering logic.
---

# 禁限卡表排除

## 現行策略 (v2 — 標題優先)

Discovery 現在主要透過**文章標題**篩選:

- 標題含 `禁限卡表` → **直接排除** (在 `EXCLUDE_TITLE_KEYWORDS` 中)
- 標題含 `[卡表資料]` + RD 關鍵字 → 接受

因此禁限卡表在標題篩選階段就會被排除，不需要 URL 模式匹配。

## URL 排除 (備用)

對於標題無法分類的文章 (Phase 3 URL fallback)，仍保留 URL 排除規則:

**排除 regex**: `r"/rush-duel-202\d{2,}"`

匹配 URL 中 `rush-duel-` 後接 `202` + 2位以上數字的模式:
- ✗ `/rush-duel-20231.html` → 2023年1月禁限 (排除)
- ✗ `/rush-duel-202410.html` → 2024年10月禁限 (排除)
- ✓ `/rush-duel-2025.html` → 2025活動包集合 (保留，因 `2025` 只有1位數在202後)

## 禁限卡表 URL 範例

```
rush-duel-20231.html     → 2023年1月
rush-duel-20234.html     → 2023年4月
rush-duel-20241.html     → 2024年1月
rush-duel-202410.html    → 2024年10月
rush-duel-20254.html     → 2025年4月
rush-duel-20261.html     → 2026年1月
```
