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

**★ 文字對比規則**（底色 `#09090F` 幾乎純黑，Tailwind 的中階灰在這裡會暗一階）：
- 次要文字用 `text-gray-400`；**不要**用 `text-gray-500` / `text-gray-600` 當文字色（4.11 / 2.27:1，低於 WCAG AA 小字要求的 4.5:1）
- 金色文字用 `text-gold`；`gold-dim` 是裝飾色（邊框、進度條漸層起點），當文字只有 2.76:1
- chip／badge 這種自帶底色的元素，文字要再提一階（如 `bg-gray-700` 配 `text-gray-200`）
- `--color-dark-3` = `#262B3D`（原 `#181B28`），讓 badge 這類小面積底色和文字拉開
- 例外：`disabled` 控制項維持低對比（狀態訊號，WCAG 不要求）

- CSS layer 順序 (main.css)：`@layer tailwind-base, primevue, tailwind-utilities`
  - Tailwind utilities 永遠覆蓋 PrimeVue 預設樣式
- 使用元件：`Button`、`InputText`、`InputNumber`、`Select`（種族用 `editable`）、`Slider`（Level / ATK / DEF 拉桿）、`Textarea`、`Checkbox`、`SelectButton`、`IftaLabel`（篩選下拉的欄位內頂端標籤）
- 卡片 stat 欄位共用元件 `components/detail/StatInput.vue`（ATK/DEF/MAX：允許 `?` 的文字輸入 + step-100 拉桿）；驗證工具 `utils/cardFields.ts`（`isStatValid` / `isLevelValid`）
- 效果文字內卡名引用：`CardRefText`（解析「」/『』→ hover 浮動預覽 + 點擊開 modal）、`CardBasicInfo`（唯讀卡片摘要，共用於預覽與 modal）、`CardRefModal`（Dialog，左側同名卡編號清單）；查詢用 `searchCardsByName()`（`api/cards.ts`，走 `exact`）
- Button severity 規範：`warn` = 主要操作（amber）、`secondary` = 次要、`danger` = 刪除、`success` = 完成
- Button variant 規範：(無) = 實心、`outlined` = 外框、`text` = 無背景
- **共用 action 按鈕 `components/ui/AppButton.vue`**：封裝 PrimeVue `Button`，固定尺寸避免同一列按鈕高度不一
  - props：`label` / `variant`（`filled` | `outlined`（預設） | `text`）/ `severity`（PrimeVue 語意色，預設 `secondary`）/ `tone`（App 自訂色票，目前只有 `gold`，給了就覆蓋 `severity`）/ `size`（`sm`=24px、`md`=32px（預設）、`lg`=40px）/ `iconOnly`（正方形）/ `fluid`（撐滿寬度）/ `disabled`
  - slots：預設 slot = 文字（優先於 `label`）；`#icon` = 圖示，svg 由元件依 size 統一縮成 12/14/16px，不用自己標 `w-3.5 h-3.5`
  - **`fluid` 會改用 `flex-1 min-w-0`（不是 `shrink-0`）**：兩顆並排的 fluid 按鈕各要 100% 寬，不能壓縮就會把後面那顆擠出容器
  - **字級可被個別覆寫**：元件用 `--app-button-font`（`main.css` 的 `.app-button` 未分層規則讀取），呼叫端加 `!text-sm` 之類的 class 就能蓋掉。`!important` 在 CSS layer 內的優先順序是**反過來的**，所以元件不能用 `!text-xs` 當預設，否則呼叫端怎麼加都蓋不掉
  - `tone` 的樣式寫在元件的 scoped `<style>`（未進 `@layer`，優先度高於 primevue layer）；要加新色票就在那裡加 `.app-button--{tone}-{variant}`
  - 工具列上與按鈕並排的 `SelectButton`（如 `ViewToggle`）加 `app-toolbar-toggle` class，`main.css` 有對應規則把 `.p-togglebutton` 拉成 2rem 對齊
  - **不套用**：卡圖上的浮動 overlay 按鈕、`OwnershipControl` 的 ±、`RarityTabs` 分頁、側邊欄收合把手 —— 定位／形狀特殊，不是一般 action 按鈕

**★ PrimeVue 優先原則**：所有互動式元素（按鈕、輸入框、下拉選單、彈窗等）必須優先使用 PrimeVue v4 元件，或以 PrimeVue 元件為基礎的自訂封裝。禁止使用原生 HTML 表單元素（`<button>`、`<input>`、`<select>`、`<textarea>`），除非 PrimeVue 沒有對應元件且無法合理封裝。

## 路由

| Path | View | 說明 |
|------|------|------|
| `/` | HomeView | 全部卡組列表 |
| `/sets/:productType` | HomeView (same) | 依產品類型篩選 |
| `/set/:setId` | SetView (lazy) | 卡組內的卡片列表；含顯示模式/進度模式切換、貴罕度+卡種篩選（選項僅列該 set 實際出現者）、雙模式進度條（前端由 `cards` 即時計算，隨 owned_count 變動更新）|
| `/search?q=&...` | SearchView (lazy) | 搜尋結果 |

## Pinia Stores

