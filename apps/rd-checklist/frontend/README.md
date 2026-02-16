# rd-checklist Frontend

Vue 3 + TypeScript + Tailwind CSS 前端，深色主題卡牌收藏管理介面。

## 元件架構

```
App.vue
├── AppHeader              # 頂部導航 (Logo + 搜尋框 + Browse/Search)
├── <RouterView>
│   ├── HomeView           # / 和 /sets/:productType
│   │   ├── BreadcrumbBar
│   │   ├── ProductTypeNav # 產品類型 pill 篩選列
│   │   └── SetList        # 卡組 grid (set_id, 名稱, 日期, 卡數)
│   │
│   ├── SetView            # /set/:setId
│   │   ├── BreadcrumbBar
│   │   ├── SetMetadataEditor  # 卡組 metadata 顯示/編輯 + override 管理
│   │   ├── ViewToggle     # Grid ↔ Table 切換
│   │   ├── CardGrid       # Grid 模式
│   │   │   └── CardGridItem × N
│   │   │       ├── OwnershipBadge  (右上角)
│   │   │       ├── RarityTabs      (多稀有度切換)
│   │   │       └── OwnershipControl ([ - 0 + ])
│   │   └── CardTable      # Table 模式 (同樣的子元件)
│   │
│   └── SearchView         # /search?q=
│       ├── SearchFilters  # 類型/屬性/等級/稀有度/持有 下拉
│       ├── ViewToggle
│       └── CardGrid / CardTable
│
└── AppSidebar (Teleport)  # 條件: ui.sidebarOpen
    └── CardDetailPanel    # 大圖 + 完整資訊 + 效果
        └── CardEditForm   # 條件: showEditForm
```

## 狀態管理

```
┌──────────────────────────────────┐    ┌─────────────────────────┐
│ useCardSetsStore                 │    │ useUiStore              │
│                                  │    │                         │
│ productTypes: ProductType[]      │    │ viewMode: 'grid'|'table'│
│ sets: CardSet[]                  │    │ sidebarOpen: boolean    │
│ currentSet: CardSetWithCards     │    │ sidebarCardId: string   │
│ loading: boolean                 │    │ sidebarRarity: string   │
│                                  │    │                         │
│ loadProductTypes()               │    │ openSidebar(id, rarity) │
│ loadSets(productType?)           │    │ closeSidebar()          │
│ loadSet(setId)                   │    │ toggleView()            │
└──────────────────────────────────┘    └─────────────────────────┘
```

## 資料流

```
元件 ──呼叫──▶ api/*.ts ──axios──▶ /api/* ──proxy──▶ Backend :8000
  ▲                                                       │
  └───────────────── JSON response ◀──────────────────────┘

持有數更新:
  OwnershipControl [+] → emit('update') → CardGridItem
    → PATCH /api/ownership/{id}/{rarity} (async)
    → 更新本地 variant.owned_count (樂觀更新)
    → emit('ownershipChanged') → SetView.loadStats() (進度條更新)
```

## 視覺設計

- **深色主題**: bg-gray-950 基底，gray-900 卡片，yellow-400 強調色
- **未持有卡片**: grayscale + opacity-40 (Grid), opacity-40 整行 (Table)
- **稀有度色碼**: UR=金, SER=紅, SR=橙, R=藍, N=灰, OVER-RUSH=紫, RUSH=青
- **LEGEND 標記**: amber-500 badge

## 指令

```bash
npm install
npm run dev          # 開發 (http://localhost:5173, proxy /api → :8000)
npm run build        # 建置
npm run type-check   # TypeScript 檢查
```
