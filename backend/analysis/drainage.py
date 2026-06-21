import math
from typing import List, Dict, Tuple
import numpy as np
from sqlalchemy.orm import Session
from models import Culvert, Section, Slope, RainScenario, SedimentRecord


def calculate_hydraulic_radius(section: Section) -> float:
    if section.shape == '矩形':
        if section.height and section.width:
            area = section.width * section.height
            perimeter = 2 * (section.width + section.height)
            return area / perimeter if perimeter > 0 else 0
    elif section.shape == '圆形':
        if section.diameter:
            area = math.pi * (section.diameter / 2) ** 2
            perimeter = math.pi * section.diameter
            return area / perimeter if perimeter > 0 else 0
    elif section.shape == '马蹄形':
        if section.width and section.height:
            area = section.width * section.height * 0.785
            perimeter = 2.5 * section.width
            return area / perimeter if perimeter > 0 else 0
    elif section.shape == '拱形':
        if section.width and section.height:
            area = section.width * section.height * 0.87
            perimeter = 2 * section.height + 1.57 * section.width
            return area / perimeter if perimeter > 0 else 0
    return 0


def calculate_flow_capacity(section: Section, slope: float, roughness: float = 0.013) -> float:
    hydraulic_radius = calculate_hydraulic_radius(section)
    if hydraulic_radius <= 0 or slope <= 0:
        return 0

    area = section.area if section.area else 0
    if section.shape == '矩形' and section.height and section.width:
        area = section.width * section.height
    elif section.shape == '圆形' and section.diameter:
        area = math.pi * (section.diameter / 2) ** 2
    elif section.shape == '马蹄形' and section.width and section.height:
        area = section.width * section.height * 0.785
    elif section.shape == '拱形' and section.width and section.height:
        area = section.width * section.height * 0.87

    if area <= 0:
        return 0

    flow_rate = (1 / roughness) * area * (hydraulic_radius ** (2 / 3)) * (slope ** 0.5)
    return flow_rate


def calculate_design_flow(scenario: RainScenario, catchment_area: float, runoff_coefficient: float = 0.6) -> float:
    rainfall_intensity_mm_h = scenario.total_rainfall / scenario.rainfall_duration
    rainfall_intensity_m_s = rainfall_intensity_mm_h / 3600000
    return rainfall_intensity_m_s * catchment_area * runoff_coefficient


def calculate_actual_capacity(db: Session, culvert_id: int) -> float:
    sections = db.query(Section).filter(Section.culvert_id == culvert_id).order_by(Section.station).all()
    slopes = db.query(Slope).filter(Slope.section_id.in_([s.id for s in sections])).all()

    if not sections:
        return 0

    capacities = []
    for section in sections:
        section_slopes = [s for s in slopes if s.section_id == section.id]
        avg_slope = sum(s.slope_value for s in section_slopes) / len(section_slopes) if section_slopes else 0.001

        capacity = calculate_flow_capacity(section, avg_slope)
        capacities.append(capacity)

    return min(capacities) if capacities else 0


def calculate_sediment_impact(db: Session, culvert_id: int, base_capacity: float) -> float:
    latest_sediment = db.query(SedimentRecord).filter(
        SedimentRecord.culvert_id == culvert_id
    ).order_by(SedimentRecord.record_date.desc()).first()

    if not latest_sediment:
        return base_capacity

    reduction_ratio = max(0, 1 - (latest_sediment.sediment_thickness / 1.5) * 0.6)
    return base_capacity * reduction_ratio


def analyze_drainage_capacity(db: Session, culvert_id: int, scenario_ids: List[int]) -> List[Dict]:
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        return []

    base_capacity = calculate_actual_capacity(db, culvert_id)
    actual_capacity = calculate_sediment_impact(db, culvert_id, base_capacity)

    catchment_area = culvert.length * 80

    results = []
    for scenario_id in scenario_ids:
        scenario = db.query(RainScenario).filter(RainScenario.id == scenario_id).first()
        if not scenario:
            continue

        design_flow = calculate_design_flow(scenario, catchment_area)
        overflow = max(0, design_flow - actual_capacity)
        overflow_ratio = overflow / design_flow if design_flow > 0 else 0

        results.append({
            'scenario_id': scenario.id,
            'scenario_name': scenario.name,
            'return_period': scenario.return_period,
            'total_rainfall': scenario.total_rainfall,
            'design_flow': round(design_flow, 3),
            'actual_capacity': round(actual_capacity, 3),
            'overflow': round(overflow, 3),
            'overflow_ratio': round(overflow_ratio, 4),
            'is_sufficient': actual_capacity >= design_flow
        })

    return results
