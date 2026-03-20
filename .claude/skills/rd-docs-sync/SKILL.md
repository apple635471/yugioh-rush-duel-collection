---
name: rd-docs-sync
description: >
  Mandatory workflow for ALL code changes in this project. TRIGGER AT THE START of any feature/fix/refactor request.
  BEFORE writing any code: (1) ask the user if they want a PR opened, (2) create a new git branch (feat/* or fix/*).
  AFTER finishing code: update CHANGELOG.md, update affected SKILL.md/README.md, then commit and create PR.
  Never work directly on main. Never skip CHANGELOG. Never skip asking about PR.
---

# 文件同步規則

**每次修改專案的邏輯架構時，必須同步更新對應的 SKILL.md 和 README.md，避免文件與程式碼衝突。**

> 開始任務前可先讀 `rd-project-index` 決定要改哪些模組、對應哪些文件。

## 觸發時機

以下任一變更發生時，必須檢查並更新文件：

| 變更類型 | 需更新的文件 |
|---------|-------------|
| DB schema (加欄位/表/改關聯) | `rd-checklist-db-schema/SKILL.md`, `backend/README.md` |
| API endpoint (新增/改路徑/改 schema) | `rd-checklist-api/SKILL.md`, `backend/README.md` |
| 前端元件 (新增/改層級/改 props) | `rd-checklist-frontend-arch/SKILL.md`, `frontend/README.md` |
| 匯入邏輯 (改拆分/merge/安全規則) | `rd-checklist-data-import/SKILL.md` |
| 圖片服務 (改路徑/來源/上傳) | `rd-checklist-image-serving/SKILL.md` |
| Scraper 解析 (新 HTML 格式/欄位) | `rd-html-parsing/SKILL.md`, `scraper/README.md` |
| 產品類型 (新前綴) | `rd-product-types/SKILL.md` |
| 專案結構 (搬目錄/改 config) | 根目錄 `README.md`, `CLAUDE.md` |
| 新增子系統/工具 | 根目錄 `README.md`, 對應 `README.md`, 考慮建新 SKILL |
| 任何 feature/fix/refactor | `CHANGELOG.md` — 見 `rd-changelog-reminder` |

## 文件位置速查

```
.claude/skills/rd-project-index/SKILL.md            # 任務→SKILL 導航 (邏輯/feature/bug 時先讀)
.claude/skills/rd-changelog-reminder/SKILL.md       # feature/fix/refactor 時更新 CHANGELOG
README.md                                           # 系統架構總覽、資料流、快速開始
CLAUDE.md                                           # 開發指令、注意事項
tools/rd-card-scraper/README.md                    # Scraper 架構、輸出格式
apps/rd-checklist/backend/README.md                # Backend 架構、DB schema、API 表
apps/rd-checklist/frontend/README.md               # 元件樹、Pinia stores、視覺設計

.claude/skills/rd-checklist-db-schema/SKILL.md     # DB 表/欄位/關聯/約束
.claude/skills/rd-checklist-api/SKILL.md           # API 端點、request/response、資料流
.claude/skills/rd-checklist-frontend-arch/SKILL.md # 元件樹、props/emit、stores
.claude/skills/rd-checklist-data-import/SKILL.md   # 匯入流程、多稀有度拆分、安全規則
.claude/skills/rd-checklist-image-serving/SKILL.md # 圖片來源優先順序、路徑解析
.claude/skills/rd-html-parsing/SKILL.md            # HTML 結構、解析策略
.claude/skills/rd-product-types/SKILL.md           # Set ID 前綴 → 產品類型
.claude/skills/rd-card-keywords/SKILL.md           # 卡片類型/屬性/種族關鍵字
```

## 執行方式

1. 完成程式碼修改後，**在同一個 commit 中**一起更新文件
2. 對照上表確認所有受影響的文件都已更新
3. 如果不確定是否需要更新，寧可更新也不要漏掉
4. 新增全新子系統時，評估是否需要建立新的 SKILL.md

## ★ 完整交付流程 (每次 feature/fix 都必須執行)

> 缺少以下任一步驟都是不完整的交付。

```
任務開始時（寫程式碼之前）：
0a. 主動詢問使用者：「這個修改要開 PR 嗎？」
0b. git checkout -b feat/xxx  或  fix/xxx  ← 一定要開新 branch，禁止在 main 直接 commit

完成程式碼後：
1. 更新 CHANGELOG.md (見 rd-changelog-reminder)
2. 更新受影響的 SKILL.md / README.md（見觸發時機表）
3. git add + git commit
4. git push -u origin <branch>
5. gh pr create  (用 GH_TOKEN from .env，見 MEMORY.md)
```

**⚠️ 最常遺漏的步驟**：
- 任務開始就問 PR → 不要等到使用者提醒才問
- 任務開始就開 branch → 不要在 main 累積修改
- 完成後更新 CHANGELOG → 不要等到使用者提醒

**branch 命名**: `feat/<簡短功能>` 或 `fix/<簡短問題>`
**PR title**: 英文，≤70 字元
**PR body**: 中文（見溝通偏好），技術名詞保留英文
