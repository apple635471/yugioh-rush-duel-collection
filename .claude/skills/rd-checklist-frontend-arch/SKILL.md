---
name: rd-checklist-frontend-arch
description: Vue 3 frontend architecture for rd-checklist (components, Pinia stores, routing). Use when adding/modifying components, debugging UI behavior, understanding data flow between views and API, or changing view structure.
---

# Checklist App 前端架構

**何時讀此 SKILL**：加/改元件、debug UI、改 store 或路由、理解元件層級與 emit 流程。

Vue 3 (Composition API) + TypeScript + Tailwind CSS + Pinia + Vue Router + **PrimeVue v4**。

## UI 元件庫

**PrimeVue v4** (`primevue@^4.5.4` + `@primeuix/themes`)
- 主題：`definePreset(Aura, ...)` 客製 primary palette 為 amber（`{amber.50}` → `{amber.950}`）
- `darkModeSelector: ':root'` — 全域強制深色，不依賴系統設定
- CSS layer 順序 (main.css)：`@layer tailwind-base, primevue, tailwind-utilities`
  - Tailwind utilities 永遠覆蓋 PrimeVue 預設樣式
- 使用元件：`Button`、`InputText`、`InputNumber`、`Select`、`Textarea`、`Checkbox`、`SelectButton`
- Button severity 規範：`warn` = 主要操作（amber）、`secondary` = 次要、`danger` = 刪除、`success` = 完成
- Button variant 規範：(無) = 實心、`outlined` = 外框、`text` = 無背景

**★ PrimeVue 優先原則**：所有互動式元素（按鈕、輸入框、下拉選單、彈窗等）必須優先使用 PrimeVue v4 元件，或以 PrimeVue 元件為基礎的自訂封裝。禁止使用原生 HTML 表單元素（`<button>`、`<input>`、`<select>`、`<textarea>`），除非 PrimeVue 沒有對應元件且無法合理封裝。

## 路由

| Path | View | 說明 |
|------|------|------|
| `/` | HomeView | 全部卡組列表 |
| `/sets/:productType` | HomeView (same) | 依產品類型篩選 |
| `/set/:setId` | SetView (lazy) | 卡組內的卡片列表 |
| `/search?q=&...` | SearchView (lazy) | 搜尋結果 |

## Pinia Stores

