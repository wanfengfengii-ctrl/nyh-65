from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from database import get_db
from models import (
    VesselProfile,
    CeramicVesselTemplate,
    VesselVersion,
    RestorationAssessment,
)
from schemas import (
    VesselProfileCreate,
    VesselProfileUpdate,
    VesselProfile as ProfileSchema,
    VesselVersionCreate,
    VesselVersion as VersionSchema,
    RestorationAssessmentCreate,
    RestorationAssessment as AssessmentSchema,
    KeyPartsIdentificationRequest,
    ParametricEditRequest,
    RestorationAssessmentRequest,
)
from analysis.ceramic_analysis import (
    identify_key_parts,
    calculate_dimensions,
    parametric_edit,
)
from analysis.ceramic_report import assess_restoration

router = APIRouter(prefix="/api/vessel-profiles", tags=["器型档案管理"])


@router.get("", response_model=List[ProfileSchema])
def list_profiles(
    condition_status: Optional[str] = None,
    vessel_type: Optional[str] = None,
    dynasty: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(VesselProfile)
    if condition_status:
        query = query.filter(VesselProfile.condition_status == condition_status)
    if vessel_type:
        query = query.filter(VesselProfile.vessel_type == vessel_type)
    if dynasty:
        query = query.filter(VesselProfile.dynasty == dynasty)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (VesselProfile.name.like(like))
            | (VesselProfile.code.like(like))
            | (VesselProfile.description.like(like))
        )
    return query.order_by(VesselProfile.updated_at.desc()).all()


@router.get("/{profile_id}", response_model=ProfileSchema)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(VesselProfile).filter(VesselProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="器型档案不存在")
    return profile


def _auto_calculate_fields(profile_data, cp_dicts):
    dims = calculate_dimensions(cp_dicts, profile_data.get("unit", "mm"))
    key_parts = identify_key_parts(cp_dicts, profile_data.get("unit", "mm"))

    rm_dicts = None
    if profile_data.get("repair_marks"):
        rm_dicts = [r.model_dump() for r in profile_data.repair_marks]

    return dims, key_parts, rm_dicts


@router.post("", response_model=ProfileSchema)
def create_profile(profile: VesselProfileCreate, db: Session = Depends(get_db)):
    existing = db.query(VesselProfile).filter(VesselProfile.code == profile.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"编号 {profile.code} 已存在")

    cp_dicts = [p.model_dump() for p in profile.control_points]
    dims, key_parts, rm_dicts = _auto_calculate_fields(profile, cp_dicts)

    new_profile = VesselProfile(
        name=profile.name,
        code=profile.code,
        template_id=profile.template_id,
        unit=profile.unit,
        vessel_type=profile.vessel_type,
        dynasty=profile.dynasty,
        provenance=profile.provenance,
        material=profile.material,
        condition_status=profile.condition_status,
        control_points=cp_dicts,
        repair_marks=rm_dicts,
        key_parts_identified=key_parts,
        dimensions=dims,
        parameters=profile.parameters,
        is_restored=profile.is_restored,
        restoration_method=profile.restoration_method,
        restoration_confidence=profile.restoration_confidence,
        description=profile.description,
        tags=profile.tags,
        created_by=profile.created_by,
    )
    db.add(new_profile)
    db.flush()

    v1 = VesselVersion(
        profile_id=new_profile.id,
        version_number=1,
        version_label="初始版本",
        change_summary="创建器型档案",
        control_points=cp_dicts,
        repair_marks=rm_dicts,
        dimensions=dims,
        key_parts_identified=key_parts,
        parameters=profile.parameters,
        restoration_confidence=profile.restoration_confidence,
        created_by=profile.created_by,
    )
    db.add(v1)
    db.commit()
    db.refresh(new_profile)
    return new_profile


