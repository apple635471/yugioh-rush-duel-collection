#!/usr/bin/env python3
"""
Rush Duel Card Scanner — two-phase: OCR extraction then translation.

Phase 1 (extract_model, default gpt-4o):        read raw Japanese text from card image.
Phase 2 (translate_model, default gpt-4o-mini): translate to Traditional Chinese.

Usage:
    python scan_card.py <image_path>
    python scan_card.py <image_path> --extract-model gpt-4o --translate-model gpt-4o-mini
    python scan_card.py <image_path> -o result.json
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
    print("請先安裝 openai: uv sync", file=sys.stderr)
    sys.exit(1)


# ── 專案路徑 ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_PATH = PROJECT_ROOT / "apps" / "rd-checklist" / "backend" / "data" / "rd_checklist.db"

# ── Default models ─────────────────────────────────────────────────────────────
# Phase 1 (Vision OCR): gpt-4o — best vision for accurate Japanese text extraction
# Phase 2 (Translation): gpt-4o-mini — text-only, ~15x cheaper, quality sufficient
DEFAULT_EXTRACT_MODEL = "gpt-4o"
DEFAULT_TRANSLATE_MODEL = "gpt-4o-mini"

# ── 載入 .env ─────────────────────────────────────────────────────────────────
def _load_dotenv(env_path: Path):
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())

_load_dotenv(PROJECT_ROOT / ".env")


# ── 從 DB 載入已知的列舉值 ─────────────────────────────────────────────────────
def load_known_values() -> dict:
    if not DB_PATH.exists():
        return {
            "attributes": ["光", "暗", "炎", "水", "風", "地"],
            "monster_types": ["龍族", "魔法使族", "天使族", "惡魔族", "不死族", "戰士族"],
            "card_types": ["通常怪獸", "效果怪獸", "融合怪獸", "通常魔法", "通常陷阱"],
        }

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT attribute FROM cards WHERE attribute IS NOT NULL AND attribute != '' ORDER BY attribute")
    attributes = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT monster_type FROM cards
        WHERE monster_type IS NOT NULL AND monster_type != ''
          AND length(monster_type) <= 10
          AND monster_type NOT LIKE '條件%'
        ORDER BY monster_type
    """)
    monster_types = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT card_type FROM cards WHERE card_type IS NOT NULL AND card_type != '' ORDER BY card_type")
    card_types = [r[0] for r in cur.fetchall()]

    conn.close()
    return {
        "attributes": attributes or ["光", "暗", "炎", "水", "風", "地"],
        "monster_types": monster_types or ["龍族", "魔法使族", "天使族", "惡魔族", "不死族", "戰士族"],
        "card_types": card_types or ["通常怪獸", "效果怪獸", "融合怪獸", "通常魔法", "通常陷阱"],
    }


# ── 圖片讀取 ─────────────────────────────────────────────────────────────────
def load_image_b64(image_path: str) -> tuple[str, str]:
    path = Path(image_path)
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png", ".webp": "image/webp"}
    media_type = media_map.get(path.suffix.lower(), "image/jpeg")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode(), media_type


# ── Phase 1: OCR Prompt ───────────────────────────────────────────────────────
EXTRACT_PROMPT = """你是遊戲王 Rush Duel（超速決鬥）OCR 專家。
請完整讀取卡牌圖片中的所有文字，不做任何翻譯，原文照錄。

## 回傳格式
嚴格回傳合法 JSON，不要任何額外說明。

{
  "name_jp": "カード名（原文）",
  "card_type_jp": "卡牌種類原文（e.g. 効果モンスター、通常魔法）",
  "is_legend": true 或 false（卡片上有 LEGEND 標記則 true）,
  "attribute_jp": "属性原文（e.g. 闇、光、炎）或 null",
  "monster_type_jp": "種族原文（e.g. 魔法使い族、ドラゴン族）或 null",
  "level": 等級數字或 null,
  "atk": "ATK 數值字串或 '?' 或 null",
  "defense": "DEF 數值字串或 '?' 或 null",
  "description_jp": "フレーバーテキスト原文（通常怪獸的說明）或 null",
  "summon_condition_jp": "特殊召喚条件原文（融合/儀式/マキシマム 等）或 null",
  "condition_jp": "効果発動条件原文（条件 の部分）或 null",
  "effect_jp": "効果テキスト原文或 null",
  "continuous_effect_jp": "永続効果テキスト原文（場で常に有効）或 null"
}

## 注意
- 完整保留日文原文，包含符號
- ATK/DEF 顯示問號時填 "?"
- 看不到或不適用的欄位填 null
- 不要翻譯、不要解釋，只讀原文
"""


