"""Card scanner API — two-phase: OCR extraction then translation via OpenAI."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CardVariantModel
from ..services.image_service import get_image_path, get_user_image_path

router = APIRouter(prefix="/api/scan", tags=["scan"])

# ── Load OPENAI_API_KEY from root .env if not already set ─────────────────────

def _load_dotenv() -> None:
    env_path = Path(__file__).parents[5] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


_load_dotenv()

# ── Default models ─────────────────────────────────────────────────────────────
# Phase 1 (Vision OCR): gpt-4o — best vision for accurate Japanese text extraction
# Phase 2 (Translation): gpt-4o-mini — text-only, ~15x cheaper, quality sufficient
DEFAULT_EXTRACT_MODEL = "gpt-4o"
DEFAULT_TRANSLATE_MODEL = "gpt-4o-mini"

# ── Response schemas ──────────────────────────────────────────────────────────

class CardRawExtract(BaseModel):
    """Phase 1 result: raw Japanese text extracted from image, no translation."""
    name_jp: str | None = None
    card_type_jp: str | None = None      # e.g. "効果モンスター"
    is_legend: bool | None = None
    attribute_jp: str | None = None      # e.g. "闇"
    monster_type_jp: str | None = None   # e.g. "魔法使い族"
    level: int | None = None
    atk: str | None = None
    defense: str | None = None
    description_jp: str | None = None
    summon_condition_jp: str | None = None
    condition_jp: str | None = None
    effect_jp: str | None = None
    continuous_effect_jp: str | None = None


class ScanResult(BaseModel):
    """Combined two-phase result: raw OCR + translated fields."""
    # ── Phase 1 raw ──
    raw: CardRawExtract
    # ── Phase 2 translated ──
    name_jp: str | None = None
    name_zh: str | None = None
    card_type: str | None = None
    is_legend: bool | None = None
    attribute: str | None = None
    monster_type: str | None = None
    level: int | None = None
    atk: str | None = None
    defense: str | None = None
    description: str | None = None
    summon_condition: str | None = None
    condition: str | None = None
    effect: str | None = None
    continuous_effect: str | None = None


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _get_known_values(db: Session) -> dict:
    attrs = [r[0] for r in db.execute(
        text("SELECT DISTINCT attribute FROM cards"
             " WHERE attribute IS NOT NULL AND attribute != '' ORDER BY attribute")
    ).fetchall()]
    monster_types = [r[0] for r in db.execute(
        text("SELECT DISTINCT monster_type FROM cards"
             " WHERE monster_type IS NOT NULL AND monster_type != ''"
             "   AND length(monster_type) <= 10"
             "   AND monster_type NOT LIKE '條件%'"
             " ORDER BY monster_type")
    ).fetchall()]
    card_types = [r[0] for r in db.execute(
        text("SELECT DISTINCT card_type FROM cards"
             " WHERE card_type IS NOT NULL AND card_type != '' ORDER BY card_type")
    ).fetchall()]
    return {
        "attributes":    attrs         or ["光", "暗", "炎", "水", "風", "地"],
        "monster_types": monster_types or ["龍族", "魔法使族", "天使族", "惡魔族", "不死族", "戰士族"],
        "card_types":    card_types    or ["通常怪獸", "效果怪獸", "融合怪獸", "通常魔法", "通常陷阱"],
    }


# ── Phase 1: OCR extraction prompt ────────────────────────────────────────────

_EXTRACT_PROMPT = """你是遊戲王 Rush Duel（超速決鬥）OCR 專家。
請完整讀取卡牌圖片中的所有文字，**不做任何翻譯**，原文照錄。

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
  "condition_jp": "効果発動条件原文（「条件」の部分）或 null",
  "effect_jp": "効果テキスト原文或 null",
  "continuous_effect_jp": "永続効果テキスト原文（場で常に有効）或 null"
}

