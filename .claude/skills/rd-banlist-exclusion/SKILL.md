---
name: rd-banlist-exclusion
description: Rules for excluding posts that look like Rush Duel card lists but aren't (ban lists, OCG products). Use when modifying URL discovery/filtering logic.
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

# 非 Rush Duel 的商品（OCG）

部落格也寫本傳 OCG 的卡表，標題一樣掛 `[卡表資料]`。判別關鍵是**卡號格式**：Rush Duel
一律是 `RD/{set}-JP###`，OCG 沒有 `RD/` 前綴。爬到這種文章會解析出 0 張卡。

已知案例：**Revolution Booster**（`RV01-JP###`，主題是卡通／巫術／破械，都是 OCG 主題）。
它原本被**誤列在接受清單**裡（`RD_TITLE_KEYWORDS` 與 `RD_URL_MARKERS` 各一筆），已改為排除：

- `EXCLUDE_TITLE_KEYWORDS` 加入 `"Revolution Booster"`
- `EXCLUDE_URL_PATTERNS` 加入 `r"revolution-booster"`（雙保險，標題改寫也擋得住）

判斷一篇是不是 OCG：抓下來看卡號有沒有 `RD/` 前綴即可

```bash
uv run python -c "
import requests
from rd_card_scraper.parser import extract_post_body, CARD_ID_RE
h = requests.get(URL, timeout=25, headers={'User-Agent':'Mozilla/5.0'}).text
print(len(CARD_ID_RE.findall(extract_post_body(h).get_text())), '個 RD 卡號')"
```
