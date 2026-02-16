---
name: rd-checklist-frontend-arch
description: Vue 3 frontend architecture for rd-checklist (components, Pinia stores, routing). Use when adding/modifying components, debugging UI behavior, understanding data flow between views and API, or changing view structure.
---

# Checklist App 前端架構

**何時讀此 SKILL**：加/改元件、debug UI、改 store 或路由、理解元件層級與 emit 流程。

Vue 3 (Composition API) + TypeScript + Tailwind CSS + Pinia + Vue Router。

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

**useUiStore** — UI 狀態
- `viewMode: 'grid' | 'table'` — Grid/Table 切換
- `sidebarOpen`, `sidebarCardId`, `sidebarRarity` — 側邊欄
- `openSidebar(cardId, rarity?)`, `closeSidebar()` — 任何元件都能呼叫

## API 層

```
api/client.ts      → axios instance, baseURL: '/api', timeout: 30s
api/cardSets.ts    → fetchProductTypes, fetchCardSets, fetchCardSet, fetchSetStats,
                     updateCardSet, fetchCardSetOverrides, deleteCardSetOverride
api/cards.ts       → fetchCard, updateCard, updateOwnership, searchCards, getCardImageUrl,
                     uploadCardImage, revertCardImage
```

## 元件分類

### Layout — 全域 UI
- `AppHeader`: Logo + 搜尋框 (submit → router.push /search) + Browse/Search nav
- `BreadcrumbBar`: 接收 `items: {label, to?}[]` 渲染麵包屑
- `ViewToggle`: 直接讀寫 `ui.viewMode`

### Navigation — 首頁
- `ProductTypeNav`: pill 列，router-link 到 `/sets/{type}`
- `SetList`: 卡組 grid cards，router-link 到 `/set/{id}`

### Cards — 卡片顯示 (Grid/Table 共用子元件)
- `CardGrid` / `CardGridItem`: 圖片 grid，未持有灰階；user_upload 圖 URL 加 `?t=1` cache buster
- `CardTable`: 表格行，未持有半透明
- `RarityTabs`: 多稀有度 tab 切換，各稀有度有對應色碼
- `OwnershipBadge`: 持有數 badge (綠色/灰色)
- `OwnershipControl`: `[-] 0 [+]` 按鈕，樂觀更新 + emit event

### Detail — 側邊欄 & 卡組編輯
- `AppSidebar`: Teleport to body，backdrop + panel，Esc 關閉
- `CardDetailPanel`: 大圖 + info table + effect text + **inline 編輯模式** (取代獨立的 CardEditForm)
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
2. → `emit('cardUpdated')` → `AppSidebar` 重新 `fetchCard()` 更新顯示
3. 編輯時 `isMonster` computed 動態顯示/隱藏怪獸專屬欄位
4. `expandedSections` reactive 控制空白文字欄位的展開/收合

**卡組 metadata 編輯**:
1. `SetMetadataEditor` 的 Edit 按鈕 → 展開 inline 表單
2. Save → `PATCH /api/card-sets/{set_id}` (自動建立 override)
3. → `emit('updated')` → `SetView` 重新 `loadAll()` 刷新全部資料
4. Override 管理: 展開可見 active overrides，可逐一刪除恢復 scraper 值
