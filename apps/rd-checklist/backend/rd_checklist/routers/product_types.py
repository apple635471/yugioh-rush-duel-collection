"""Product type rules — the classification the whole app runs on.

Editing a rule here re-files every set at once: sets do not store a product
type, they are whatever these rules say (see
``services.product_type_service``). The scraper reads the same list through
``GET /api/product-types``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CardSetModel, ProductTypeModel, ProductTypeRuleModel
from ..schemas import (
    ProductTypeCreate,
    ProductTypeOrderUpdate,
    ProductTypeOut,
    ProductTypeUpdate,
    RulePreviewOut,
    RulePreviewRequest,
)
from ..services.product_type_service import (
    classify_set,
    invalidate,
    matching_set_ids,
)

router = APIRouter(prefix="/api/product-types", tags=["product-types"])

_CODE_RE = re.compile(r"^[a-z0-9_]+$")


def _validate_patterns(patterns: list[str]) -> None:
    for pattern in patterns:
        if not pattern.strip():
            raise HTTPException(status_code=400, detail="規則不可為空白")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise HTTPException(
                status_code=400, detail=f"規則 {pattern!r} 不是合法的正規表示式：{exc}"
            ) from exc


def _validate_code(code: str) -> str:
    code = code.strip().lower()
    if not _CODE_RE.match(code):
        raise HTTPException(
            status_code=400, detail="代號只能用小寫英文、數字與底線"
        )
    return code


def _replace_rules(db: Session, code: str, patterns: list[str]) -> None:
    db.query(ProductTypeRuleModel).filter_by(product_type_code=code).delete(
        synchronize_session=False
    )
    for order, pattern in enumerate(patterns):
        db.add(
            ProductTypeRuleModel(
                product_type_code=code, pattern=pattern.strip(), sort_order=order
            )
        )


def _to_out(pt: ProductTypeModel, counts: dict[str, int]) -> ProductTypeOut:
    return ProductTypeOut(
        code=pt.code,
        name_en=pt.name_en,
        name_zh=pt.name_zh,
        group_label=pt.group_label,
        color=pt.color,
        sort_order=pt.sort_order,
        is_fallback=pt.is_fallback,
        rules=[r.pattern for r in sorted(pt.rules, key=lambda r: (r.sort_order, r.id))],
        set_count=counts.get(pt.code, 0),
    )


def _set_counts(db: Session) -> dict[str, int]:
    """How many sets each type currently claims, by running the rules."""
    counts: dict[str, int] = {}
    for (set_id,) in db.query(CardSetModel.set_id).all():
        code = classify_set(set_id)
        counts[code] = counts.get(code, 0) + 1
    return counts


def _listing(db: Session) -> list[ProductTypeOut]:
    invalidate()  # rules may have just changed
    counts = _set_counts(db)
    types = (
        db.query(ProductTypeModel)
        .order_by(ProductTypeModel.sort_order, ProductTypeModel.code)
        .all()
    )
    return [_to_out(pt, counts) for pt in types]


@router.get("", response_model=list[ProductTypeOut])
def list_product_types(db: Session = Depends(get_db)):
    """Every product type, its rules, and how many sets it currently holds."""
    return _listing(db)


@router.post("", response_model=list[ProductTypeOut], status_code=201)
def create_product_type(body: ProductTypeCreate, db: Session = Depends(get_db)):
    code = _validate_code(body.code)
    if db.query(ProductTypeModel).filter_by(code=code).first():
        raise HTTPException(status_code=409, detail=f"代號 {code} 已經存在")
    _validate_patterns(body.rules)

    if body.sort_order is None:
        highest = db.query(ProductTypeModel).count()
        sort_order = highest
    else:
        sort_order = body.sort_order

    db.add(
        ProductTypeModel(
            code=code,
            name_en=body.name_en or code,
            name_zh=body.name_zh or None,
            group_label=body.group_label,
            color=body.color,
            sort_order=sort_order,
            is_fallback=False,
        )
    )
    _replace_rules(db, code, body.rules)
    db.commit()
    return _listing(db)


@router.patch("/{code}", response_model=list[ProductTypeOut])
def update_product_type(
    code: str, body: ProductTypeUpdate, db: Session = Depends(get_db)
):
    pt = db.query(ProductTypeModel).filter_by(code=code).first()
    if not pt:
        raise HTTPException(status_code=404, detail=f"找不到產品類型 {code}")

    updates = body.model_dump(exclude_unset=True)

    if "rules" in updates and updates["rules"] is not None:
        if pt.is_fallback and updates["rules"]:
            raise HTTPException(
                status_code=400, detail="fallback 類型不能有規則——它收的是沒人認領的卡組"
            )
        _validate_patterns(updates["rules"])

    new_code = pt.code
    if "code" in updates and updates["code"] and updates["code"] != pt.code:
        new_code = _validate_code(updates["code"])
        if db.query(ProductTypeModel).filter_by(code=new_code).first():
            raise HTTPException(status_code=409, detail=f"代號 {new_code} 已經存在")

    for field in ("name_en", "group_label", "color", "sort_order"):
        if field in updates and updates[field] is not None:
            setattr(pt, field, updates[field])
    if "name_zh" in updates:
        pt.name_zh = updates["name_zh"] or None

    if "rules" in updates and updates["rules"] is not None:
        _replace_rules(db, pt.code, updates["rules"])

    if new_code != pt.code:
        # Sets are classified by rule, so a rename moves nothing but the
        # rules' foreign key (and the /sets/<code> URL).
        db.query(ProductTypeRuleModel).filter_by(product_type_code=pt.code).update(
            {"product_type_code": new_code}, synchronize_session=False
        )
        pt.code = new_code

    pt.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    return _listing(db)


@router.delete("/{code}", response_model=list[ProductTypeOut])
def delete_product_type(code: str, db: Session = Depends(get_db)):
    """Remove a type; the sets it held fall through to the other rules."""
    pt = db.query(ProductTypeModel).filter_by(code=code).first()
    if not pt:
        raise HTTPException(status_code=404, detail=f"找不到產品類型 {code}")
    if pt.is_fallback:
        raise HTTPException(
            status_code=400, detail="不能刪除 fallback 類型——沒人認領的卡組要有地方去"
        )

    db.query(ProductTypeRuleModel).filter_by(product_type_code=code).delete(
        synchronize_session=False
    )
    db.delete(pt)
    db.commit()
    return _listing(db)


@router.put("/order", response_model=list[ProductTypeOut])
def reorder_product_types(body: ProductTypeOrderUpdate, db: Session = Depends(get_db)):
    """Set the display order — which is also the order rules are tried in."""
    for order, code in enumerate(body.codes):
        pt = db.query(ProductTypeModel).filter_by(code=code).first()
        if pt:
            pt.sort_order = order
    db.commit()
    return _listing(db)


@router.post("/preview", response_model=RulePreviewOut)
def preview_rules(body: RulePreviewRequest, db: Session = Depends(get_db)):
    """Which sets these patterns catch — feedback while editing a rule."""
    set_ids = [row[0] for row in db.query(CardSetModel.set_id).all()]
    set_ids.sort()
    matched = matching_set_ids(body.patterns, set_ids)
    # A set can match here and still belong elsewhere: an earlier type wins.
    claimed = {s: classify_set(s) for s in matched}
    return RulePreviewOut(set_ids=matched, claimed_elsewhere=claimed)
