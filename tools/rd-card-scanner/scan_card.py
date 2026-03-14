#!/usr/bin/env python3
"""
Rush Duel Card Scanner
用一張卡牌圖片，透過 OpenAI Vision API 萃取卡牌資訊並翻譯成中文。

Usage:
    python scan_card.py <image_path> [--model gpt-4o] [--output card_info.json]
"""

import argparse
import base64
import json
import os
import sqlite3
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("請先安裝 openai: pip install openai")
    sys.exit(1)


# ── 專案路徑 ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "apps" / "rd-checklist" / "backend" / "data" / "rd_checklist.db"

# ── 載入 .env ─────────────────────────────────────────────────────────────────
def _load_dotenv(env_path: Path):
    """簡易 .env 載入，不依賴 python-dotenv。"""
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())

_load_dotenv(PROJECT_ROOT / ".env")


# ── 從 DB 載入已知的列舉值，供 prompt 使用 ────────────────────────────────────
def load_known_values() -> dict:
    """從 DB 讀取已收錄過的屬性、種族、卡牌種類列表。"""
    if not DB_PATH.exists():
        # fallback：hardcoded
        return {
            "attributes": ["光", "暗", "炎", "水", "風", "地"],
            "monster_types": [
                "龍族", "魔法使族", "天使族", "惡魔族", "不死族", "戰士族", "獸戰士族",
                "獸族", "鳥獸族", "水族", "海龍族", "昆蟲族", "植物族", "岩石族",
                "機械族", "炎族", "雷族", "超能族", "超龍族", "銀河族", "魚族",
                "爬蟲族", "恐龍族", "半機械族", "電子族", "幻龍族", "天界戰士族",
                "奧米茄超能族", "獸族", "魔導騎士族", "魔法族",
            ],
            "card_types": [
                "通常怪獸", "效果怪獸", "融合怪獸", "融合/效果怪獸",
                "儀式怪獸", "儀式/效果怪獸", "巨極/效果怪獸",
                "通常魔法", "場地魔法", "裝備魔法", "儀式魔法",
                "通常陷阱",
            ],
        }

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 屬性
    cur.execute("SELECT DISTINCT attribute FROM cards WHERE attribute IS NOT NULL AND attribute != '' ORDER BY attribute")
    attributes = [r[0] for r in cur.fetchall()]

    # 種族（過濾掉解析錯誤殘留的長字串）
    cur.execute("""
        SELECT DISTINCT monster_type FROM cards
        WHERE monster_type IS NOT NULL AND monster_type != ''
          AND length(monster_type) <= 10
          AND monster_type NOT LIKE '條件%'
        ORDER BY monster_type
    """)
    monster_types = [r[0] for r in cur.fetchall()]

    # 卡牌種類
    cur.execute("SELECT DISTINCT card_type FROM cards WHERE card_type IS NOT NULL AND card_type != '' ORDER BY card_type")
    card_types = [r[0] for r in cur.fetchall()]

    conn.close()
    return {"attributes": attributes, "monster_types": monster_types, "card_types": card_types}


# ── 載入圖片為 base64 ─────────────────────────────────────────────────────────
def load_image_b64(image_path: str) -> tuple[str, str]:
    """回傳 (base64_string, media_type)。"""
    path = Path(image_path)
    suffix = path.suffix.lower()
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    media_type = media_map.get(suffix, "image/jpeg")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode(), media_type


