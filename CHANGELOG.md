# Changelog

## v0.9.5 (2026-03-24)

### 修正

- **Fetch Konami 抓到卡背 SAMPLE / 舊 rarity 問題**：
  - 修正更改 rarity 後「Fetch Konami」仍用舊 rarity 組 URL 的 bug（`submitEditRarity` 時同步更新 `ui.sidebarRarity`）
  - 修正 Konami CDN URL 稀有度尾綴對應：N→無尾綴, R→`_r`, RR→`_rr`, SR→`_sr`, UR→`_ur`, UPR→`_urp`, SER→`_se`, FORR→`_for`；未知 rarity 不猜，直接進備案
  - 新增 Rush DB 備案機制：CDN 404 時以 `stype=4` 搜尋 card number 取得 cid/ciid/enc，依 rarity 對應尾綴優先嘗試所有已知 CDN 尾綴（CDN 高畫質）；全部 404 才使用 `get_image.action` 作最終手段

### 改善

- **卡組列表排序**：改為依發售日期新到舊排列（`printf('%04d%02d',year,month)` 避免單位數月份排序錯誤）；無日期的卡組排到最後再依 set_id 排序
- **產品類型名稱統一**：前後端全面改為「English (中文)」格式（例：`Booster Pack (補充包)`、`Promo (Promo)`），側欄顯示名稱、下拉選單、後端 `PRODUCT_TYPE_LABELS` 三者一致
- **新增 / 編輯卡組對話框產品類型選項統一**：共用 `src/constants/productTypes.ts`，選項完整且格式一致
- **Total Cards / Rarity Distribution 改為自動計算**：`SetMetadataEditor` 不再允許手動編輯，從 `cardSet.cards` 即時計算；後端 `CardSetUpdate` schema 與前端型別移除這兩個欄位

---

## v0.9.4 (2026-03-24)

### 新增

- **側欄「前往所屬卡組」按鈕**：在非該卡所屬卡組頁面開啟側欄時（例如搜尋、篩選結果），卡片 ID 列旁顯示卡組 ID 按鈕，點擊可將主頁面導向至 `/set/{set_id}`，方便確認卡牌歸屬

---

## v0.9.3 (2026-03-22)

### 修正

- **AppSidebar 錯誤訊息顯示**：卡片載入失敗時顯示實際錯誤原因（HTTP 狀態碼 / 後端 detail），並透過 `console.error` 輸出詳細錯誤，方便除錯
- **`GET /api/card-sets/{id}` 回應補 `is_manual` 欄位**：原先手動建立的卡組在 `CardSetWithCardsOut` 中 `is_manual` 永遠回傳 `false`，現已修正

### 新增

- **手動新增卡組**：首頁標題右側加入「新增卡組」按鈕，可透過 Dialog 建立任意 set_id 的卡組
  - 支援填寫中文名稱、日文名稱、產品類型（預設「其他 / Promo」）、發售日期
  - 建立後自動跳轉至該卡組頁面
  - 手動卡組標記 `is_manual=True`，匯入時完全跳過，不會被 scraper 資料覆蓋
  - 後端新增 `POST /api/card-sets` 端點（409 防重複）
  - DB 新增 `card_sets.is_manual` 欄位（auto-migration）
- **新產品類型「其他 / Promo」**（`other`）：對應書卡、Promo 等非包裝發行的卡組，顯示於側欄「其他」分類

---

## v0.9.2 (2026-03-21)

### 新增

- **從 Konami CDN 一鍵抓圖**：CardDetailPanel 圖片區新增「Fetch from Konami」按鈕（雲端上傳 icon，位於 Scan 按鈕左側）
  - 點擊後自動組出 Konami CDN URL：`https://img.konami.com/yugioh/rushduel/products/{set}/cards/{num}_{rarity}.jpg`
  - 稀有度名稱對應：`UPR→urp`、`SER→se`、`FORR→for`，其他直接小寫
  - 找到圖片則自動儲存為 user upload（等同手動上傳）；找不到則顯示提示訊息
  - 後端新增 `POST /api/images/card/{card_id}/{rarity}/fetch-konami` 端點
  - 新增 `httpx` 依賴（async HTTP client）

---

## v0.9.1 (2026-03-21)

