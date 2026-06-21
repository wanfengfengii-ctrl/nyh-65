from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import RainScenario
from schemas import RainScenario as RainScenarioSchema, RainScenarioCreate, RainScenarioUpdate

router = APIRouter(prefix="/api/scenarios", tags=["降雨情景管理"])


@router.get("/", response_model=List[RainScenarioSchema])
def get_scenarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    scenarios = db.query(RainScenario).order_by(RainScenario.return_period).offset(skip).limit(limit).all()
    return scenarios


@router.get("/default", response_model=RainScenarioSchema)
def get_default_scenario(db: Session = Depends(get_db)):
    scenario = db.query(RainScenario).filter(RainScenario.is_default == True).first()
    if not scenario:
        scenario = db.query(RainScenario).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="未找到降雨情景")
    return scenario


@router.get("/{scenario_id}", response_model=RainScenarioSchema)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.query(RainScenario).filter(RainScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="降雨情景不存在")
    return scenario


@router.post("/", response_model=RainScenarioSchema)
def create_scenario(scenario: RainScenarioCreate, db: Session = Depends(get_db)):
    if scenario.is_default:
        db.query(RainScenario).update({"is_default": False})

    db_scenario = RainScenario(**scenario.dict())
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario


@router.put("/{scenario_id}", response_model=RainScenarioSchema)
def update_scenario(scenario_id: int, scenario: RainScenarioUpdate, db: Session = Depends(get_db)):
    db_scenario = db.query(RainScenario).filter(RainScenario.id == scenario_id).first()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="降雨情景不存在")

    if scenario.is_default:
        db.query(RainScenario).filter(RainScenario.id != scenario_id).update({"is_default": False})

    for key, value in scenario.dict().items():
        setattr(db_scenario, key, value)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario


@router.delete("/{scenario_id}")
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    db_scenario = db.query(RainScenario).filter(RainScenario.id == scenario_id).first()
    if not db_scenario:
        raise HTTPException(status_code=404, detail="降雨情景不存在")
    db.delete(db_scenario)
    db.commit()
    return {"message": "删除成功"}
