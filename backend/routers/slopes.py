from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Slope, Section
from schemas import Slope as SlopeSchema, SlopeCreate, SlopeUpdate

router = APIRouter(prefix="/api/slopes", tags=["坡度管理"])


@router.get("/", response_model=List[SlopeSchema])
def get_slopes(section_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Slope)
    if section_id:
        query = query.filter(Slope.section_id == section_id)
    slopes = query.offset(skip).limit(limit).all()
    return slopes


@router.get("/{slope_id}", response_model=SlopeSchema)
def get_slope(slope_id: int, db: Session = Depends(get_db)):
    slope = db.query(Slope).filter(Slope.id == slope_id).first()
    if not slope:
        raise HTTPException(status_code=404, detail="坡度记录不存在")
    return slope


@router.post("/", response_model=SlopeSchema)
def create_slope(slope: SlopeCreate, db: Session = Depends(get_db)):
    section = db.query(Section).filter(Section.id == slope.section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="断面不存在")

    db_slope = Slope(**slope.dict())
    db.add(db_slope)
    db.commit()
    db.refresh(db_slope)
    return db_slope


@router.put("/{slope_id}", response_model=SlopeSchema)
def update_slope(slope_id: int, slope: SlopeUpdate, db: Session = Depends(get_db)):
    db_slope = db.query(Slope).filter(Slope.id == slope_id).first()
    if not db_slope:
        raise HTTPException(status_code=404, detail="坡度记录不存在")

    for key, value in slope.dict().items():
        setattr(db_slope, key, value)
    db.commit()
    db.refresh(db_slope)
    return db_slope


@router.delete("/{slope_id}")
def delete_slope(slope_id: int, db: Session = Depends(get_db)):
    db_slope = db.query(Slope).filter(Slope.id == slope_id).first()
    if not db_slope:
        raise HTTPException(status_code=404, detail="坡度记录不存在")
    db.delete(db_slope)
    db.commit()
    return {"message": "删除成功"}