### 改善

- **CardDetailPanel 版面重設計（v3）**：
  - **Rarity row**：稀有度 pill 按鈕（紫色 active 樣式）+ 分隔線 + icon 按鈕群（Add Variant ⓘ、Edit Rarity 鉛筆、Delete 垃圾桶，含 hover tooltip）+ spacer + 持有數控制；整合原本分散的 RarityTabs、OwnershipControl、variant 管理按鈕成單一橫排
  - **Card ID row**：獨立行顯示卡片編號（monospace），靠右有 `copy` pill 按鈕，點擊後顯示 `copied!`（綠色），1.5 秒後自動復原
  - **ATK / DEF 方塊**：標籤與數字靠左對齊（移除置中），ATK 紅框 `#f87171`、DEF 藍框 `#93c5fd`；MAXIMUM ATK 方塊改為標籤靠左、數值靠右 flex 排列
  - **Info grid**：三欄 grid 取代舊 detail table 的 view mode；Type 佔全寬，屬性／種族／Level 並排三格，每格有小 uppercase label + 數值

---

## v0.9.0 (2026-03-21)

### 新增

- **巨極怪獸 MAXIMUM ATK 欄位**
  - 後端：`cards` 表新增 `maximum_atk TEXT` 欄位，支援 migration（`ALTER TABLE ADD COLUMN` 已存在時跳過）
  - 新增卡片（`CardCreatePanel`）：卡種含「巨極」時顯示 MAX ATK 輸入欄
  - 編輯卡片（`CardDetailPanel`）：同上，編輯表單顯示 MAX ATK 欄位
  - 詳情檢視：ATK/DEF 下方以金色方塊（`border-gold`、Orbitron 字型）展示 MAXIMUM ATK 數值

- **側邊欄編輯即時同步 card grid**
  - 調整持有數（+/-）：card grid 立即變彩色/灰色，不需重整頁面
  - 修改稀有度、上傳/還原圖片、編輯卡片資訊後：card grid 立即反映最新圖片、稀有度 tab 等
  - 實作方式：`cardSetsStore` 新增 `patchVariantOwnership` 與 `updateCardInSet` 兩個 action；`CardDetailPanel` 在 ownership 更新後呼叫前者；`AppSidebar` 在重新載入 card 後呼叫後者

---

## v0.8.0 (2026-03-20)

### 改善

- **首頁側邊欄導覽**：以可收合左側欄（`ProductTypeSidebar`）取代舊有 pill 導覽，依顯示名稱分為「補充包系列」、「構築/預組」、「活動/限定」等分組；使用 PrimeVue Button 控制展開/收合狀態（200px ↔ 36px）；進入卡組頁後自動隱藏
- **首頁全局收集統計**：頁面右上角新增統計面板，顯示套牌包總數、卡片（variant）總數、整體收集百分比；後端新增 `GET /ownership/stats-bulk` 單一 SQL GROUP BY 查詢取得所有套牌統計
- **SetList 進度條**：每張套牌卡片底部加入 owned/total 數字 + 黃金漸層進度條（完成時轉為翠綠色），資料來自新的 `stats-bulk` 批量 API
- **Hover 效果**：套牌卡片 `hover:-translate-y-0.5 shadow-lg`；卡片格圖 `hover:-translate-y-1 scale-[1.02] shadow-xl`
- **卡片詳情面板重設計**：
  - 卡名改用 `Cinzel` 字型，顯示稀有度色彩標籤（N 灰/R 藍/SR 金/RR 紅/UR 紫等，13 種稀有度對應色碼）
  - 怪獸卡顯示 ATK/DEF 大數字方塊（紅框/藍框，Orbitron 字型）
  - 資料表格改為黃金色鍵欄（key column）+ 深色底，Orbitron 標籤
  - 效果文字加上框線樣式區塊
- **文件 / 規範**：`rd-checklist-frontend-arch` SKILL.md 新增 PrimeVue 優先原則（禁止使用原生 HTML 互動元素）

---

## v0.7.1 (2026-03-21)

### 修正

