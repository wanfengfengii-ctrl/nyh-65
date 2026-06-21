from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Culvert
from schemas import Culvert as CulvertSchema, CulvertCreate, CulvertUpdate

router = APIRouter(prefix="/api/culverts", tags=["暗渠管理"])


@router.get("/", response_model=List[CulvertSchema])
def get_culverts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    culverts = db.query(Culvert).offset(skip).limit(limit).all()
    return culverts


@router.get("/{culvert_id}", response_model=CulvertSchema)
def get_culvert(culvert_id: int, db: Session = Depends(get_db)):
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        raise HTTPException(status_code=404, detail="暗渠不存在")
    return culvert


@router.post("/", response_model=CulvertSchema)
def create_culvert(culvert: CulvertCreate, db: Session = Depends(get_db)):
    existing = db.query(Culvert).filter(Culvert.code == culvert.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="暗渠编号已存在")
    db_culvert = Culvert(**culvert.dict())
    db.add(db_culvert)
    db.commit()
    db.refresh(db_culvert)
    return db_culvert


@router.put("/{culvert_id}", response_model=CulvertSchema)
def update_culvert(culvert_id: int, culvert: CulvertUpdate, db: Session = Depends(get_db)):
    db_culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not db_culvert:
        raise HTTPException(status_code=404, detail="暗渠不存在")

    existing = db.query(Culvert).filter(
        Culvert.code == culvert.code,
        Culvert.id != culvert_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="暗渠编号已存在")

    for key, value in culvert.dict().items():
        setattr(db_culvert, key, value)
    db.commit()
    db.refresh(db_culvert)
    return db_culvert


@router.delete("/{culvert_id}")
def delete_culvert(culvert_id: int, db: Session = Depends(get_db)):
    db_culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not db_culvert:
        raise HTTPException(status_code=404, detail="暗渠不存在")
    db.delete(db_culvert)
    db.commit()
    return {"message": "删除成功"}
