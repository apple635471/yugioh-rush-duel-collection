---
name: rd-changelog-reminder
description: Mandatory checklist item: update CHANGELOG.md when adding features, fixing bugs, or doing significant refactors. Use before committing to avoid forgetting release notes.
---

# CHANGELOG 更新提醒

**開 feature、改 bug、重構時，必須在同一個 commit 中更新 CHANGELOG.md。**

## 觸發時機

| 變更類型 | 是否更新 CHANGELOG |
|---------|-------------------|
| 新增功能 (feature) | ✅ 必須 |
| 修復 bug (fix) | ✅ 必須 |
| 重構 (refactor) | ✅ 顯著變更時必須 |
| 僅文件/SKILL 同步 | 視情況 (若配合前 commit 可一併記錄) |

## 格式

在 `CHANGELOG.md` 最上方新增版本區塊：

```markdown
## vX.Y.Z (YYYY-MM-DD)

### 新增 / 修復 / 更新
- 條目 1
- 條目 2
```

版本號依語意化版本：feature → minor (0.3→0.4)，bugfix → patch (0.3.1→0.3.2)。

## 執行時機

1. 完成程式碼修改後、commit 前
2. 與 `rd-docs-sync` 一併檢查：改架構時同時更新 CHANGELOG + 對應 SKILL/README
