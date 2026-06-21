from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import os

from database import get_db
from models import (
    VesselProfile,
    DifferenceAnalysis as DifferenceAnalysisModel,
    ResearchReport as ResearchReportModel,
    CeramicVesselTemplate,
)
from schemas import (
    DifferenceAnalysisCreate,
    DifferenceAnalysis as DiffSchema,
    DifferenceAnalysisRequest,
    ResearchReportCreate,
    ResearchReport as ReportSchema,
    ResearchReportGenerateRequest,
)
from analysis.ceramic_analysis import analyze_differences
from analysis.ceramic_report import generate_research_report

router = APIRouter(prefix="/api/ceramic-analysis", tags=["器型差异分析与研究报告"])

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ceramic_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


@router.post("/difference-analysis")
def api_difference_analysis(request: DifferenceAnalysisRequest):
    cp_a = [p.model_dump() for p in request.profile_a_control_points]
    cp_b = [p.model_dump() for p in request.profile_b_control_points]

    result = analyze_differences(
        cp_a, cp_b,
        profile_a_name=request.profile_a_name,
        profile_b_name=request.profile_b_name,
        unit=request.unit,
        sample_count=request.sample_count,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "差异分析失败"))
    return result


@router.post("/difference-analysis/save", response_model=DiffSchema)
def save_difference_analysis(
    data: DifferenceAnalysisCreate,
    db: Session = Depends(get_db),
):
    if data.profile_a_id:
        p = db.query(VesselProfile).filter(VesselProfile.id == data.profile_a_id).first()
        if not p:
            raise HTTPException(status_code=404, detail=f"器型A (id={data.profile_a_id}) 不存在")
    if data.profile_b_id:
        p = db.query(VesselProfile).filter(VesselProfile.id == data.profile_b_id).first()
        if not p:
            raise HTTPException(status_code=404, detail=f"器型B (id={data.profile_b_id}) 不存在")

    hd_dicts = [h.model_dump() for h in data.heatmap_data] if data.heatmap_data else None
    kd_dicts = [k.model_dump() for k in data.key_differences] if data.key_differences else None

    record = DifferenceAnalysisModel(
        name=data.name,
        profile_a_id=data.profile_a_id,
        profile_b_id=data.profile_b_id,
        template_id=data.template_id,
        analysis_type=data.analysis_type,
        heatmap_data=hd_dicts,
        key_differences=kd_dicts,
        overall_similarity=data.overall_similarity,
        dimension_differences=data.dimension_differences,
        description=data.description,
        created_by=data.created_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/difference-analyses", response_model=List[DiffSchema])
def list_difference_analyses(
    profile_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(DifferenceAnalysisModel)
    if profile_id:
        query = query.filter(
            (DifferenceAnalysisModel.profile_a_id == profile_id)
            | (DifferenceAnalysisModel.profile_b_id == profile_id)
        )
    return query.order_by(DifferenceAnalysisModel.created_at.desc()).all()


@router.get("/difference-analyses/{analysis_id}", response_model=DiffSchema)
def get_difference_analysis(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(DifferenceAnalysisModel).filter(DifferenceAnalysisModel.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="差异分析记录不存在")
    return record


@router.delete("/difference-analyses/{analysis_id}")
def delete_difference_analysis(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(DifferenceAnalysisModel).filter(DifferenceAnalysisModel.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="差异分析记录不存在")
    db.delete(record)
    db.commit()
    return {"success": True, "message": "分析记录已删除"}


def _get_profile_with_template(profile_id: int, db: Session) -> dict:
    profile = db.query(VesselProfile).filter(VesselProfile.id == profile_id).first()
    if not profile:
        return None
    template = None
    if profile.template_id:
        tpl = db.query(CeramicVesselTemplate).filter(CeramicVesselTemplate.id == profile.template_id).first()
        if tpl:
            template = {
                "id": tpl.id,
                "name": tpl.name,
                "code": tpl.code,
                "category": tpl.category,
                "dynasty": tpl.dynasty,
                "region": tpl.region,
                "control_points": tpl.control_points,
            }
    return {
        "id": profile.id,
        "name": profile.name,
        "code": profile.code,
        "template_id": profile.template_id,
        "unit": profile.unit,
        "vessel_type": profile.vessel_type,
        "dynasty": profile.dynasty,
        "provenance": profile.provenance,
        "material": profile.material,
        "condition_status": profile.condition_status,
        "control_points": profile.control_points,
        "repair_marks": profile.repair_marks,
        "key_parts_identified": profile.key_parts_identified,
        "dimensions": profile.dimensions,
        "parameters": profile.parameters,
        "is_restored": profile.is_restored,
        "restoration_method": profile.restoration_method,
        "restoration_confidence": profile.restoration_confidence,
        "description": profile.description,
        "tags": profile.tags,
        "template": template,
    }


@router.post("/generate-report")
def api_generate_report(
    request: ResearchReportGenerateRequest,
    db: Session = Depends(get_db),
):
    profile_data = _get_profile_with_template(request.profile_id, db)
    if not profile_data:
        raise HTTPException(status_code=404, detail="器型档案不存在")

    report_data = generate_research_report(
        profile_data=profile_data,
        report_type=request.report_type,
        include_sections=request.include_sections,
        author=request.author,
        keywords=request.keywords,
        custom_title=request.custom_title,
    )

    report_code = f"RPT-{request.profile_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    filename = f"{report_code}.json"
    filepath = os.path.join(REPORTS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    conclusions_list = report_data.get("conclusions", [])
    record = ResearchReportModel(
        profile_id=request.profile_id,
        title=report_data["title"],
        report_type=request.report_type,
        content=report_data,
        sections=report_data.get("sections"),
        summary=report_data.get("summary"),
        conclusions=conclusions_list,
        file_path=filepath,
        file_format="json",
        author=report_data.get("author"),
        keywords=report_data.get("keywords"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "report_id": record.id,
        "title": record.title,
        "filename": filename,
        "created_at": record.created_at.isoformat(),
        "summary": report_data.get("summary"),
        "conclusions": conclusions_list,
        "sections_count": len(report_data.get("sections", [])),
    }


@router.post("/reports", response_model=ReportSchema)
def save_report(report: ResearchReportCreate, db: Session = Depends(get_db)):
    profile = db.query(VesselProfile).filter(VesselProfile.id == report.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="器型档案不存在")

    record = ResearchReportModel(
        profile_id=report.profile_id,
        title=report.title,
        report_type=report.report_type,
        content=report.content,
        sections=report.sections,
        summary=report.summary,
        conclusions=report.conclusions,
        file_path=report.file_path,
        file_format=report.file_format,
        author=report.author,
        keywords=report.keywords,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/reports", response_model=List[ReportSchema])
def list_reports(
    profile_id: Optional[int] = None,
    report_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ResearchReportModel)
    if profile_id:
        query = query.filter(ResearchReportModel.profile_id == profile_id)
    if report_type:
        query = query.filter(ResearchReportModel.report_type == report_type)
    return query.order_by(ResearchReportModel.created_at.desc()).all()


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    record = db.query(ResearchReportModel).filter(ResearchReportModel.id == report_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="报告不存在")

    filepath = record.file_path
    content = record.content
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = json.load(f)
        except Exception:
            pass

    return {
        "id": record.id,
        "profile_id": record.profile_id,
        "title": record.title,
        "report_type": record.report_type,
        "summary": record.summary,
        "conclusions": record.conclusions,
        "author": record.author,
        "keywords": record.keywords,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
        "content": content,
        "sections": record.sections,
    }


@router.delete("/reports/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    record = db.query(ResearchReportModel).filter(ResearchReportModel.id == report_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="报告不存在")
    if record.file_path and os.path.exists(record.file_path):
        try:
            os.remove(record.file_path)
        except Exception:
            pass
    db.delete(record)
    db.commit()
    return {"success": True, "message": "报告已删除"}


@router.get("/reports/{report_id}/export")
def export_report(report_id: int, format: str = "json", db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    import csv
    import io

    record = db.query(ResearchReportModel).filter(ResearchReportModel.id == report_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="报告不存在")

    content = record.content
    if not content:
        raise HTTPException(status_code=400, detail="报告内容为空")

    if format == "json":
        filename = f"报告_{record.id}_{record.title[:20]}.json"
        filepath = os.path.join(REPORTS_DIR, f"export_{report_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        return FileResponse(filepath, media_type="application/json", filename=filename)

    elif format == "csv":
        filename = f"报告_{record.id}_{record.title[:20]}.csv"
        filepath = os.path.join(REPORTS_DIR, f"export_{report_id}.csv")
        dims = content.get("raw_dimensions", {})
        rows = [
            ["项目", "数值", "单位"],
            ["通高", dims.get("height", ""), record.content.get("basic_info", {}).get("items", [{}])[8].get("value", "mm") if isinstance(record.content, dict) else "mm"],
            ["口径", dims.get("mouthDiameter", ""), ""],
            ["腹径", dims.get("bellyDiameter", ""), ""],
            ["底径", dims.get("bottomDiameter", ""), ""],
            ["容量(mL)", dims.get("volume", ""), ""],
            ["", "", ""],
            ["摘要", content.get("summary", ""), ""],
        ]
        for c in content.get("conclusions", []):
            rows.append(["结论", c, ""])
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        return FileResponse(filepath, media_type="text/csv", filename=filename)

    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")


@router.get("/reports/{report_id}/download")
def download_report_file(report_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    record = db.query(ResearchReportModel).filter(ResearchReportModel.id == report_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="报告不存在")
    if not record.file_path or not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="报告文件不存在")
    filename = os.path.basename(record.file_path)
    return FileResponse(record.file_path, media_type="application/json", filename=filename)
