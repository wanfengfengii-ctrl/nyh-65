from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Manhole, Culvert
from schemas import Manhole as ManholeSchema, ManholeCreate, ManholeUpdate

router = APIRouter(prefix="/api/manholes", tags=["检查井管理"])


@router.get("/", response_model=List[ManholeSchema])
def get_manholes(culvert_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Manhole)
    if culvert_id:
        query = query.filter(Manhole.culvert_id == culvert_id)
    manholes = query.order_by(Manhole.station).offset(skip).limit(limit).all()
    return manholes


@router.get("/{manhole_id}", response_model=ManholeSchema)
def get_manhole(manhole_id: int, db: Session = Depends(get_db)):
    manhole = db.query(Manhole).filter(Manhole.id == manhole_id).first()
    if not manhole:
        raise HTTPException(status_code=404, detail="检查井不存在")
    return manhole


@router.post("/", response_model=ManholeSchema)
def create_manhole(manhole: ManholeCreate, db: Session = Depends(get_db)):
    culvert = db.query(Culvert).filter(Culvert.id == manhole.culvert_id).first()
    if not culvert:
        raise HTTPException(status_code=404, detail="暗渠不存在")

    db_manhole = Manhole(**manhole.dict())
    db.add(db_manhole)
    db.commit()
    db.refresh(db_manhole)
    return db_manhole


@router.put("/{manhole_id}", response_model=ManholeSchema)
def update_manhole(manhole_id: int, manhole: ManholeUpdate, db: Session = Depends(get_db)):
    db_manhole = db.query(Manhole).filter(Manhole.id == manhole_id).first()
    if not db_manhole:
        raise HTTPException(status_code=404, detail="检查井不存在")

    for key, value in manhole.dict().items():
        setattr(db_manhole, key, value)
    db.commit()
    db.refresh(db_manhole)
    return db_manhole


@router.delete("/{manhole_id}")
def delete_manhole(manhole_id: int, db: Session = Depends(get_db)):
    db_manhole = db.query(Manhole).filter(Manhole.id == manhole_id).first()
    if not db_manhole:
        raise HTTPException(status_code=404, detail="检查井不存在")
    db.delete(db_manhole)
    db.commit()
    return {"message": "删除成功"}