**useCardSetsStore** — 資料存取層
- `productTypes`, `sets`, `currentSet`, `loading`
- `loadProductTypes()`, `loadSets(pt?)`, `loadSet(setId)` — 呼叫 api/*.ts
- `patchVariantOwnership(cardId, rarity, count)` — 即時更新 `currentSet.cards` 中對應 variant 的 `owned_count`（側邊欄調整數量後呼叫）
- `updateCardInSet(updated: Card)` — 以 `Object.assign` 將側邊欄重新載入的 card 物件同步回 `currentSet.cards`（編輯/圖片上傳後呼叫）

**useUiStore** — UI 狀態
- `viewMode: 'grid' | 'table'` — Grid/Table 切換
- `sidebarOpen`, `sidebarCardId`, `sidebarRarity` — 側邊欄
- `sidebarMode: 'detail' | 'create'` — 側邊欄模式 (檢視/建立)
- `sidebarCreateSetId: string | null` — 建立模式的目標 set_id
- `openSidebar(cardId, rarity?)`, `closeSidebar()` — 任何元件都能呼叫
- `openCreateSidebar(setId)` — 開啟建立模式

## API 層

```
api/client.ts      → axios instance, baseURL: '/api', timeout: 30s
api/cardSets.ts    → fetchProductTypes, fetchCardSets, fetchCardSet, fetchSetStats,
                     updateCardSet, fetchCardSetOverrides, deleteCardSetOverride
api/cards.ts       → fetchCard, updateCard, updateOwnership, searchCards, getCardImageUrl,
                     uploadCardImage, revertCardImage, getNextCardId, createCard, addVariant,
                     editVariantRarity, deleteVariant
```

## 元件分類

### Layout — 全域 UI
- `AppHeader`: Logo + 搜尋框 (submit → router.push /search) + Browse/Search nav
- `BreadcrumbBar`: 接收 `items: {label, to?}[]` 渲染麵包屑
- `ViewToggle`: 直接讀寫 `ui.viewMode`

### Navigation — 首頁
- `ProductTypeSidebar`: 可收合左側導覽欄（200px 展開 / 36px 收合），依 display_name 關鍵字分組（補充包系列/構築/活動/其他），使用 PrimeVue Button 切換
- `ProductTypeNav`: pill 列（舊版，仍保留但 HomeView 已改用 Sidebar）
- `SetList`: 卡組 grid cards，router-link 到 `/set/{id}`

### Cards — 卡片顯示 (Grid/Table 共用子元件)
- `CardGrid`: `auto-fill minmax(190px,1fr)` grid，container 為 `max-w-screen-2xl`
- `CardGridItem`: 圖片 grid item
  - **佈局（上→下）**: 完整卡牌編號 + 複製按鈕（卡圖上方）→ 卡圖 → 卡名 → card_type → RarityTabs（靠右獨立行，`@click.stop`）→ OwnershipControl
  - **fullCardId**: `card_id` 含 `/` 時直接用（如 `RD/23PR-JP001`）；否則補 `RD/{set_id}-{card_id}`
  - 未持有灰階；user_upload 圖 URL 加 `?t=1` cache buster
  - 選中時 yellow-400 ring；scrollIntoView 延遲 520ms（等 layout transition）
- `CardTable`: 表格行，未持有半透明
- `RarityTabs`: 多稀有度 tab 切換，各稀有度有對應色碼
- `OwnershipBadge`: 持有數 badge (綠色/灰色)
- `OwnershipControl`: `[−] 0 [+]` 按鈕（縮小版 w-5 h-5），樂觀更新 + emit event

### Detail — 側邊欄 & 卡組編輯
- `AppSidebar`: Teleport to body，backdrop + panel，Esc 關閉；根據 `ui.sidebarMode` 切換 detail/create 模式
  - **收起/展開 tab**: 兩個狀態皆固定在 `fixed top-1/2 right-0 z-[60]`（不在 aside 內部），位置不跳動
  - **Layout transition**: `main` 加 `sm:pr-[28rem]` transition 500ms ease-in-out
- `CardDetailPanel`: 大圖 + info table + effect text + **inline 編輯模式** + variant 管理列 (非編輯模式下顯示)
  - **Add Variant**: 展開 inline dropdown，選擇尚未存在的貴罕度
  - **Edit Rarity**: 展開 inline dropdown，修改當前 rarity；呼叫 `PATCH /api/cards/{id}/variants/{rarity}`
  - **Delete** (只有 >1 variant 時顯示): 確認後刪除；呼叫 `DELETE /api/cards/{id}/variants/{rarity}`
  - 貴罕度選項從 `src/constants/rarities.ts` 讀取，顯示中文標籤
- `CardCreatePanel`: 建立新卡片表單 (card_id 自動生成 + 可編輯, rarity dropdown, card_type dropdown, 怪獸欄位條件顯示)
- `SetMetadataEditor`: 卡組 metadata inline 編輯，嵌入 SetView header
  - View mode: 顯示中文/日文名 + meta tags (set_id, release_date, card count)
  - Edit mode: 表單可修改 set_name_zh, set_name_jp, product_type, release_date, total_cards, rarity_distribution
  - 儲存時自動建立 override (防止匯入覆蓋)，已有 override 的欄位顯示黃色圖示
  - 可展開查看/刪除 override (恢復 scraper 值)
  - `@updated` → SetView 重新 `loadAll()` 刷新資料
  - **卡圖上傳**: 大圖 hover 顯示 overlay，點擊選擇檔案上傳替換；user_upload 時顯示「Revert to original」按鈕
  - **Cache buster**: user_upload 圖 URL 加 `?t=...`，上傳/還原後 `imageCacheBuster = Date.now()` 強制重載
  - Card Type: 下拉選單 (所有簡單 + 複合類型)
  - 怪獸專屬欄位 (Attribute, Race, Level, ATK, DEF, Summon Condition): 僅在選擇怪獸類型時顯示
  - 文字欄位 (Summon Condition, Condition, Effect, Continuous Effect): 無值時收合為 `+` 按鈕，點擊展開
  - 編輯直接在原本的顯示欄位上操作，不再跳轉到獨立表單

### Search
- `SearchFilters`: 5 個 select 下拉，emit change event

## 資料更新模式

**持有數**:
1. `OwnershipControl` 的 `[+]` → `localCount++` + `emit('update', cardId, rarity, count)`
2. 父元件 (CardGridItem/CardTable) → `PATCH /api/ownership/...` + 更新本地 `variant.owned_count`
3. → `emit('ownershipChanged')` → SetView 重新 `fetchSetStats()` 更新進度條

**卡片編輯**:
1. `CardDetailPanel` inline 編輯模式 → `PATCH /api/cards/...`
2. → `emit('cardUpdated')` → `AppSidebar` 重新 `fetchCard()` 更新顯示，並呼叫 `cardSetsStore.updateCardInSet()` 同步 card grid
3. 編輯時 `isMonster` computed 動態顯示/隱藏怪獸專屬欄位；`isMaximum` computed 顯示/隱藏 MAXIMUM ATK 欄位
4. `expandedSections` reactive 控制空白文字欄位的展開/收合

**卡組 metadata 編輯**:
1. `SetMetadataEditor` 的 Edit 按鈕 → 展開 inline 表單
2. Save → `PATCH /api/card-sets/{set_id}` (自動建立 override)
3. → `emit('updated')` → `SetView` 重新 `loadAll()` 刷新全部資料
4. Override 管理: 展開可見 active overrides，可逐一刪除恢復 scraper 值

**卡片建立**:
1. `SetView` header 的 **Add Card** 按鈕 → `ui.openCreateSidebar(setId)`
2. `AppSidebar` 根據 `ui.sidebarMode === 'create'` 顯示 `CardCreatePanel`
3. 表單: card_id (自動生成 via `getNextCardId()` + 可編輯), rarity (dropdown), card_type (dropdown)
4. Submit → `POST /api/cards` → `emit('cardCreated')` → `AppSidebar` 關閉 sidebar
5. `SetView` watch `ui.sidebarOpen` → 關閉時重新 `loadAll()` 刷新卡片列表
6. 建立的卡片 `is_manual=True`，匯入時不會被覆蓋

**新增稀有度 variant**:
1. `CardDetailPanel` rarity tabs 下方有 **+ Add Variant** 按鈕 (非 editing 模式時顯示)
2. 點擊展開 inline dropdown: 僅顯示尚未存在的稀有度（從 `constants/rarities.ts` 過濾）
3. Add → `POST /api/cards/{card_id}/variants` → 切換到新 rarity tab → `emit('cardUpdated')`

**編輯 / 刪除 variant 貴罕度**:
1. `CardDetailPanel` 同一行顯示 **Edit Rarity** 和 **Delete** 按鈕（只有 >1 variant 時顯示 Delete）
2. Edit Rarity → 展開 inline dropdown 選新 rarity → `PATCH /api/cards/{id}/variants/{old}` → 更新 currentRarity → `emit('cardUpdated')`
3. Delete → 顯示確認提示 → `DELETE /api/cards/{id}/variants/{rarity}` → 切換到其他 rarity → `emit('cardUpdated')`
