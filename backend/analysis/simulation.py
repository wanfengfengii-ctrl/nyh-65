from typing import Dict
from sqlalchemy.orm import Session
from models import Culvert, Section, Slope, SedimentRecord
from analysis.drainage import calculate_actual_capacity, calculate_sediment_impact, calculate_flow_capacity


def simulate_cleaning(db: Session, culvert_id: int, cleaning_ratio: float = 1.0) -> Dict:
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        return {}

    original_capacity = calculate_actual_capacity(db, culvert_id)
    original_capacity_with_sediment = calculate_sediment_impact(db, culvert_id, original_capacity)

    latest_sediment = db.query(SedimentRecord).filter(
        SedimentRecord.culvert_id == culvert_id
    ).order_by(SedimentRecord.record_date.desc()).first()

    if latest_sediment:
        remaining_sediment = latest_sediment.sediment_thickness * (1 - cleaning_ratio)
        reduction_ratio = max(0, 1 - (remaining_sediment / 1.5) * 0.6)
        simulated_capacity = original_capacity * reduction_ratio
    else:
        simulated_capacity = original_capacity

    capacity_improvement = simulated_capacity - original_capacity_with_sediment

    segment_length = culvert.length
    avg_width = 1.5
    sediment_volume = segment_length * avg_width * (latest_sediment.sediment_thickness if latest_sediment else 0) * cleaning_ratio
    cost_estimate = sediment_volume * 80 + 2000

    construction_period = f"{max(1, int(segment_length / 50))} 天"

    return {
        'plan_type': '清淤方案',
        'original_capacity': round(original_capacity_with_sediment, 3),
        'simulated_capacity': round(simulated_capacity, 3),
        'capacity_improvement': round(capacity_improvement, 3),
        'cost_estimate': round(cost_estimate, 2),
        'construction_period': construction_period,
        'suggestion': f'清淤比例 {cleaning_ratio * 100}%，预计清除淤积量 {round(sediment_volume, 2)} 立方米'
    }


def simulate_section_expansion(db: Session, culvert_id: int, expansion_ratio: float = 0.2) -> Dict:
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        return {}

    original_capacity = calculate_actual_capacity(db, culvert_id)
    original_capacity_with_sediment = calculate_sediment_impact(db, culvert_id, original_capacity)

    sections = db.query(Section).filter(Section.culvert_id == culvert_id).all()
    slopes = db.query(Slope).filter(Slope.section_id.in_([s.id for s in sections])).all()

    if not sections:
        return {}

    simulated_capacities = []
    for section in sections:
        section_slopes = [s for s in slopes if s.section_id == section.id]
        avg_slope = sum(s.slope_value for s in section_slopes) / len(section_slopes) if section_slopes else 0.001

        expanded_section = Section(
            shape=section.shape,
            width=section.width * (1 + expansion_ratio),
            height=section.height * (1 + expansion_ratio) if section.height else None,
            diameter=section.diameter * (1 + expansion_ratio) if section.diameter else None
        )

        capacity = calculate_flow_capacity(expanded_section, avg_slope)
        simulated_capacities.append(capacity)

    simulated_capacity = min(simulated_capacities) if simulated_capacities else 0
    simulated_capacity = calculate_sediment_impact(db, culvert_id, simulated_capacity)

    capacity_improvement = simulated_capacity - original_capacity_with_sediment

    segment_length = culvert.length
    avg_width = 1.5
    excavation_volume = segment_length * avg_width * avg_width * expansion_ratio
    cost_estimate = excavation_volume * 1200 + 50000

    construction_period = f"{max(7, int(segment_length / 20))} 天"

    return {
        'plan_type': '断面扩建方案',
        'original_capacity': round(original_capacity_with_sediment, 3),
        'simulated_capacity': round(simulated_capacity, 3),
        'capacity_improvement': round(capacity_improvement, 3),
        'cost_estimate': round(cost_estimate, 2),
        'construction_period': construction_period,
        'suggestion': f'断面扩大比例 {expansion_ratio * 100}%，预计开挖量 {round(excavation_volume, 2)} 立方米'
    }


def simulate_slope_adjustment(db: Session, culvert_id: int, new_slope: float) -> Dict:
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        return {}

    original_capacity = calculate_actual_capacity(db, culvert_id)
    original_capacity_with_sediment = calculate_sediment_impact(db, culvert_id, original_capacity)

    sections = db.query(Section).filter(Section.culvert_id == culvert_id).all()

    if not sections:
        return {}

    simulated_capacities = []
    for section in sections:
        capacity = calculate_flow_capacity(section, new_slope)
        simulated_capacities.append(capacity)

    simulated_capacity = min(simulated_capacities) if simulated_capacities else 0
    simulated_capacity = calculate_sediment_impact(db, culvert_id, simulated_capacity)

    capacity_improvement = simulated_capacity - original_capacity_with_sediment

    segment_length = culvert.length
    avg_depth = 2.0
    excavation_volume = segment_length * 2.0 * avg_depth * 0.3
    cost_estimate = excavation_volume * 600 + 30000

    construction_period = f"{max(5, int(segment_length / 30))} 天"

    return {
        'plan_type': '坡度调整方案',
        'original_capacity': round(original_capacity_with_sediment, 3),
        'simulated_capacity': round(simulated_capacity, 3),
        'capacity_improvement': round(capacity_improvement, 3),
        'cost_estimate': round(cost_estimate, 2),
        'construction_period': construction_period,
        'suggestion': f'调整后坡度 {new_slope * 100}‰，预计开挖量 {round(excavation_volume, 2)} 立方米'
    }


def simulate_plan(db: Session, culvert_id: int, plan_type: str, parameters: Dict) -> Dict:
    if plan_type == 'cleaning':
        cleaning_ratio = parameters.get('cleaning_ratio', 1.0)
        return simulate_cleaning(db, culvert_id, cleaning_ratio)
    elif plan_type == 'expansion':
        expansion_ratio = parameters.get('expansion_ratio', 0.2)
        return simulate_section_expansion(db, culvert_id, expansion_ratio)
    elif plan_type == 'slope':
        new_slope = parameters.get('new_slope', 0.005)
        return simulate_slope_adjustment(db, culvert_id, new_slope)
    else:
        return {
            'plan_type': '未知方案',
            'original_capacity': 0,
            'simulated_capacity': 0,
            'capacity_improvement': 0,
            'cost_estimate': 0,
            'construction_period': '未知',
            'suggestion': '不支持的方案类型'
        }
