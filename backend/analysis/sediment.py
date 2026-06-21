import numpy as np
from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Culvert, SedimentRecord


def analyze_sediment_trend(db: Session, culvert_id: int, months: int = 12) -> Dict:
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        return {}

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=months * 30)

    records = db.query(SedimentRecord).filter(
        SedimentRecord.culvert_id == culvert_id,
        SedimentRecord.record_date >= start_date,
        SedimentRecord.record_date <= end_date
    ).order_by(SedimentRecord.record_date).all()

    if not records:
        return {
            'culvert_id': culvert_id,
            'culvert_name': culvert.name,
            'trend_points': [],
            'avg_sediment_rate': 0,
            'max_thickness': 0,
            'predicted_thickness_6m': 0,
            'predicted_thickness_12m': 0,
            'risk_level': '低'
        }

    monthly_data = {}
    for record in records:
        month_key = record.record_date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = []
        monthly_data[month_key].append(record.sediment_thickness)

    trend_points = []
    thickness_values = []
    for month_key in sorted(monthly_data.keys()):
        avg_thickness = np.mean(monthly_data[month_key])
        thickness_values.append(avg_thickness)
        trend_points.append({
            'date': month_key,
            'avg_thickness': round(avg_thickness, 3),
            'accumulated_volume': round(avg_thickness * culvert.length * 1.5, 2)
        })

    if len(thickness_values) >= 2:
        avg_sediment_rate = (thickness_values[-1] - thickness_values[0]) / max(1, len(thickness_values) - 1)
    else:
        avg_sediment_rate = 0.1

    max_thickness = max(thickness_values) if thickness_values else 0
    current_thickness = thickness_values[-1] if thickness_values else 0

    predicted_6m = current_thickness + avg_sediment_rate * 6
    predicted_12m = current_thickness + avg_sediment_rate * 12

    if predicted_12m >= 0.8:
        risk_level = '高'
    elif predicted_12m >= 0.5:
        risk_level = '中'
    else:
        risk_level = '低'

    return {
        'culvert_id': culvert_id,
        'culvert_name': culvert.name,
        'trend_points': trend_points,
        'avg_sediment_rate': round(avg_sediment_rate, 4),
        'max_thickness': round(max_thickness, 3),
        'predicted_thickness_6m': round(max(0, predicted_6m), 3),
        'predicted_thickness_12m': round(max(0, predicted_12m), 3),
        'risk_level': risk_level
    }


def identify_risk_sections(db: Session, culvert_id: int) -> Dict:
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        return {}

    records = db.query(SedimentRecord).filter(
        SedimentRecord.culvert_id == culvert_id
    ).order_by(SedimentRecord.record_date.desc()).all()

    if not records:
        return {
            'culvert_id': culvert_id,
            'culvert_name': culvert.name,
            'total_risk_sections': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'risk_sections': []
        }

    latest_records = {}
    for record in records:
        key = (record.start_station, record.end_station)
        if key not in latest_records:
            latest_records[key] = record

    risk_sections = []
    high_count = 0
    medium_count = 0
    low_count = 0

    for (start, end), record in latest_records.items():
        thickness = record.sediment_thickness

        if thickness >= 0.8:
            risk_level = '高'
            risk_score = 80 + min(20, (thickness - 0.8) * 50)
            high_count += 1
            suggestion = '建议立即清淤，该区域淤积严重，已严重影响排水能力'
        elif thickness >= 0.5:
            risk_level = '中'
            risk_score = 50 + min(30, (thickness - 0.5) * 100)
            medium_count += 1
            suggestion = '建议3个月内安排清淤，该区域淤积已影响排水效率'
        elif thickness >= 0.3:
            risk_level = '低'
            risk_score = 20 + min(30, (thickness - 0.3) * 100)
            low_count += 1
            suggestion = '建议纳入年度清淤计划，定期监测淤积情况'
        else:
            continue

        risk_sections.append({
            'start_station': start,
            'end_station': end,
            'risk_level': risk_level,
            'risk_score': round(risk_score, 1),
            'description': f'桩号 {start} - {end} 米处淤积厚度 {thickness} 米',
            'suggestion': suggestion
        })

    risk_sections.sort(key=lambda x: x['risk_score'], reverse=True)

    return {
        'culvert_id': culvert_id,
        'culvert_name': culvert.name,
        'total_risk_sections': len(risk_sections),
        'high_risk_count': high_count,
        'medium_risk_count': medium_count,
        'low_risk_count': low_count,
        'risk_sections': risk_sections
    }
