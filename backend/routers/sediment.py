from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import SedimentRecord, Culvert
from schemas import SedimentRecord as SedimentRecordSchema, SedimentRecordCreate, SedimentRecordUpdate

router = APIRouter(prefix="/api/sediment", tags=["淤积记录管理"])


@router.get("/", response_model=List[SedimentRecordSchema])
def get_sediment_records(culvert_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(SedimentRecord)
    if culvert_id:
        query = query.filter(SedimentRecord.culvert_id == culvert_id)
    records = query.order_by(SedimentRecord.record_date.desc()).offset(skip).limit(limit).all()
    return records


@router.get("/{record_id}", response_model=SedimentRecordSchema)
def get_sediment_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(SedimentRecord).filter(SedimentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="淤积记录不存在")
    return record


@router.post("/", response_model=SedimentRecordSchema)
def create_sediment_record(record: SedimentRecordCreate, db: Session = Depends(get_db)):
    culvert = db.query(Culvert).filter(Culvert.id == record.culvert_id).first()
    if not culvert:
        raise HTTPException(status_code=404, detail="暗渠不存在")

    if not record.sediment_volume:
        length = record.end_station - record.start_station
        record.sediment_volume = length * 1.5 * record.sediment_thickness

    db_record = SedimentRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.put("/{record_id}", response_model=SedimentRecordSchema)
def update_sediment_record(record_id: int, record: SedimentRecordUpdate, db: Session = Depends(get_db)):
    db_record = db.query(SedimentRecord).filter(SedimentRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="淤积记录不存在")

    if not record.sediment_volume:
        length = record.end_station - record.start_station
        record.sediment_volume = length * 1.5 * record.sediment_thickness

    for key, value in record.dict().items():
        setattr(db_record, key, value)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.delete("/{record_id}")
def delete_sediment_record(record_id: int, db: Session = Depends(get_db)):
    db_record = db.query(SedimentRecord).filter(SedimentRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="淤积记录不存在")
    db.delete(db_record)
    db.commit()
    return {"message": "删除成功"}
