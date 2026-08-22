# rd-checklist Frontend

Vue 3 + TypeScript + Tailwind CSS + **PrimeVue v4** 前端，深色主題卡牌收藏管理介面。

## 元件架構

```
App.vue
├── AppHeader              # 頂部導航 (Logo + 搜尋框 + Browse/Search)
├── <RouterView>
│   ├── HomeView           # / 和 /sets/:productType  (新增卡組 → AppButton)
│   │   ├── BreadcrumbBar
│   │   ├── ProductTypeSidebar # 左側導覽欄，SECTIONS 常數以 product_type 明列分組
│   │   │                      #   (補充包系列 / 預組 / 其他)，中文名另起一行
│   │   ├── ProductTypeNav # 產品類型 pill 篩選列 (舊版，仍保留)
│   │   └── SetList        # 卡組 grid (set_id, 名稱, 日期, 卡數)
│   │
│   ├── SetView            # /set/:setId
│   │   ├── BreadcrumbBar
│   │   ├── SetMetadataEditor  # 卡組 metadata 顯示/編輯 + override 管理
│   │   │   └── #actions-left slot → SetListCompareDialog 觸發鈕（對照 yugipedia 卡表）
│   │   │   └── AppButton  # 共用 action 按鈕 (Edit)
│   │   ├── AppButton      # Add Card
│   │   ├── ViewToggle     # Grid ↔ Table 切換 (高度對齊 AppButton md)
│   │   ├── CardGrid       # Grid 模式 (auto-fill minmax(190px,1fr))
│   │   │   └── CardGridItem × N
│   │   │       ├── 完整卡牌編號列 + 複製按鈕  (卡圖上方)
│   │   │       ├── OwnershipBadge  (卡圖右上角 overlay)
│   │   │       ├── 卡名 / card_type
│   │   │       ├── RarityTabs      (獨立一行靠右；click.stop 不觸發側邊欄)
│   │   │       └── OwnershipControl ([ − 0 + ]，縮小版)
│   │   └── CardTable      # Table 模式 (同樣的子元件)
│   │
│   └── SearchView         # /search?q=
│       ├── SearchFilters  # 卡種/屬性/種族/等級/貴罕度/Legend/持有 下拉 (清除篩選 → AppButton)
│       ├── ViewToggle
│       └── CardGrid / CardTable
│
└── AppSidebar (Teleport)  # 條件: ui.sidebarOpen
    ├── CardDetailPanel    # ui.sidebarMode='detail': 大圖 + 完整資訊 + 效果 + Add Variant
    │                       #   貴罕度工具列 icon 鈕 / 同名卡片 (tone=gold) / 底部動作皆用 AppButton
    │   └── ScanResultPanel (Teleport, 浮動可拖曳)  # ✦ Scan 按鈕觸發，顯示 AI 掃描結果剪貼板
    ├── CardCreatePanel    # ui.sidebarMode='create': 新卡建立表單
    └── 收起/展開 tab      # fixed top-1/2 right-0，兩狀態同位置
```

## 狀態管理

```
┌──────────────────────────────────┐    ┌──────────────────────────────┐
│ useCardSetsStore                 │    │ useUiStore                   │
│                                  │    │                              │
│ productTypes: ProductType[]      │    │ viewMode: 'grid'|'table'     │
│ sets: CardSet[]                  │    │ sidebarOpen: boolean         │
│ currentSet: CardSetWithCards     │    │ sidebarCardId: string        │
│ loading: boolean                 │    │ sidebarRarity: string        │
│                                  │    │ sidebarMode: 'detail'|'create│
│ loadProductTypes()               │    │ sidebarCreateSetId: string   │
│ loadSets(productType?)           │    │                              │
│ loadSet(setId)                   │    │ openSidebar(id, rarity)      │
└──────────────────────────────────┘    │ openCreateSidebar(setId)     │
                                        │ closeSidebar() / toggleView()│
                                        └──────────────────────────────┘
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

## UI 元件庫

**PrimeVue v4** (`primevue@^4.5.4` + `@primeuix/themes`)
- 主題：Aura Dark，primary palette 客製為 amber（配合 yellow-400/500 系設計語言）
- `darkModeSelector: ':root'` 全域強制深色模式
- CSS layer 順序：`tailwind-base → primevue → tailwind-utilities`（Tailwind 優先覆蓋）
- 使用元件：`Button`、`InputText`、`InputNumber`、`Select`、`Textarea`、`Checkbox`、`SelectButton`

## 視覺設計

- **深色主題**: bg-gray-950 基底，gray-900 卡片，yellow-400 強調色
- **文字色規則**（所有文字須 ≥ 4.5:1）
  - 次要／輔助文字一律 `text-gray-400`（#99A1AF，在 #09090F 上 7.63:1）；`text-gray-500` / `text-gray-600` 在這個近黑底上不足 4.5:1，不要當文字色用
  - 金色文字用 `text-gold`（#C9A84C）；`gold-dim`（#6B5428）是**裝飾色**，只給邊框與進度條漸層，不當文字色
  - 有底色的 chip／badge 要再提一階（例如 `bg-gray-700` 上用 `text-gray-200`）
  - 例外：`disabled` 控制項（如數量 −）維持低對比，那是狀態訊號，WCAG 也不要求
- **左側導覽欄**: `bg-dark-1` + 右側 `rgba(201,168,76,0.10)` 細邊，與內容區分層
- **未持有卡片**: grayscale + opacity-40 (Grid), opacity-40 整行 (Table)
- **稀有度色碼**: UR=金, SER=紅, SR=橙, R=藍, N=灰, OVER-RUSH=紫, RUSH=青
- **LEGEND 標記**: amber-500 badge
- **Grid 容器**: `max-w-screen-2xl`（1536px），`auto-fill minmax(190px,1fr)`
- **側邊欄 layout**: 開啟時主容器加 `sm:pr-[28rem]`（transition 500ms ease-in-out）

## 指令

```bash
npm install
npm run dev          # 開發 (http://localhost:5173, proxy /api → :8000)
npm run build        # 建置
npm run type-check   # TypeScript 檢查
```
