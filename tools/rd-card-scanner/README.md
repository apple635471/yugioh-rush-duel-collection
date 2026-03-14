# rd-card-scanner

用一張遊戲王 Rush Duel 卡牌圖片，透過 **兩階段 OpenAI API** 自動萃取卡牌資訊並翻譯成繁體中文。

## 兩階段架構

| 階段 | 模型（預設） | 工作 |
|------|------------|------|
| **Phase 1 — OCR** | `gpt-4o` | 讀取卡牌圖片，完整輸出日文原文，不翻譯 |
| **Phase 2 — 翻譯** | `gpt-4o-mini` | 將 Phase 1 的日文 JSON 翻譯成繁體中文 |

Phase 1 和 Phase 2 分離的好處：
- 每個模型做好一件事，整體準確度更高
- 可切換 Phase 2 到更強的模型（如 `gpt-4o`）提升翻譯品質
- 結果同時保留原始日文與繁中翻譯，方便人工核對

## 功能

- **Phase 1**: 從卡牌圖片 OCR 出日文原文（卡名、種族、效果文字等）
- **Phase 2**: 翻譯成繁體中文，從 DB 讀取已知屬性/種族/卡牌種類確保術語一致
- 結果輸出為 JSON，包含 `raw`（日文原文）與翻譯欄位
- 支援 jpg / png / webp 圖片格式

## 環境設定

在**專案根目錄**的 `.env` 加入：

```
OPENAI_API_KEY=sk-...
```

> `scan_card.py` 會自動讀取 `PROJECT_ROOT/.env`，無需手動 export。

## 安裝

```bash
cd tools/rd-card-scanner
uv sync
```

## 使用方式

```bash
# 基本用法（結果印到 stdout）
uv run python scan_card.py /path/to/card.jpg

# 儲存結果到 JSON 檔
uv run python scan_card.py /path/to/card.jpg -o result.json

# 指定兩階段的模型（預設如下）
uv run python scan_card.py /path/to/card.jpg \
  --extract-model gpt-4o \
  --translate-model gpt-4o-mini

# Phase 2 改用 gpt-4o 提升翻譯品質（費用較高）
uv run python scan_card.py /path/to/card.jpg --translate-model gpt-4o
```

### 輸出範例

```json
{
  "name_jp": "超魔導戦士-マスター・オブ・カオス",
  "name_zh": "超魔導戰士－混沌之主",
  "card_type": "融合/效果怪獸",
  "is_legend": false,
  "attribute": "暗",
  "monster_type": "魔法使族",
  "level": 8,
  "atk": "3000",
  "defense": "2500",
  "description": null,
  "summon_condition": "「黑魔術師」＋光或暗屬性怪獸（「黑魔術師」＋光属性または暗属性のモンスター）",
  "condition": null,
  "effect": "...",
  "continuous_effect": null
}
```

## 翻譯規則

| 日文術語 | 繁體中文 |
|----------|----------|
| 手札 | 手牌 |
| デッキ | 牌組 |
| フィールド | 場上 |
| ライフポイント | 生命值 |
| バトルフェイズ | 戰鬥階段 |
| メインフェイズ | 主要階段 |
| ターン | 回合 |
| ドロー | 抽牌 |

文字欄位格式：「**繁體中文譯文**（日文原文）」，方便核對原文。

## 注意事項

- 推薦模型為 `gpt-4o`（Vision 辨識品質最佳）
- 每次呼叫約消耗 1,000–3,000 tokens（視卡牌文字量而定）
- 辨識結果僅供參考，請務必人工核對後再儲存
- 巨極怪獸（MAXIMUM）有 L / M / R 三張，請分別掃描

## 在 Checklist App 中使用

Checklist App 的 CardDetailPanel 右側面板提供 **✦ Scan** 按鈕，可直接呼叫後端的
`POST /api/scan/{card_id}/{rarity}` 端點，掃描目前稀有度對應的卡圖（優先使用 user upload），
並在浮動面板中顯示結果供複製貼上。

```
CardDetailPanel
  └── [✦ Scan 按鈕]
        └── ScanResultPanel（浮動可拖曳）
              ├── 各欄位 + 複製按鈕
              ├── [重整] 重新呼叫 API
              └── [×] 關閉
```

## 目錄結構

```
tools/rd-card-scanner/
  scan_card.py        # 主程式（可獨立執行，也被後端 import）
  pyproject.toml      # Python 依賴（openai）
  README.md           # 本文件
```
