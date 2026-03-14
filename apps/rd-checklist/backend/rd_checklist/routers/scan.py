"""Card scanner API — calls OpenAI Vision to extract card info from image."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import SCRAPER_DATA_DIR
from ..database import get_db
from ..models import CardVariantModel
from ..services.image_service import get_image_path, get_user_image_path

router = APIRouter(prefix="/api/scan", tags=["scan"])


# ── Load OPENAI_API_KEY from root .env if not already set ─────────────────────

def _load_dotenv() -> None:
    """Load .env from project root without depending on python-dotenv."""
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


# ── Response schema ───────────────────────────────────────────────────────────

class ScanResult(BaseModel):
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


# ── Prompt helpers ────────────────────────────────────────────────────────────

def _get_known_values(db: Session) -> dict:
    """Fetch distinct enum values from DB for better prompt accuracy."""
    attrs = [
        r[0] for r in db.execute(
            text("SELECT DISTINCT attribute FROM cards"
                 " WHERE attribute IS NOT NULL AND attribute != ''"
                 " ORDER BY attribute")
        ).fetchall()
    ]
    monster_types = [
        r[0] for r in db.execute(
            text("SELECT DISTINCT monster_type FROM cards"
                 " WHERE monster_type IS NOT NULL AND monster_type != ''"
                 "   AND length(monster_type) <= 10"
                 "   AND monster_type NOT LIKE '條件%'"
                 " ORDER BY monster_type")
        ).fetchall()
    ]
    card_types = [
        r[0] for r in db.execute(
            text("SELECT DISTINCT card_type FROM cards"
                 " WHERE card_type IS NOT NULL AND card_type != ''"
                 " ORDER BY card_type")
        ).fetchall()
    ]
    return {
        "attributes":    attrs         or ["光", "暗", "炎", "水", "風", "地"],
        "monster_types": monster_types or ["龍族", "魔法使族", "天使族", "惡魔族", "不死族", "戰士族"],
        "card_types":    card_types    or ["通常怪獸", "效果怪獸", "融合怪獸", "通常魔法", "通常陷阱"],
    }


def _build_prompt(known: dict) -> str:
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

## card_type 可能值（請從以下選一個最符合的）：
{card_types_str}

## attribute 可能值（屬性）：
{attrs}

## monster_type 可能值（種族）：
{types}

## is_legend
卡片上印有「LEGEND」標記時為 true。

## 翻譯術語對照
手札→手牌、デッキ→牌組、フィールド→場上、ライフポイント→生命值、
モンスター→怪獸、魔法カード→魔法卡、罠カード→陷阱卡、
攻撃→攻擊、守備→守備、破壊→破壞、特殊召喚→特殊召喚、
バトルフェイズ→戰鬥階段、メインフェイズ→主要階段、ターン→回合、ドロー→抽牌、
融合→融合、儀式→儀式。

## 欄位對應（Rush Duel 版面由上至下）
- 怪獸卡：卡名 → 屬性+等級 → 卡牌種類/種族 → 圖片 → 召喚條件（若有）→ 條件（若有）→ 效果 → 持續效果 → ATK / DEF
- 魔法/陷阱卡：卡名 → 圖片 → 說明文 → 條件（若有）→ 效果

## 注意
- ATK/DEF 為問號時填 "?"
- 無法辨識或不適用的欄位填 null
"""


# ── Image path resolution ─────────────────────────────────────────────────────

def _resolve_image_path(variant: CardVariantModel) -> Path | None:
    """Return the filesystem path for a variant image (user upload > scraper)."""
    if variant.image_source == "user_upload":
        path = get_user_image_path(variant.card_id, variant.rarity)
        if path:
            return path

    if variant.image_path:
        parts = variant.image_path.split("/")
        if len(parts) >= 3:
            set_id = parts[0]
            filename = parts[-1]
            path = get_image_path(set_id, filename)
            if path:
                return path

    return None


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/{card_id:path}/{rarity}", response_model=ScanResult)
def scan_card(
    card_id: str,
    rarity: str,
    db: Session = Depends(get_db),
) -> ScanResult:
    """Call OpenAI gpt-4o Vision to extract card info from a variant image."""
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
        from openai import OpenAI  # lazy import — only needed when scanning
    except ImportError:
        raise HTTPException(status_code=503, detail="openai package not installed in backend")

    client = OpenAI(api_key=api_key)
    known = _get_known_values(db)
    prompt = _build_prompt(known)

    img_bytes = img_path.read_bytes()
    img_b64 = base64.b64encode(img_bytes).decode()
    suffix = img_path.suffix.lower()
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    media_type = media_map.get(suffix, "image/jpeg")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
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
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {exc}") from exc

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to parse OpenAI response: {exc}") from exc

    valid_keys = ScanResult.model_fields.keys()
    return ScanResult(**{k: v for k, v in data.items() if k in valid_keys})
