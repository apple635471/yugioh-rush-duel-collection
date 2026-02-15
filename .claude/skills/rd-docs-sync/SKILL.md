---
name: rd-docs-sync
description: Mandatory rule to keep documentation in sync with code changes. ALWAYS check this skill when modifying architecture, schemas, APIs, components, or data flow in this project.
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

## 文件位置速查

```
.claude/skills/rd-project-index/SKILL.md            # 任務→SKILL 導航 (邏輯/feature/bug 時先讀)
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