- **修正 import 不覆蓋已存在卡片的 `set_id`**
  - 部落格文章偶爾會交叉引用其他卡組的卡片，導致爬蟲將卡片歸入錯誤的 set
  - `_import_one_card()` 現在只在新建卡時設定 `set_id`；已存在的卡不覆蓋，除非 `--force`
  - 移除 `MRP1/cards.json` 中錯誤收錄的 `RD/MAX1-JP002`、`RD/MAX1-JP003`

---

## v0.7.0 (2026-03-20)

### 改善

- **視覺全面重新設計（黃金深色主題）**
  - 引入 Google Fonts：`Cinzel`（品牌標題）、`Orbitron`（ID/數字/標籤）、`Noto Sans TC`（內文）
  - 建立黃金色系設計 token（`--color-gold: #C9A84C`、`--color-gold-light`、`--color-gold-dim`、`--color-dark-bg: #09090F` 等），透過 Tailwind v4 `@theme` 統一管理
  - `body` 背景改為深邃黑（`#09090F`）搭配細微黃金格線，全局 `background-attachment: fixed`
  - **`AppHeader`**：改用 `Cinzel` 字型品牌名稱，深色背景加黃金邊框，導覽 active 狀態以金色框標示
  - **`ProductTypeNav`**：pill 按鈕改為黃金邊框 / 金色底色 active 樣式
  - **`SetList`**：卡組卡片改用 `bg-surface`（`#181B2A`）+ 黃金半透明邊框，set_id / 日期欄位改為 `Orbitron` 字型，4 欄響應式佈局
  - **`SetView` 進度條**：改為獨立卡片式面板，標題用 `Orbitron uppercase`，數字用金色，進度條改為黃金漸層（`#6B5428 → #EAC96A`），高度加粗（`h-2`）
  - **`CardGridItem`**：卡片背景改用 `bg-surface`，卡號改為 `Orbitron` 金色字型，選中 ring 改為金色
  - **`CardTable`**：表頭改用 `Orbitron` + 金色，列分隔線改為黃金半透明
  - **`AppSidebar`**：側邊欄背景改為 `bg-dark-1`，左側邊框 + 展開/收合 tab 改為黃金邊框樣式

---

## v0.6.0 (2026-03-20)

### 改善

- **前端 UI 元件全面遷移至 PrimeVue v4**
  - 安裝 `primevue@^4.5.4` + `@primeuix/themes`，移除手刻原生 HTML 表單元素
  - 採用 Aura Dark 主題，primary palette 客製為 amber（配合既有黃色系設計語言）
  - `darkModeSelector: ':root'` 全域強制深色模式
  - CSS layer 宣告順序：`tailwind-base → primevue → tailwind-utilities`，確保 Tailwind utility class 永遠優先
  - 替換元件涵蓋：`Button`、`InputText`、`InputNumber`、`Select`、`Textarea`、`Checkbox`、`SelectButton`
  - 受影響元件：`ViewToggle`、`RarityTabs`、`OwnershipControl`、`AppHeader`、`SearchFilters`、`CardDetailPanel`、`CardCreatePanel`、`SetMetadataEditor`、`ScanResultPanel`、`AppSidebar`、`CardGridItem`

---

## v0.5.1 (2026-03-15)

### 改善

- **卡牌掃描器改為兩階段架構**（提升準確度）
  - **Phase 1 — OCR** (`gpt-4o`): 只讀取日文原文，不翻譯，輸出 `raw` 欄位
  - **Phase 2 — 翻譯** (`gpt-4o-mini`): 以 Phase 1 日文為輸入，專注翻譯成繁體中文
  - 兩個模型各司其職，避免「同時看圖又翻譯」造成的混淆
  - Phase 1 / Phase 2 模型可各自透過 API query params 或 CLI flag 覆寫
  - 後端 `POST /api/scan/{card_id}/{rarity}` 新增 `extract_model` / `translate_model` query params
  - 前端 `ScanResultPanel` 新增「繁體中文 / 原始日文」標籤切換，方便人工核對原文

---

## v0.5.0 (2026-03-14)

### 新增

- **AI 卡牌掃描器 (rd-card-scanner)**: 透過 OpenAI gpt-4o Vision 從卡牌圖片萃取資訊並翻譯成繁體中文
  - 新增 `tools/rd-card-scanner/` 工具，含 `scan_card.py` 主程式與 `README.md`
  - 環境用 uv 管理，依賴：`openai>=1.0.0`
  - OPENAI_API_KEY 讀取自專案根目錄 `.env`