**useCardSetsStore** — 資料存取層
- `productTypes`, `sets`, `currentSet`, `loading`
- `loadProductTypes()`, `loadSets(pt?)`, `loadSet(setId)` — 呼叫 api/*.ts
- `patchVariantOwnership(cardId, rarity, count)` — 即時更新 `currentSet.cards` 中對應 variant 的 `owned_count`（側邊欄調整數量後呼叫）
- `updateCardInSet(updated: Card)` — 以 `Object.assign` 將側邊欄重新載入的 card 物件同步回 `currentSet.cards`（編輯/圖片上傳後呼叫）

**useUiStore** — UI 狀態
- `viewMode: 'grid' | 'table'` — 卡組頁的卡片 Grid/Table 切換
- `setViewMode: 'card' | 'timeline'` — 首頁卡組清單的呈現方式（卡片牆／時間軸）
- `displayMode: 'owned' | 'highest'` — SetView 預設 variant 選取模式（`owned`=擁有優先、`highest`=一律最高；預設 `owned`）
- `progressMode: 'standard' | 'net'` — SetView 進度條模式（`standard`=全部 variant、`net`=排除異圖與 SER；預設 `net`）
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

### UI — 共用基礎元件
- `ui/AppButton`: 全站 action 按鈕（見上方「UI 元件庫」）。新增按鈕優先用它，不要再自刻原生 `<button>` 或各自指定 `size`

### Layout — 全域 UI
- `AppHeader`: Logo + 搜尋框 (submit → router.push /search) + Browse/Search nav
- `BreadcrumbBar`: 接收 `items: {label, to?}[]` 渲染麵包屑
- `ViewToggle`: 直接讀寫 `ui.viewMode`；`SelectButton` 帶 `app-toolbar-toggle` class 以對齊 `AppButton` 高度

### Navigation — 首頁
- `ProductTypeSidebar`: 可收合左側導覽欄（200px 展開 / 36px 收合），使用 PrimeVue Button 切換
  - 分組寫在元件內的 `SECTIONS` 常數，**用 `product_type` 明列**（不是比對 display_name）：`補充包系列` = booster / advanced_pack / maximum_pack / over_rush_pack / legend_pack / triple_build_pack；`預組` = structure_deck；`其他` = battle_pack / promo / other
  - 組內順序就是 `SECTIONS` 裡的順序；沒列到的新類型自動落在最後一組，不會憑空消失
  - 每個項目英文名一行、`display_name_zh` 另起一行（見 `rd-product-types`）
- `ProductTypeNav`: pill 列（舊版，仍保留但 HomeView 已改用 Sidebar）
- `SetList`: 卡組 grid cards，router-link 到 `/set/{id}`
  - hover 時顯示該卡組的圖片（Teleport 到 body 的浮動視窗，卡片本身 `overflow-hidden` 會裁掉）。每個卡組只查一次 API 就快取；進場延遲 120ms，滑過一整排不會每張都打；沒有圖就不彈視窗
- `SetViewToggle`: 讀寫 `ui.setViewMode`，卡片牆 ↔ 時間軸；與 `ViewToggle` 一樣帶 `app-toolbar-toggle` class
- `SetTimeline`: 時間軸視圖，資料來自 `GET /api/card-sets/timeline`（`HomeView` 切到時間軸才載入，同一個產品線不重載）
  - 顏色帶產品類型（`constants/productTypes.ts` 的 `PRODUCT_TYPE_THEME` → CSS 變數 `--c`）：節點、邊條、箭頭、貴罕度標籤、進度條同色
  - 盒高固定 228px、`.tl-row + .tl-row { margin-top: -98px }` → 列距 130px，異側咬合、同側留 32px；`.tl-box` 的 `overflow` 必須是 `visible`，否則指向軸線的箭頭（`::after` 三角形）會被裁掉，圓角改由各子元素自己處理
  - 盒高固定，所以 `.tl-main > *` 一律 `flex-shrink: 0`，剩餘高度全給卡圖列（否則標題會被壓成半截）
  - < 1100px 時放棄交錯：軸線靠左、卡組一律排右邊、盒高改 auto

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
- `SetGalleryStrip`: 卡組圖片的固定長寬瀏覽窗（240×82），**絕對定位掛在按鈕列左側**（`right-full`），所以不論幾張圖都不會推開標題、中日文名或卡片列表；超出就橫向捲動，點擊開大圖
  - 這個排版限制是刻意的：實測有／無縮圖窗時卡片列表的 top 都是同一個值
- `SetListCompareDialog`: 對照 yugipedia 卡表（`SetView` header 最左邊的按鈕開啟）。輸入卡組頁網址 → 比對 → 兩份可勾選清單（缺少 / 多出），一鍵建立或刪除；多出的項目會標示持有數與「刪掉整張卡」警告
  - `SetMetadataEditor` 為此新增 `#actions-left` slot（Edit 按鈕左邊）
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
- `SearchFilters`: 7 個 select 下拉（卡種／屬性／種族／等級／貴罕度／Legend／持有），emit change event
  - 種族選項來自 `constants/monsterTypes.ts`，與 `CardDetailPanel` / `CardCreatePanel` 編輯卡牌時同一份清單

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