# ── Phase 2: Translation Prompt ───────────────────────────────────────────────
def build_translate_prompt(raw: dict, known: dict) -> str:
    attrs = "、".join(known["attributes"])
    types = "、".join(known["monster_types"])
    card_types_str = "、".join(known["card_types"])
    raw_json = json.dumps(raw, ensure_ascii=False, indent=2)

    return f"""你是遊戲王 Rush Duel 翻譯專家，專門將日文卡牌資訊翻譯成繁體中文。
以下是從卡牌圖片 OCR 出的日文原文（JSON 格式），請根據規則翻譯成繁體中文並回傳指定格式。

## 原始日文資料
{raw_json}

## 回傳格式
嚴格回傳合法 JSON，不要任何額外說明。

{{
  "name_jp": "日文卡名（原封不動複製）",
  "name_zh": "繁體中文卡名",
  "card_type": "繁體中文卡牌種類（從下方清單選一個）",
  "is_legend": true 或 false（同原始資料）,
  "attribute": "繁體中文屬性（從下方清單選一個）或 null",
  "monster_type": "繁體中文種族（從下方清單選一個）或 null",
  "level": 等級數字或 null,
  "atk": "ATK 原值或 null",
  "defense": "DEF 原值或 null",
  "description": "繁體中文說明文，格式：繁中（日文原文）或 null",
  "summon_condition": "繁體中文召喚條件，格式：繁中（日文原文）或 null",
  "condition": "繁體中文效果條件，格式：繁中（日文原文）或 null",
  "effect": "繁體中文效果文字，格式：繁中（日文原文）或 null",
  "continuous_effect": "繁體中文持續效果，格式：繁中（日文原文）或 null"
}}

## card_type 可能值（從以下選最符合的）：
{card_types_str}

## attribute 可能值（屬性）：
{attrs}

## monster_type 可能值（種族）：
{types}

## 翻譯術語對照
手札→手牌、デッキ→牌組、フィールド→場上、墓地→墓地、
ライフポイント→生命值、モンスター→怪獸、魔法カード→魔法卡、
罠カード→陷阱卡、攻撃→攻擊、守備→守備、破壊→破壞、
特殊召喚→特殊召喚、バトルフェイズ→戰鬥階段、メインフェイズ→主要階段、
ターン→回合、ドロー→抽牌、融合→融合、儀式→儀式。

## 注意
- card_type / attribute / monster_type 直接對應到繁中清單，不要附日文原文
- 文字欄位格式務必是「繁中（日文原文）」
- ATK/DEF 直接複製，不需翻譯
- 原始資料為 null 的欄位回傳 null
"""


# ── OpenAI 呼叫 ───────────────────────────────────────────────────────────────
def call_vision(client: OpenAI, model: str, img_b64: str, media_type: str, prompt: str) -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{img_b64}", "detail": "high"},
                },
                {"type": "text", "text": prompt},
            ],
        }],
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def call_text(client: OpenAI, model: str, prompt: str) -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


# ── 主流程 ────────────────────────────────────────────────────────────────────
def scan_card(
    image_path: str,
    extract_model: str = DEFAULT_EXTRACT_MODEL,
    translate_model: str = DEFAULT_TRANSLATE_MODEL,
) -> dict:
    """Two-phase card scan. Returns {'raw': {...}, ...translated_fields}."""
    known = load_known_values()
    img_b64, media_type = load_image_b64(image_path)
    client = OpenAI()

    print(f"[phase 1] OCR ({extract_model}): {image_path}", file=sys.stderr)
    raw = call_vision(client, extract_model, img_b64, media_type, EXTRACT_PROMPT)

    print(f"[phase 2] Translate ({translate_model})", file=sys.stderr)
    translated = call_text(client, translate_model, build_translate_prompt(raw, known))

    return {"raw": raw, **translated}


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Rush Duel 卡牌圖片兩階段掃描器")
    parser.add_argument("image", help="卡牌圖片路徑（jpg/png/webp）")
    parser.add_argument("--extract-model",   default=DEFAULT_EXTRACT_MODEL,
                        help=f"Phase 1 Vision 模型（預設 {DEFAULT_EXTRACT_MODEL}）")
    parser.add_argument("--translate-model", default=DEFAULT_TRANSLATE_MODEL,
                        help=f"Phase 2 翻譯模型（預設 {DEFAULT_TRANSLATE_MODEL}）")
    parser.add_argument("--output", "-o", help="輸出 JSON 檔案路徑（預設印到 stdout）")
    args = parser.parse_args()

    if not Path(args.image).exists():
        print(f"[error] 找不到圖片：{args.image}", file=sys.stderr)
        sys.exit(1)

    if not os.environ.get("OPENAI_API_KEY"):
        print("[error] 請設定 OPENAI_API_KEY（在 .env 或環境變數）", file=sys.stderr)
        sys.exit(1)

    result = scan_card(args.image, args.extract_model, args.translate_model)
    output_str = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"[ok] 結果已寫入：{args.output}", file=sys.stderr)
    else:
        print(output_str)


if __name__ == "__main__":
    main()