- **後端 Scan API** (`POST /api/scan/{card_id}/{rarity}`):
  - 從 DB 讀取已知屬性 / 種族 / 卡牌種類，動態建構 prompt 確保術語一致性
  - 圖片來源優先用 user_upload，否則 fallback scraper 圖
  - 後端 `pyproject.toml` 新增 `openai>=1.0.0` 依賴

- **前端 ScanResultPanel**: 浮動可拖曳剪貼板視窗
  - CardDetailPanel 圖片下方新增 ✦ **Scan** 按鈕
  - 掃描結果顯示所有欄位，每個欄位旁有單獨複製按鈕；底部有「複製全部欄位」按鈕
  - **重整按鈕**：可重新呼叫 gpt-4o 取得新結果（因準確度有限，支援多次掃描）
  - 面板可拖曳移動，使用 Teleport 到 body 避免被側邊欄遮擋

---

## v0.4.2 (2026-03-13)

### 修正

- **卡圖即時更新**: 上傳或還原圖片後，card grid 的卡圖即時反映最新圖片（不再需要重整頁面）
  - UI store 新增 `imageUpdates` map，`CardDetailPanel` 上傳/還原後呼叫 `markImageUpdated`
  - `CardGridItem` 改用動態 timestamp cache buster，取代靜態 `?t=1`

### 新增

- **卡牌描述 (description) 欄位**: `CardDetailPanel` 與 `CardCreatePanel` 的編輯區新增 Description 欄位
  - 有別於 Effect/Condition，用於填寫卡牌的背景介紹文字
  - 後端 DB 新增 `description` 欄位（含 migration），API schema 同步更新

---

## v0.4.1 (2026-03-13)

### 更新

#### 前端 Card Grid UI 改善

- **完整卡牌編號顯示**: CardGridItem 在卡圖上方顯示完整編號（如 `RD/KP02-JP001`），旁邊附複製按鈕（複製成功顯示綠色打勾 1.5 秒）
  - 相容兩種 `card_id` 格式：已含完整路徑（`RD/23PR-JP001`）直接顯示；短形式（`JP001`）自動補上 `RD/{set_id}-`
- **稀有度獨立一行**: RarityTabs 移至資訊區底部靠右顯示；點稀有度 tab 切換卡圖，不再觸發側邊欄開啟（`@click.stop`）
- **OwnershipControl 縮小**: 按鈕 `w-7 h-7 text-base` → `w-5 h-5 text-xs`，減少視覺佔用
- **Grid 容器加寬**: `max-w-7xl` (1280px) → `max-w-screen-2xl` (1536px)，在 1440px+ 螢幕填滿版面
- **Grid 自動填充**: 改用 `auto-fill minmax(190px, 1fr)`，欄數隨視窗寬度自然增減（不硬跳格）

#### 側邊欄互動改善

- **收起／展開按鈕位置統一**: 兩個狀態皆固定在畫面右側垂直正中間（`fixed top-1/2 right-0`），位置不跳動
- **關閉後不捲回頂部**: 選中卡片的 `scrollIntoView` 延遲至 layout transition 完成後（520ms）才執行
- **Layout transition 緩和**: `duration-300` → `duration-500 ease-in-out`，重排動畫更柔和

---

## v0.4.0 (2026-03-07)

### 新增

#### 貴罕度校正與 variant 刪除

- **card_variant_overrides 表**: 新增 DB 表儲存 variant 層級的貴罕度覆寫規則
  - `action="remap"`: 將 scraper 的錯誤貴罕度對應到正確的，reimport 不覆蓋
  - `action="delete"`: 標記已刪除的 variant，reimport 不重建
  - 支援鏈式 remap（A→B 再改 B→C 時，正確追蹤原始 scraper_rarity A→C）