@router.put("/{profile_id}", response_model=ProfileSchema)
def update_profile(
    profile_id: int,
    profile: VesselProfileUpdate,
    db: Session = Depends(get_db),
):
    db_profile = db.query(VesselProfile).filter(VesselProfile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="器型档案不存在")

    cp_dicts = [p.model_dump() for p in profile.control_points]
    dims, key_parts, rm_dicts = _auto_calculate_fields(profile, cp_dicts)

    old_cp = db_profile.control_points
    cp_changed = json.dumps(old_cp, sort_keys=True) != json.dumps(cp_dicts, sort_keys=True)
    if cp_changed:
        last_version = db.query(VesselVersion).filter(
            VesselVersion.profile_id == profile_id
        ).order_by(VesselVersion.version_number.desc()).first()
        next_num = last_version.version_number + 1 if last_version else 1

        new_version = VesselVersion(
            profile_id=profile_id,
            version_number=next_num,
            version_label=f"V{next_num}",
            change_summary="控制点或参数更新",
            control_points=cp_dicts,
            repair_marks=rm_dicts,
            dimensions=dims,
            key_parts_identified=key_parts,
            parameters=profile.parameters,
            restoration_confidence=profile.restoration_confidence,
            parent_version_id=last_version.id if last_version else None,
            created_by=profile.created_by,
        )
        db.add(new_version)

    db_profile.name = profile.name
    db_profile.code = profile.code
    db_profile.template_id = profile.template_id
    db_profile.unit = profile.unit
    db_profile.vessel_type = profile.vessel_type
    db_profile.dynasty = profile.dynasty
    db_profile.provenance = profile.provenance
    db_profile.material = profile.material
    db_profile.condition_status = profile.condition_status
    db_profile.control_points = cp_dicts
    db_profile.repair_marks = rm_dicts
    db_profile.key_parts_identified = key_parts
    db_profile.dimensions = dims
    db_profile.parameters = profile.parameters
    db_profile.is_restored = profile.is_restored
    db_profile.restoration_method = profile.restoration_method
    db_profile.restoration_confidence = profile.restoration_confidence
    db_profile.description = profile.description
    db_profile.tags = profile.tags
    db_profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_profile)
    return db_profile


@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    db_profile = db.query(VesselProfile).filter(VesselProfile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="器型档案不存在")
    db.delete(db_profile)
    db.commit()
    return {"success": True, "message": "器型档案已删除"}


@router.post("/identify-key-parts")
def api_identify_key_parts(request: KeyPartsIdentificationRequest):
    cp_dicts = [p.model_dump() for p in request.control_points]
    key_parts = identify_key_parts(cp_dicts, request.unit, request.vessel_type_hint)
    dims = calculate_dimensions(cp_dicts, request.unit)
    return {
        "success": True,
        "key_parts": key_parts,
        "dimensions": dims,
        "count": len(key_parts),
    }


@router.post("/parametric-edit")
def api_parametric_edit(request: ParametricEditRequest):
    cp_dicts = [p.model_dump() for p in request.control_points]
    result = parametric_edit(
        cp_dicts,
        request.dimension_type,
        request.target_value,
        request.unit,
        request.preserve_proportions,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "参数化编辑失败"))
    return result


