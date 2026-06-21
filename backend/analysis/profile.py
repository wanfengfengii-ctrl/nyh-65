from typing import Dict, List
from sqlalchemy.orm import Session
from models import Culvert, Section, Slope, Manhole, SedimentRecord
import numpy as np


def generate_profile(db: Session, culvert_id: int) -> Dict:
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        return {}

    sections = db.query(Section).filter(Section.culvert_id == culvert_id).order_by(Section.station).all()
    manholes = db.query(Manhole).filter(Manhole.culvert_id == culvert_id).order_by(Manhole.station).all()
    slopes = db.query(Slope).filter(Slope.section_id.in_([s.id for s in sections])).all()
    sediment_records = db.query(SedimentRecord).filter(SedimentRecord.culvert_id == culvert_id).all()

    if not sections:
        return {
            'culvert_id': culvert_id,
            'culvert_name': culvert.name,
            'profile_points': [],
            'max_elevation': 0,
            'min_elevation': 0,
            'avg_slope': 0
        }

    base_elevation = 10.0

    profile_points = []
    elevations = []

    manhole_map = {m.station: m for m in manholes}

    for section in sections:
        section_slopes = [s for s in slopes if s.section_id == section.id]

        if section_slopes:
            slope_obj = section_slopes[0]
            if slope_obj.start_elevation is not None:
                elevation = slope_obj.start_elevation
            else:
                elevation = base_elevation - section.station * 0.003
        else:
            elevation = base_elevation - section.station * 0.003

        sediment_thickness = None
        for record in sediment_records:
            if record.start_station <= section.station <= record.end_station:
                sediment_thickness = record.sediment_thickness
                break

        manhole_name = manhole_map.get(section.station, {}).name if section.station in manhole_map else None

        profile_points.append({
            'station': section.station,
            'elevation': round(elevation, 3),
            'section_width': section.width,
            'section_height': section.height,
            'sediment_thickness': round(sediment_thickness, 3) if sediment_thickness else None,
            'manhole_name': manhole_name
        })

        elevations.append(elevation)

    for manhole in manholes:
        existing_stations = [p['station'] for p in profile_points]
        if manhole.station not in existing_stations:
            elevation = base_elevation - manhole.station * 0.003
            if manhole.elevation is not None:
                elevation = manhole.elevation

            profile_points.append({
                'station': manhole.station,
                'elevation': round(elevation, 3),
                'section_width': 0,
                'section_height': None,
                'sediment_thickness': None,
                'manhole_name': manhole.name
            })
            elevations.append(elevation)

    profile_points.sort(key=lambda x: x['station'])

    if len(elevations) >= 2:
        max_elevation = max(elevations)
        min_elevation = min(elevations)
        total_length = max(p['station'] for p in profile_points) - min(p['station'] for p in profile_points)
        avg_slope = (max_elevation - min_elevation) / total_length if total_length > 0 else 0
    else:
        max_elevation = elevations[0] if elevations else 0
        min_elevation = elevations[0] if elevations else 0
        avg_slope = 0

    return {
        'culvert_id': culvert_id,
        'culvert_name': culvert.name,
        'profile_points': profile_points,
        'max_elevation': round(max_elevation, 3),
        'min_elevation': round(min_elevation, 3),
        'avg_slope': round(avg_slope, 5)
    }