- **Edit Rarity**: `PATCH /api/cards/{card_id}/variants/{rarity}` 修改 variant 貴罕度，自動建立 remap override
- **Delete Variant**: `DELETE /api/cards/{card_id}/variants/{rarity}` 刪除 variant（最後一個不可刪），自動建立 delete override
- **Import 保護**: `_import_one_card()` 在處理每個 rarity 前查詢 `card_variant_overrides`，套用 remap/delete 規則
- **前端 Edit Rarity**: CardDetailPanel 新增「Edit Rarity」按鈕（非編輯模式），展開 inline 下拉選單修改當前貴罕度
- **前端 Delete Variant**: CardDetailPanel 新增「Delete」按鈕，顯示確認提示後刪除（只有一個 variant 時不顯示）
- **貴罕度完整清單**: 新增 `src/constants/rarities.ts`，統一管理 13 種貴罕度（含中文說明）
  - N / NPR / R / SR / SPR / UR / PUR / RUR / SER / RR / ORR / ORRPBV / FORR
- **貴罕度選單中文標籤**: 搜尋、新增 variant、建立卡片的下拉選項改顯示中文標籤（如 `UR (金亮)`）

### 更新

- `api/cards.ts`: 新增 `editVariantRarity()`, `deleteVariant()`
- CardCreatePanel、SearchFilters 改用共用貴罕度常數

---

## v0.3.6 (2026-03-07)

### 更新

#### Scraper：SD01–SD05 連結新增至 MULTI_DECK_URL

- `parser.py` `MULTI_DECK_URL`: 加入 SD01–SD05 文章 URL，使這些多卡組文章在爬取時正確拆分

---

## v0.3.5 (2026-03-07)

### 修復

#### Scraper：預組類型統一、多卡組拆分、x{數字} 解析

- **產品類型統一**: ST、GRD 改歸類為 `structure_deck`（與 SD/SBD 一致），移除 `starter`、`go_rush_deck`
- **多卡組拆分** (`parse_post_multi`): 新增例外 URL 清單，SD0C+SD0D、GRD1+GRD2、ST01+ST02 等文章依 set_id 拆分為各自 CardSet
- **孤立圖片清除**: `_cleanup_orphaned_images()` 在成功儲存 CardSet 後刪除不屬於當前卡組的殘留圖片
- **緊湊格式 x{數字} 支援**: `COMPACT_STATS_RE` 加入 `(?:x\d+)?` 接受數量標記（如「x2 光 5星」）
- **Discovery 驗證改善**: `verify_post_is_card_list` 增加緊湊格式偵測，無完整類型關鍵字的文章也能通過驗證
- **SBD 前綴新增**: `PRODUCT_TYPE_MAP` 加入 `SBD → structure_deck`
- **前端 product_type 下拉**: 移除廢棄的 `starter`、`go_rush_deck`，選項加上中文括號提示

#### Import：自動修正 legacy unknown product_type

- 新增 `_derive_product_type()`：當 JSON 的 `product_type` 為 `"unknown"` 時，從 `set_id` 前綴自動推導正確類型

---

## v0.3.4 (2026-03-07)

### 修復

#### Scraper parser：SD 系列緊湊格式與多行 chunk 解析
- **修復 JP001-JP028 遺漏**: SD 系列重印卡使用緊湊單行格式 `JP名(中文名) 屬性 N星 類型/種族 ATK DEF`，不含標準類型關鍵字，導致 `_is_detail_entry()` 誤判為摘要而跳過。現在會對 header 和後續相鄰 chunks 合併後用 `COMPACT_STATS_RE` 偵測
- **修復多行 chunk 條件/效果遺漏**: 部分文章的卡種、條件、效果被包在單一 leaf element 的多行文字中（如 `white-space-collapse: preserve` span）。舊邏輯在找到 stats 後 `continue` 導致同一 chunk 後半的條件/效果被跳過。現在 `_parse_card_details()` 會先將所有 context 按 `\n` 拆分展開
- **修復 JPS01-JPS06、JP029-JP030 等效果未解析**: 同上（多行 chunk 問題）
- **修復緊湊格式類型誤判**: 若緊湊格式只有一個字段且不在類型映射表中（如 `魔法使`、`戰士`），正確解讀為種族、卡種設為通常怪獸；而非錯誤拼接為「魔法使怪獸」
- **新增 JP 名提取**: 緊湊格式的 JP 名從合併後的文字中提取（card_id 尾端到 (中文名) 之間）

**受影響範圍**: `tools/rd-card-scraper/rd_card_scraper/parser.py`

---

## v0.3.3 (2026-02-16)