@router.get("/{profile_id}/versions", response_model=List[VersionSchema])
def list_profile_versions(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(VesselProfile).filter(VesselProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="器型档案不存在")
    return db.query(VesselVersion).filter(
        VesselVersion.profile_id == profile_id
    ).order_by(VesselVersion.version_number.desc()).all()


@router.post("/{profile_id}/versions", response_model=VersionSchema)
def create_version(
    profile_id: int,
    version: VesselVersionCreate,
    db: Session = Depends(get_db),
):
    profile = db.query(VesselProfile).filter(VesselProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="器型档案不存在")

    last_version = db.query(VesselVersion).filter(
        VesselVersion.profile_id == profile_id
    ).order_by(VesselVersion.version_number.desc()).first()
    next_num = version.version_number or (last_version.version_number + 1 if last_version else 1)

    cp_dicts = None
    rm_dicts = None
    dims = None
    kp = None
    if version.control_points:
        cp_dicts = [p.model_dump() for p in version.control_points]
        dims = calculate_dimensions(cp_dicts, profile.unit)
        kp = identify_key_parts(cp_dicts, profile.unit)
    if version.repair_marks:
        rm_dicts = [r.model_dump() for r in version.repair_marks]

    new_version = VesselVersion(
        profile_id=profile_id,
        version_number=next_num,
        version_label=version.version_label or f"V{next_num}",
        change_summary=version.change_summary,
        control_points=cp_dicts,
        repair_marks=rm_dicts,
        dimensions=version.dimensions.model_dump() if version.dimensions else dims,
        key_parts_identified=version.key_parts_identified.model_dump() if version.key_parts_identified else kp,
        parameters=version.parameters,
        restoration_confidence=version.restoration_confidence,
        parent_version_id=version.parent_version_id or (last_version.id if last_version else None),
        created_by=version.created_by,
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version


@router.get("/{profile_id}/versions/{version_id}", response_model=VersionSchema)
def get_version(profile_id: int, version_id: int, db: Session = Depends(get_db)):
    version = db.query(VesselVersion).filter(
        VesselVersion.id == version_id,
        VesselVersion.profile_id == profile_id,
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return version


@router.post("/{profile_id}/restore-version/{version_id}", response_model=ProfileSchema)
def restore_version(
    profile_id: int,
    version_id: int,
    db: Session = Depends(get_db),
):
    profile = db.query(VesselProfile).filter(VesselProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="器型档案不存在")
    version = db.query(VesselVersion).filter(
        VesselVersion.id == version_id,
        VesselVersion.profile_id == profile_id,
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    if version.control_points:
        profile.control_points = version.control_points
    if version.repair_marks:
        profile.repair_marks = version.repair_marks
    if version.dimensions:
        profile.dimensions = version.dimensions
    if version.key_parts_identified:
        profile.key_parts_identified = version.key_parts_identified
    if version.parameters:
        profile.parameters = version.parameters
    if version.restoration_confidence is not None:
        profile.restoration_confidence = version.restoration_confidence

    last_v = db.query(VesselVersion).filter(
        VesselVersion.profile_id == profile_id
    ).order_by(VesselVersion.version_number.desc()).first()
    next_num = last_v.version_number + 1 if last_v else 1
    restore_v = VesselVersion(
        profile_id=profile_id,
        version_number=next_num,
        version_label=f"恢复至V{version.version_number}",
        change_summary=f"恢复至版本 {version.version_label or version.version_number}",
        control_points=profile.control_points,
        repair_marks=profile.repair_marks,
        dimensions=profile.dimensions,
        key_parts_identified=profile.key_parts_identified,
        parameters=profile.parameters,
        restoration_confidence=profile.restoration_confidence,
        parent_version_id=last_v.id if last_v else None,
    )
    db.add(restore_v)
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/{profile_id}/assess-restoration", response_model=AssessmentSchema)
def assess_profile_restoration(
    profile_id: int,
    request: Optional[RestorationAssessmentRequest] = None,
    db: Session = Depends(get_db),
):
    profile = db.query(VesselProfile).filter(VesselProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="器型档案不存在")

    cp_dicts = [dict(p) if isinstance(p, dict) else {"id": p.get("id"), "x": p.get("x"), "y": p.get("y")} for p in profile.control_points]

    result = assess_restoration(
        cp_dicts,
        original_points=([p.model_dump() for p in request.original_points] if request and request.original_points else None),
        restored_points=([p.model_dump() for p in request.restored_points] if request and request.restored_points else None),
        unit=request.unit if request else profile.unit,
        restoration_method=request.restoration_method if request else profile.restoration_method,
        template_control_points=(
            [p.model_dump() for p in request.template_control_points]
            if request and request.template_control_points else None
        ),
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "评估失败"))

    assessment = RestorationAssessment(
        profile_id=profile_id,
        overall_confidence=result["overall_confidence"],
        bottom_confidence=result["part_confidences"].get("bottom"),
        mouth_confidence=result["part_confidences"].get("mouth"),
        belly_confidence=result["part_confidences"].get("belly"),
        neck_confidence=result["part_confidences"].get("neck"),
        shoulder_confidence=result["part_confidences"].get("shoulder"),
        foot_confidence=result["part_confidences"].get("foot"),
        fragment_coverage=result["fragment_coverage"],
        gap_count=result["gap_count"],
        critical_gaps=result["critical_gaps"],
        supporting_evidence=result["supporting_evidence"],
        risk_factors=result["risk_factors"],
        recommendations=result["recommendations"],
        assessment_method=result["assessment_method"],
        assessed_by=request.assessed_by if request else None,
    )
    db.add(assessment)

    profile.restoration_confidence = result["overall_confidence"]
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/{profile_id}/assessments", response_model=List[AssessmentSchema])
def list_assessments(profile_id: int, db: Session = Depends(get_db)):
    return db.query(RestorationAssessment).filter(
        RestorationAssessment.profile_id == profile_id
    ).order_by(RestorationAssessment.created_at.desc()).all()