# ── 建構 prompt ───────────────────────────────────────────────────────────────
def build_prompt(known: dict) -> str:
    attrs = "、".join(known["attributes"])
    types = "、".join(known["monster_types"])
    card_types_str = "、".join(known["card_types"])

    return f"""你是遊戲王 Rush Duel（超速決鬥）卡牌資料庫專家。
我會給你一張卡牌圖片，請從圖片中讀取所有文字，萃取以下欄位，並將日文翻譯成繁體中文。

## 回傳格式
請嚴格回傳合法 JSON，不要有任何額外說明文字。結構如下：

{{
  "name_jp": "日文卡名（原文）",
  "name_zh": "繁體中文卡名",
  "card_type": "卡牌種類（見下方說明）",
  "is_legend": true 或 false,
  "attribute": "屬性（怪獸卡才有）或 null",
  "monster_type": "種族（怪獸卡才有）或 null",
  "level": 等級數字（怪獸卡才有）或 null,
  "atk": "攻擊力數字字串或 '?' 或 null",
  "defense": "守備力數字字串或 '?' 或 null",
  "description": "卡片說明文（通常怪獸的繪圖說明、魔法/陷阱的說明），繁體中文，原始日文以括號附在後面，例：「繁中譯文（日文原文）」",
  "summon_condition": "特殊召喚條件（儀式/融合/巨極等），繁體中文，格式同上，無則 null",
  "condition": "效果發動條件（條件:...），繁體中文，格式同上，無則 null",
  "effect": "效果文字，繁體中文，格式同上，無則 null",
  "continuous_effect": "持續效果文字（場上一直有效），繁體中文，格式同上，無則 null"
}}

## 欄位說明

### card_type 可能值（請從以下選一個最符合的）：
{card_types_str}

### attribute 可能值（屬性）：
{attrs}

### monster_type 可能值（種族）：
{types}

### is_legend
卡片上印有「LEGEND」標記時為 true。

### 文字欄位翻譯規則
- 繁體中文為主要翻譯
- 日文原文附在每個欄位後方，格式：「繁中譯文（日文原文）」
- 若已是繁體中文則直接填入，不需附日文
- 卡名固有名詞（角色名、技能名）可音譯
- 專有術語對照：
  - 手札 → 手牌
  - デッキ → 牌組
  - フィールド → 場上
  - 墓地 → 墓地（不變）
  - ライフポイント → 生命值
  - モンスター → 怪獸
  - 魔法カード → 魔法卡
  - 罠カード → 陷阱卡
  - 表示形式 → 表示形式（不變）
  - 攻撃 → 攻擊
  - 守備 → 守備
  - 破壊 → 破壞
  - 特殊召喚 → 特殊召喚（不變）
  - バトルフェイズ → 戰鬥階段
  - メインフェイズ → 主要階段
  - ターン → 回合
  - ドロー → 抽牌
  - 融合 → 融合（不變）
  - 儀式 → 儀式（不變）

### 欄位對應方式（Rush Duel 卡片版面由上至下）
- 怪獸卡：名稱 → 屬性、等級 → 卡牌種類/種族 → 圖片 → 召喚條件（若有）→ 條件（若有）→ 效果 → 持續效果 → ATK / DEF
- 魔法/陷阱卡：名稱 → 圖片 → 說明文 → 條件（若有）→ 效果

## 注意事項
- 卡片攻擊力/守備力如為問號顯示，atk/defense 填 "?"
- 巨極怪獸（マキシマム）通常有 [L][M][R] 三張，請各自獨立萃取
- 若某欄位在圖片中看不到或不適用，填 null
"""


# ── 呼叫 OpenAI API ───────────────────────────────────────────────────────────
def scan_card(image_path: str, model: str = "gpt-4o") -> dict:
    known = load_known_values()
    prompt = build_prompt(known)

    img_b64, media_type = load_image_b64(image_path)

    client = OpenAI()  # 讀 OPENAI_API_KEY 環境變數

    print(f"[info] 呼叫 {model}，圖片：{image_path}", file=sys.stderr)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{img_b64}",
                            "detail": "high",
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
        max_tokens=2048,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    return json.loads(raw)


# ── 主程式 ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Rush Duel 卡牌圖片掃描器")
    parser.add_argument("image", help="卡牌圖片路徑（jpg/png/webp）")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI 模型（預設 gpt-4o）")
    parser.add_argument("--output", "-o", help="輸出 JSON 檔案路徑（預設印到 stdout）")
    args = parser.parse_args()

    if not Path(args.image).exists():
        print(f"[error] 找不到圖片：{args.image}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[error] 請設定 OPENAI_API_KEY 環境變數", file=sys.stderr)
        sys.exit(1)

    result = scan_card(args.image, model=args.model)

    output_str = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"[ok] 結果已寫入：{args.output}", file=sys.stderr)
    else:
        print(output_str)


if __name__ == "__main__":
    main()