### 新增

#### 手動建立卡片
- **CardCreatePanel**: 卡組頁側邊欄可建立新卡片，支援完整欄位 (名稱、類型、屬性、效果等)
- **下一張卡號**: `GET /api/cards/next-id/{set_id}` 自動推斷下一個可用 card_id
- **is_manual 標記**: 手動建立的卡片標記 `is_manual=True`，匯入時整張跳過

#### 卡片欄位 override 持久化
- **card_overrides 表**: 使用者編輯 scraper 匯入的卡片時，欄位存於此表
- **匯入不覆蓋**: 有 override 的欄位在匯入時保留使用者編輯值；`is_manual` 卡片完全不匯入

### 更新

- API: `POST /api/cards` 建立卡片、`GET /api/cards/next-id/{set_id}` 取得下一卡號
- PATCH /api/cards: 非 manual 卡片的編輯會自動建立 override
- 匯入服務: `_import_one_card()` 跳過 `is_manual`、套用 `card_overrides`
- 前端: `sidebarMode` 區分 create/detail、`CardCreatePanel`、`createCard()` / `getNextCardId()`
- ui store: `sidebarCreateSetId`、`openCreateSidebar(setId)`

---

## v0.3.2 (2026-02-15)

### 新增

#### 卡組 metadata 編輯與 override 持久化
- **SetMetadataEditor**: 卡組頁可編輯 set_name_jp/zh、product_type、release_date、total_cards、rarity_distribution
- **card_set_overrides 表**: 使用者編輯的欄位存於此表，匯入時不覆蓋有 override 的欄位
- **還原單一欄位**: 刪除 override 後，下次匯入會恢復 scraper 原始值

### 更新

- API: `PATCH /api/card-sets/{set_id}` 編輯卡組、`GET /overrides` 列出 override、`DELETE /overrides/{field}` 還原
- 匯入服務: `_upsert_card_set()` 跳過有 override 的欄位
- 前端 `api/cardSets.ts`: `updateCardSet()`, `fetchCardSetOverrides()`, `deleteCardSetOverride()`

---

## v0.3.1 (2026-02-15)

### 新增

#### 卡圖上傳與還原
- **側邊欄卡圖上傳**: CardDetailPanel 卡圖 hover 顯示上傳 overlay，點擊選擇圖片替換
- **還原為原始圖**: 使用者上傳的卡圖可點「Revert to original」恢復為 scraper 原始圖
- **scraper_image_path 欄位**: 新增 `card_variants.scraper_image_path` 持久保存原始 scraper 路徑，確保即使所有 variant 皆被覆蓋仍能正確還原

### 修復

- **瀏覽器快取問題**: 使用者上傳圖檔回傳 `Cache-Control: no-cache`，前端對 user_upload 圖 URL 加 `?t=...` cache buster 避免顯示舊圖

### 更新

- API: `POST /api/images/card/{card_id}/{rarity}/upload`、`DELETE .../upload` 對應上傳與還原
- 前端 `api/cards.ts`: 新增 `uploadCardImage()`, `revertCardImage()`
- 匯入時寫入 `scraper_image_path`，上傳時保留原始路徑供還原使用

---

## v0.3.0 (2026-02-15)

### 新增

#### 複合卡片類型支援
- Parser 新增複合怪獸類型: `儀式/效果怪獸`, `融合/效果怪獸`, `巨極/效果怪獸`
- Parser 新增魔法子類型: `儀式魔法`
- Regex 排序: 複合類型在簡單類型前匹配，避免 `儀式/效果怪獸` 被截斷為 `效果怪獸`

#### 永續效果 & 召喚條件欄位
- 新增 `continuous_effect` 欄位: 解析 `永續效果:` 標籤，與一般 `效果:` 分開儲存
- 新增 `summon_condition` 欄位: 解析 stats 行與 `條件:` 之間的描述文字 (如「此卡只能用…特殊召喚」)
- 同行多標籤拆分: 處理 `條件:…可以發動效果:…` 連在同一個 HTML element 的情況
- `_LABEL_SPLIT_RE` 使用 negative lookbehind `(?<!永續)` 避免拆斷 `永續效果:`

