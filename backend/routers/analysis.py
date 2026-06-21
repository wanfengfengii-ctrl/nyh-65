from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import (
    DrainageCapacityRequest, DrainageCapacityResult,
    SedimentTrendRequest, SedimentTrendResult,
    RiskWarningResult, SimulationRequest, SimulationResult,
    ProfileResult
)
from analysis.drainage import analyze_drainage_capacity
from analysis.sediment import analyze_sediment_trend, identify_risk_sections
from analysis.simulation import simulate_plan
from analysis.profile import generate_profile

router = APIRouter(prefix="/api/analysis", tags=["分析研判"])


@router.post("/drainage-capacity", response_model=List[DrainageCapacityResult])
def get_drainage_capacity(request: DrainageCapacityRequest, db: Session = Depends(get_db)):
    results = analyze_drainage_capacity(db, request.culvert_id, request.scenario_ids)
    if not results:
        raise HTTPException(status_code=404, detail="未找到相关数据")
    return results


@router.post("/sediment-trend", response_model=SedimentTrendResult)
def get_sediment_trend(request: SedimentTrendRequest, db: Session = Depends(get_db)):
    result = analyze_sediment_trend(db, request.culvert_id, request.months or 12)
    if not result:
        raise HTTPException(status_code=404, detail="未找到相关数据")
    return result


@router.get("/risk-warnings/{culvert_id}", response_model=RiskWarningResult)
def get_risk_warnings(culvert_id: int, db: Session = Depends(get_db)):
    result = identify_risk_sections(db, culvert_id)
    if not result:
        raise HTTPException(status_code=404, detail="未找到相关数据")
    return result


@router.post("/simulate", response_model=SimulationResult)
def run_simulation(request: SimulationRequest, db: Session = Depends(get_db)):
    result = simulate_plan(db, request.culvert_id, request.plan_type, request.parameters)
    if not result:
        raise HTTPException(status_code=404, detail="未找到相关数据")
    return result


@router.get("/profile/{culvert_id}", response_model=ProfileResult)
def get_profile(culvert_id: int, db: Session = Depends(get_db)):
    result = generate_profile(db, culvert_id)
    if not result:
        raise HTTPException(status_code=404, detail="未找到相关数据")
    return result
