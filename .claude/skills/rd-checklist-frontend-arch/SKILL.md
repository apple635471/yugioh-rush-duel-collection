---
name: rd-checklist-frontend-arch
description: Frontend component architecture and state management for the rd-checklist Vue app. Use when adding new components, modifying views, or debugging UI behavior.
---

# Checklist App 前端架構

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
api/cardSets.ts    → fetchProductTypes, fetchCardSets, fetchCardSet, fetchSetStats
api/cards.ts       → fetchCard, updateCard, updateOwnership, searchCards, getCardImageUrl
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
- `CardGrid` / `CardGridItem`: 圖片 grid，未持有灰階
- `CardTable`: 表格行，未持有半透明
- `RarityTabs`: 多稀有度 tab 切換，各稀有度有對應色碼
- `OwnershipBadge`: 持有數 badge (綠色/灰色)
- `OwnershipControl`: `[-] 0 [+]` 按鈕，樂觀更新 + emit event

### Detail — 側邊欄
- `AppSidebar`: Teleport to body，backdrop + panel，Esc 關閉
- `CardDetailPanel`: 大圖 + info table + effect text + **inline 編輯模式** (取代獨立的 CardEditForm)
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