#### 前端 inline 編輯
- CardDetailPanel 重寫為 inline 編輯模式 (取代獨立的 CardEditForm)
- Card Type 改為下拉選單 (包含所有簡單 + 複合類型)
- 怪獸專屬欄位 (Attribute, Race, Level, ATK, DEF, Summon Condition) 僅在選擇怪獸類型時顯示
- 文字欄位 (Summon Condition, Condition, Effect, Continuous Effect) 無值時收合為 `+` 按鈕，點擊展開

### 修復

- **`--no-images` 遺失圖片路徑**: 新增 `_link_existing_images()` 在不下載時偵測磁碟上已存在的圖片檔，保留 `image_file` 路徑
- **搜尋複合類型**: `card_type` 篩選改用 `ILIKE` 部分比對，搜尋「儀式」可同時匹配 `儀式怪獸` 和 `儀式/效果怪獸`

### 更新

- DB migration: `init-db` 自動 `ALTER TABLE ADD COLUMN` 補新欄位 (safe to run repeatedly)
- 前端 SearchFilters: 補齊所有卡片類型選項
- 刪除 `CardEditForm.vue` (功能已整合至 CardDetailPanel)

---

## v0.2.1 (2026-02-15)

### 修復

#### Discovery 策略重寫

- **問題**: 舊版 discovery 使用 sitemap + URL 模式匹配，漏掉了 ~15 篇使用非標準 URL slug 的卡表文章 (如 `rush-duel-110.html`)
- **新策略**: 「標題優先，內容驗證兜底」
  - Phase 1: 翻頁爬取 blog listing page，每頁 ~20 篇文章含 URL + 標題
  - Phase 2: 標題含 `[卡表資料]` + RD 關鍵字 → 直接接受；含 `禁限卡表`/Meta/Combo → 直接排除
  - Phase 3: URL 含 `rush-duel`/`rdgrd` 但標題無法分類 → 候選
  - Phase 4: 候選文章 fetch 驗證內容 (RD/ 卡號 + 卡片類型關鍵字)
- **結果**: 74 篇 RD 卡表 (比舊版多 15 篇)，0 篇需要逐篇 fetch 驗證
- **效能**: 預設只爬 2020 年以後 (~71 頁 listing page)，增量更新自動早停

### 新增

- CLI `--since YEAR` 參數: 限定只發現指定年份以後的文章 (如 `--since 2025` 只翻 9 頁)
- 增量更新早停: 傳入 known_urls，當整頁都是已知 URL 時停止翻頁
- Pagination cursor 年份截止: 基於 `updated-max` 參數判斷是否繼續翻頁

### 更新

- discovery.py: 完全重寫 (移除 sitemap 方式，改用 listing page 翻頁 + 標題篩選)
- scraper.py: 支援 `**discover_kwargs` 透傳參數 (since_year 等)
- cli.py: 新增 `--since` 參數，discover 指令顯示標題
- 3 個 SKILL 更新: ntucgm-blog-structure, rd-banlist-exclusion, rd-scraping-etiquette
- tools/rd-card-scraper/README.md: 更新架構圖與 discovery 策略說明

---

## v0.2.0 (2026-02-14)

### 新增

#### rd-checklist 收藏管理 Web App

**Backend (FastAPI + SQLite)**
- 資料庫設計: `card_sets`, `cards`, `card_variants` (每個稀有度一筆), `card_edits` (編輯歷史)
- 匯入服務: 從 scraper 的 `cards.json` 匯入，自動拆分多稀有度 (如 `UR/SER` → 兩筆 variant)
- 匯入安全: 重新匯入時絕不覆蓋使用者的 `owned_count`
- API 端點:
  - `GET /api/card-sets` — 列出所有卡組，可依產品類型篩選
  - `GET /api/card-sets/product-types` — 產品類型列表 (含中文顯示名)
  - `GET /api/card-sets/{set_id}` — 卡組詳情含所有卡片
  - `GET/PATCH /api/cards/{card_id}` — 卡片詳情與編輯
  - `PATCH /api/ownership/{card_id}/{rarity}` — 更新持有數量
  - `PATCH /api/ownership/batch` — 批次更新
  - `GET /api/ownership/stats[/{set_id}]` — 收藏統計
  - `GET /api/search` — 搜尋 (支援名稱/ID/效果/類型/屬性/等級/稀有度/持有狀態)
  - `GET /api/images/card/{card_id}/{rarity}` — 卡圖 (直接讀取 scraper data)
