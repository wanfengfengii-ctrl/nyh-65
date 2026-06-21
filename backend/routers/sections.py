from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Section, Culvert
from schemas import Section as SectionSchema, SectionCreate, SectionUpdate

router = APIRouter(prefix="/api/sections", tags=["断面管理"])


@router.get("/", response_model=List[SectionSchema])
def get_sections(culvert_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Section)
    if culvert_id:
        query = query.filter(Section.culvert_id == culvert_id)
    sections = query.order_by(Section.station).offset(skip).limit(limit).all()
    return sections


@router.get("/{section_id}", response_model=SectionSchema)
def get_section(section_id: int, db: Session = Depends(get_db)):
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="断面不存在")
    return section


@router.post("/", response_model=SectionSchema)
def create_section(section: SectionCreate, db: Session = Depends(get_db)):
    culvert = db.query(Culvert).filter(Culvert.id == section.culvert_id).first()
    if not culvert:
        raise HTTPException(status_code=404, detail="暗渠不存在")

    db_section = Section(**section.dict())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section


@router.put("/{section_id}", response_model=SectionSchema)
def update_section(section_id: int, section: SectionUpdate, db: Session = Depends(get_db)):
    db_section = db.query(Section).filter(Section.id == section_id).first()
    if not db_section:
        raise HTTPException(status_code=404, detail="断面不存在")

    for key, value in section.dict().items():
        setattr(db_section, key, value)
    db.commit()
    db.refresh(db_section)
    return db_section


@router.delete("/{section_id}")
def delete_section(section_id: int, db: Session = Depends(get_db)):
    db_section = db.query(Section).filter(Section.id == section_id).first()
    if not db_section:
        raise HTTPException(status_code=404, detail="断面不存在")
    db.delete(db_section)
    db.commit()
    return {"message": "删除成功"}
