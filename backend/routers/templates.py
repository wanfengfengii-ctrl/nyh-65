from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import CeramicVesselTemplate, VesselProfile
from schemas import (
    CeramicVesselTemplateCreate,
    CeramicVesselTemplateUpdate,
    CeramicVesselTemplate as TemplateSchema,
    TemplateApplyRequest,
)
from analysis.ceramic_analysis import apply_template, identify_key_parts, calculate_dimensions

router = APIRouter(prefix="/api/templates", tags=["标准器型模板库"])


@router.get("", response_model=List[TemplateSchema])
def list_templates(
    category: Optional[str] = None,
    dynasty: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(CeramicVesselTemplate).filter(CeramicVesselTemplate.is_public == True)
    if category:
        query = query.filter(CeramicVesselTemplate.category == category)
    if dynasty:
        query = query.filter(CeramicVesselTemplate.dynasty == dynasty)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (CeramicVesselTemplate.name.like(like))
            | (CeramicVesselTemplate.code.like(like))
            | (CeramicVesselTemplate.description.like(like))
        )
    return query.order_by(CeramicVesselTemplate.category, CeramicVesselTemplate.name).offset(skip).limit(limit).all()


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    results = db.query(
        CeramicVesselTemplate.category,
        CeramicVesselTemplate.dynasty,
    ).distinct().all()
    categories = {}
    for cat, dyn in results:
        if cat not in categories:
            categories[cat] = []
        if dyn and dyn not in categories[cat]:
            categories[cat].append(dyn)
    return {"categories": categories, "total": len(categories)}


@router.get("/{template_id}", response_model=TemplateSchema)
def get_template(template_id: int, db: Session = Depends(get_db)):
    tpl = db.query(CeramicVesselTemplate).filter(CeramicVesselTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    return tpl


@router.post("", response_model=TemplateSchema)
def create_template(template: CeramicVesselTemplateCreate, db: Session = Depends(get_db)):
    existing = db.query(CeramicVesselTemplate).filter(CeramicVesselTemplate.code == template.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"编码 {template.code} 已存在")

    cp_dicts = [p.model_dump() for p in template.control_points]
    kp_dicts = [p.model_dump() for p in template.key_parts] if template.key_parts else None

    key_parts = identify_key_parts(cp_dicts, "mm")
    dims = calculate_dimensions(cp_dicts, "mm")

    tpl = CeramicVesselTemplate(
        name=template.name,
        code=template.code,
        category=template.category,
        dynasty=template.dynasty,
        region=template.region,
        material=template.material,
        typical_height=dims["height"],
        typical_mouth_diameter=dims["mouthDiameter"],
        typical_belly_diameter=dims["bellyDiameter"],
        typical_bottom_diameter=dims["bottomDiameter"],
        typical_volume=dims["volume"],
        control_points=cp_dicts,
        key_parts=kp_dicts if kp_dicts else key_parts,
        parameters=template.parameters,
        description=template.description,
        references=template.references,
        image_url=template.image_url,
        is_public=template.is_public,
        created_by=template.created_by,
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


@router.put("/{template_id}", response_model=TemplateSchema)
def update_template(
    template_id: int,
    template: CeramicVesselTemplateUpdate,
    db: Session = Depends(get_db),
):
    tpl = db.query(CeramicVesselTemplate).filter(CeramicVesselTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")

    cp_dicts = [p.model_dump() for p in template.control_points]
    kp_dicts = [p.model_dump() for p in template.key_parts] if template.key_parts else None
    dims = calculate_dimensions(cp_dicts, "mm")

    tpl.name = template.name
    tpl.code = template.code
    tpl.category = template.category
    tpl.dynasty = template.dynasty
    tpl.region = template.region
    tpl.material = template.material
    tpl.typical_height = dims["height"]
    tpl.typical_mouth_diameter = dims["mouthDiameter"]
    tpl.typical_belly_diameter = dims["bellyDiameter"]
    tpl.typical_bottom_diameter = dims["bottomDiameter"]
    tpl.typical_volume = dims["volume"]
    tpl.control_points = cp_dicts
    tpl.key_parts = kp_dicts if kp_dicts else identify_key_parts(cp_dicts, "mm")
    tpl.parameters = template.parameters
    tpl.description = template.description
    tpl.references = template.references
    tpl.image_url = template.image_url
    tpl.is_public = template.is_public
    tpl.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(tpl)
    return tpl


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    tpl = db.query(CeramicVesselTemplate).filter(CeramicVesselTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.delete(tpl)
    db.commit()
    return {"success": True, "message": "模板已删除"}


@router.post("/{template_id}/apply")
def apply_template_to_profile(
    template_id: int,
    request: TemplateApplyRequest,
    db: Session = Depends(get_db),
):
    tpl = db.query(CeramicVesselTemplate).filter(CeramicVesselTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")

    result = apply_template(
        template_points=tpl.control_points,
        scale_factor=request.scale_factor,
        target_height=request.target_height,
        target_belly_diameter=request.target_belly_diameter,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "应用模板失败"))

    return {
        "template_id": template_id,
        "template_name": tpl.name,
        "template_code": tpl.code,
        "category": tpl.category,
        **result,
    }


@router.get("/{template_id}/preview")
def get_template_preview(template_id: int, db: Session = Depends(get_db)):
    tpl = db.query(CeramicVesselTemplate).filter(CeramicVesselTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")

    cp_dicts = [dict(p) if isinstance(p, dict) else {"id": p.get("id"), "x": p.get("x"), "y": p.get("y")} for p in tpl.control_points]
    dims = calculate_dimensions(cp_dicts, "mm")
    key_parts = identify_key_parts(cp_dicts, "mm")

    return {
        "id": tpl.id,
        "name": tpl.name,
        "code": tpl.code,
        "category": tpl.category,
        "dynasty": tpl.dynasty,
        "control_points": cp_dicts,
        "dimensions": dims,
        "key_parts": key_parts,
        "description": tpl.description,
    }
