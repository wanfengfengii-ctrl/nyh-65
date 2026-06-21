from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from database import get_db
from schemas import ReportRequest, ReportResult
from analysis.report import (
    generate_risk_report, generate_drainage_report,
    generate_sediment_report, generate_simulation_report, generate_profile_report
)

router = APIRouter(prefix="/api/reports", tags=["报告输出"])

REPORT_DIR = "./reports"


@router.post("/generate", response_model=ReportResult)
def generate_report(request: ReportRequest, db: Session = Depends(get_db)):
    params = getattr(request, 'parameters', {}) or {}

    if request.report_type == "risk":
        result = generate_risk_report(db, request.culvert_id, request.include_charts or True)
    elif request.report_type == "drainage":
        scenarios = params.get("scenario_ids", [])
        result = generate_drainage_report(db, request.culvert_id, scenarios, request.include_charts or True)
    elif request.report_type == "sediment":
        months = params.get("months", 12)
        result = generate_sediment_report(db, request.culvert_id, months, request.include_charts or True)
    elif request.report_type == "simulation":
        plan_type = params.get("plan_type", "cleaning")
        sim_params = params.get("parameters", {})
        result = generate_simulation_report(db, request.culvert_id, plan_type, sim_params, request.include_charts or True)
    elif request.report_type == "profile":
        result = generate_profile_report(db, request.culvert_id, request.include_charts or True)
    else:
        raise HTTPException(status_code=400, detail="不支持的报告类型")

    if not result:
        raise HTTPException(status_code=404, detail="生成报告失败")
    return result


@router.get("/download/{filename}")
def download_report(filename: str):
    filepath = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="报告文件不存在")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/json"
    )


@router.get("/list")
def list_reports():
    if not os.path.exists(REPORT_DIR):
        return []

    reports = []
    for filename in sorted(os.listdir(REPORT_DIR), reverse=True):
        if filename.endswith(".json"):
            filepath = os.path.join(REPORT_DIR, filename)
            reports.append({
                "filename": filename,
                "file_url": f"/api/reports/download/{filename}",
                "size": os.path.getsize(filepath),
                "created_at": os.path.getctime(filepath)
            })
    return reports
