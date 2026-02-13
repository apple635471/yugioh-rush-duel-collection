---
name: rd-banlist-exclusion
description: Rules for excluding ban list URLs that look like card list posts. Use when modifying URL discovery/filtering logic.
---

# 禁限卡表 URL 排除

禁限卡表文章的 URL 模式為 `/rush-duel-{YYYY}{M}.html`，例如:
- `rush-duel-20234.html` = 2023年4月禁限卡表
- `rush-duel-202410.html` = 2024年10月禁限卡表

這些 URL 看起來像卡表文章但實際上不包含卡牌數據。

**排除規則**: 匹配 `/rush-duel-20\d{2}\d+\.html` 且 URL 中不含產品關鍵字 (如 kp, st, b0, sd, lgp, ext, max, grc, grd, vsp, tb, ap 等)。

**注意**: 有些卡表 URL 也以數字結尾 (如 `rush-duel-201-513.html` 是 KP13)，所以不能僅靠數字模式排除，必須確認是「年份+月份」的格式。