## 注意
- 完整保留日文原文，包含符號（【】「」・等）
- ATK/DEF 顯示問號時填 "?"
- 看不到或不適用的欄位填 null
- 不要翻譯、不要解釋，只讀原文
"""


def _build_extract_prompt() -> str:
    return _EXTRACT_PROMPT


# ── Phase 2: translation prompt ───────────────────────────────────────────────

def _build_translate_prompt(raw: CardRawExtract, known: dict) -> str:
    attrs = "、".join(known["attributes"])
    types = "、".join(known["monster_types"])
    card_types_str = "、".join(known["card_types"])

    raw_json = raw.model_dump_json(indent=2, exclude_none=True)

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
  "description": "繁體中文說明文，格式：「繁中（日文原文）」或 null",
  "summon_condition": "繁體中文召喚條件，格式：「繁中（日文原文）」或 null",
  "condition": "繁體中文效果條件，格式：「繁中（日文原文）」或 null",
  "effect": "繁體中文效果文字，格式：「繁中（日文原文）」或 null",
  "continuous_effect": "繁體中文持續效果，格式：「繁中（日文原文）」或 null"
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
ターン→回合、ドロー→抽牌、融合→融合、儀式→儀式、
表側表示→正面攻擊模式、裏側守備表示→背面守備模式。

## 注意
- card_type / attribute / monster_type 直接對應到繁中清單，不要附日文原文
- 文字欄位（description/condition/effect 等）格式務必是「繁中（日文原文）」
- ATK/DEF 直接複製，不需翻譯
- 原始資料為 null 的欄位回傳 null
"""


# ── Image path resolution ──────────────────────────────────────────────────────

def _resolve_image_path(variant: CardVariantModel) -> Path | None:
    if variant.image_source == "user_upload":
        path = get_user_image_path(variant.card_id, variant.rarity)
        if path:
            return path
    if variant.image_path:
        parts = variant.image_path.split("/")
        if len(parts) >= 3:
            path = get_image_path(parts[0], parts[-1])
            if path:
                return path
    return None


def _img_to_b64(img_path: Path) -> tuple[str, str]:
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png", ".webp": "image/webp"}
    media_type = media_map.get(img_path.suffix.lower(), "image/jpeg")
    b64 = base64.b64encode(img_path.read_bytes()).decode()
    return b64, media_type


# ── OpenAI helpers ─────────────────────────────────────────────────────────────

def _call_vision(client, model: str, img_b64: str, media_type: str, prompt: str) -> dict:
    """Call OpenAI with an image + text prompt, return parsed JSON dict."""
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{img_b64}",
                        "detail": "high",
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def _call_text(client, model: str, prompt: str) -> dict:
    """Call OpenAI with a text-only prompt, return parsed JSON dict."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/{card_id:path}/{rarity}", response_model=ScanResult)
def scan_card(
    card_id: str,
    rarity: str,
    extract_model: str = Query(default=DEFAULT_EXTRACT_MODEL,
                               description="Phase 1 vision model (OCR)"),
    translate_model: str = Query(default=DEFAULT_TRANSLATE_MODEL,
                                 description="Phase 2 text model (translation)"),
    db: Session = Depends(get_db),
) -> ScanResult:
    """Two-phase card scan: Phase 1 extracts Japanese text, Phase 2 translates."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")

    variant = (
        db.query(CardVariantModel)
        .filter_by(card_id=card_id, rarity=rarity)
        .first()
    )
    if not variant:
        raise HTTPException(status_code=404, detail=f"Variant {card_id} ({rarity}) not found")

    img_path = _resolve_image_path(variant)
    if not img_path:
        raise HTTPException(status_code=404, detail="No image found for this variant")

    try:
        from openai import OpenAI
    except ImportError:
        raise HTTPException(status_code=503, detail="openai package not installed in backend")

    client = OpenAI(api_key=api_key)
    img_b64, media_type = _img_to_b64(img_path)

    # ── Phase 1: Vision OCR ────────────────────────────────────────────────────
    try:
        raw_data = _call_vision(client, extract_model, img_b64, media_type,
                                _build_extract_prompt())
    except Exception as exc:
        raise HTTPException(status_code=502,
                            detail=f"Phase 1 (OCR) OpenAI error: {exc}") from exc

    valid_raw_keys = CardRawExtract.model_fields.keys()
    raw = CardRawExtract(**{k: v for k, v in raw_data.items() if k in valid_raw_keys})

    # ── Phase 2: Text translation ──────────────────────────────────────────────
    known = _get_known_values(db)
    try:
        translated_data = _call_text(client, translate_model,
                                     _build_translate_prompt(raw, known))
    except Exception as exc:
        raise HTTPException(status_code=502,
                            detail=f"Phase 2 (translate) OpenAI error: {exc}") from exc

    valid_result_keys = set(ScanResult.model_fields.keys()) - {"raw"}
    translated = {k: v for k, v in translated_data.items() if k in valid_result_keys}

    return ScanResult(raw=raw, **translated)
