import os
import json
import uuid
from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session
from models import Culvert
from analysis.drainage import analyze_drainage_capacity
from analysis.sediment import analyze_sediment_trend, identify_risk_sections
from analysis.profile import generate_profile

REPORT_DIR = "./reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def generate_risk_report(db: Session, culvert_id: int, include_charts: bool = True) -> Dict:
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        return {}

    report_id = str(uuid.uuid4())
    filename = f"风险评估报告_{culvert.code}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    filepath = os.path.join(REPORT_DIR, filename)

    sediment_trend = analyze_sediment_trend(db, culvert_id)
    risk_warnings = identify_risk_sections(db, culvert_id)
    profile = generate_profile(db, culvert_id)

    report = {
        'report_id': report_id,
        'report_type': '风险评估报告',
        'generated_at': datetime.now().isoformat(),
        'culvert_info': {
            'id': culvert.id,
            'name': culvert.name,
            'code': culvert.code,
            'location': culvert.location,
            'length': culvert.length,
            'material': culvert.material,
            'construction_year': culvert.construction_year,
            'status': culvert.status
        },
        'sediment_trend_analysis': sediment_trend,
        'risk_warnings': risk_warnings,
        'profile_data': profile,
        'summary': {
            'overall_risk_level': sediment_trend.get('risk_level', '低'),
            'total_risk_sections': risk_warnings.get('total_risk_sections', 0),
            'high_risk_count': risk_warnings.get('high_risk_count', 0),
            'medium_risk_count': risk_warnings.get('medium_risk_count', 0),
            'low_risk_count': risk_warnings.get('low_risk_count', 0),
            'recommendations': generate_recommendations(sediment_trend, risk_warnings)
        },
        'include_charts': include_charts
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return {
        'report_id': report_id,
        'filename': filename,
        'file_url': f'/api/reports/download/{filename}',
        'created_at': datetime.now()
    }


def generate_drainage_report(db: Session, culvert_id: int, scenario_ids: list, include_charts: bool = True) -> Dict:
    culvert = db.query(Culvert).filter(Culvert.id == culvert_id).first()
    if not culvert:
        return {}

    report_id = str(uuid.uuid4())
    filename = f"排水能力分析报告_{culvert.code}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    filepath = os.path.join(REPORT_DIR, filename)

    drainage_analysis = analyze_drainage_capacity(db, culvert_id, scenario_ids)
    profile = generate_profile(db, culvert_id)

    insufficient_scenarios = [s for s in drainage_analysis if not s['is_sufficient']]
    max_overflow_ratio = max([s['overflow_ratio'] for s in drainage_analysis], default=0)

    if max_overflow_ratio > 0.3:
        overall_assessment = '排水能力严重不足'
    elif max_overflow_ratio > 0.1:
        overall_assessment = '排水能力不足'
    elif insufficient_scenarios:
        overall_assessment = '部分情景排水能力不足'
    else:
        overall_assessment = '排水能力充足'

    report = {
        'report_id': report_id,
        'report_type': '排水能力分析报告',
        'generated_at': datetime.now().isoformat(),
        'culvert_info': {
            'id': culvert.id,
            'name': culvert.name,
            'code': culvert.code,
            'location': culvert.location,
            'length': culvert.length,
            'material': culvert.material,
            'construction_year': culvert.construction_year,
            'status': culvert.status
        },
        'drainage_capacity_analysis': drainage_analysis,
        'profile_data': profile,
        'summary': {
            'overall_assessment': overall_assessment,
            'total_scenarios': len(drainage_analysis),
            'insufficient_scenarios': len(insufficient_scenarios),
            'max_overflow_ratio': round(max_overflow_ratio, 4),
            'recommendations': generate_drainage_recommendations(drainage_analysis)
        },
        'include_charts': include_charts
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return {
        'report_id': report_id,
        'filename': filename,
        'file_url': f'/api/reports/download/{filename}',
        'created_at': datetime.now()
    }


def generate_recommendations(sediment_trend: Dict, risk_warnings: Dict) -> list:
    recommendations = []

    risk_level = sediment_trend.get('risk_level', '低')
    high_count = risk_warnings.get('high_risk_count', 0)
    medium_count = risk_warnings.get('medium_risk_count', 0)

    if risk_level == '高' or high_count > 0:
        recommendations.append('立即对高风险区段进行清淤作业，消除安全隐患')
    if risk_level == '中' or medium_count > 0:
        recommendations.append('在3个月内安排对中风险区段的清淤工作')
    recommendations.append('建立定期监测机制，每季度进行一次淤积检测')
    recommendations.append('完善排水系统维护档案，记录每次清淤和检修情况')
    recommendations.append('根据淤积速率预测，制定年度清淤计划')

    return recommendations


def generate_drainage_recommendations(drainage_analysis: list) -> list:
    recommendations = []

    insufficient_scenarios = [s for s in drainage_analysis if not s['is_sufficient']]

    if insufficient_scenarios:
        high_return_insufficient = [s for s in insufficient_scenarios if s['return_period'] >= 50]
        if high_return_insufficient:
            recommendations.append('建议对排水系统进行升级改造，以满足高重现期降雨的排水需求')

        medium_return_insufficient = [s for s in insufficient_scenarios if 10 <= s['return_period'] < 50]
        if medium_return_insufficient:
            recommendations.append('建议考虑清淤或局部断面扩建，提升排水能力')

        recommendations.append('建立应急排水预案，在暴雨期间加强巡查')

    recommendations.append('定期对排水系统进行维护清淤，保持设计排水能力')

    return recommendations