- CLI: `init-db`, `import --scraper-data PATH [--force]`
- 匯入結果: 54 sets, 2210 cards, 2522 variants (305 多稀有度卡)

**Frontend (Vue 3 + TypeScript + Tailwind CSS)**
- 深色主題 UI
- 首頁: 產品類型篩選 pill + 卡組列表 grid
- 卡組頁: 收藏進度條、Card View (圖片 grid) / Table View 切換
- 卡片 Grid: 卡圖 + 稀有度 tabs + 持有數 +/- 控制、未持有卡片灰階顯示
- 卡片 Table: 排列 ID/名稱/類型/LV/ATK/DEF/稀有度/持有數，未持有行半透明
- 卡片詳情側邊欄: 大圖、完整卡片資訊、效果文字、編輯表單
- 搜尋頁: 即時搜尋 (300ms debounce) + 類型/屬性/等級/稀有度/持有狀態 filter
- 麵包屑導航、Esc 關閉側邊欄
- Vite proxy `/api` → backend

### 更新

- CLAUDE.md: 加入 Checklist App 指令與結構說明
- .gitignore: 加入 backend/data/、frontend/node_modules/、frontend/dist/

---

## v0.1.0 (2026-02-13)

### 新增

#### rd-card-scraper 卡牌爬取工具
- **文章發現** (`discovery.py`): 從 sitemap 自動發現 ~59 篇 Rush Duel 卡表文章，透過 URL 模式比對區分卡表 vs 禁限卡表
- **HTML 解析** (`parser.py`): 支援 2020~2025 三個不同時期的部落格 HTML 結構
  - 2020 (KP01 時期): 卡名和 stats 都在 `<b><span>` 中，無圖片
  - 2022 (KP09 時期): stats 在普通 `<div>` 中，有 `<img>` 圖片
  - 2025 (KP23 時期): 圖片在 `<a><img>` wrapper 中
- **圖片下載** (`downloader.py`): 從 blogger.googleusercontent.com 下載卡牌圖片，支援尺寸參數調整
- **增量更新** (`scraper.py`): 基於 post-body 的 SHA256 hash 偵測內容變更，避免重複爬取
- **CLI** (`cli.py`): 支援 `discover`, `scrape-all`, `update`, `scrape-url`, `summary` 等指令

#### 每張卡片記錄的欄位
- 卡片編號 (`RD/{SetID}-JP{Number}`)
- 日文名、中文名
- 卡片類型 (怪獸/魔法/陷阱及子類型)
- 屬性、種族、等級、ATK/DEF
- 發動條件、效果說明
- 卡圖 URL 及本地圖片路徑
- 稀有度、Legend 標記

#### 專案基礎建設
- CLAUDE.md: 專案概述、開發指令
- `.claude/skills/`: 8 個 SKILL.md 檔案，記錄部落格結構、解析心法、產品類型等領域知識
- `.gitignore`: 排除 data/、.venv/、.claude/settings.local.json

### 開發筆記

#### 網站結構探索過程
1. 透過 sitemap.xml 取得所有文章 URL
2. 發現禁限卡表 URL (`rush-duel-20234.html`) 與卡表 URL 容易混淆，需要排除規則
3. 確認卡表文章有「摘要索引 + 詳細區塊」雙重結構，卡片 ID 會出現兩次

#### Parser 迭代過程
- **v1 嘗試**: 以 bold (`<b>`) 元素作為卡片邊界 → 失敗，因為 KP01 時期的 stats 行也是 bold
- **v2 (最終)**: 改用 chunk-based 方法 — 將 HTML 扁平化為 text/image chunks，用「是否有 stats 關鍵字在附近」判斷是摘要還是詳細區塊

#### 測試結果
| 彈數 | 年份 | 預期張數 | 解析張數 | 圖片 |
|------|------|----------|----------|------|
| KP01 | 2020 | 51 | 48 | 無 (文章無圖) |
| KP09 | 2022 | 66 | 66 ✓ | 66 ✓ |
| KP23 | 2025 | 68 | 63 | 63 |
