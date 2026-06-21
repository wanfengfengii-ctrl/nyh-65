from typing import List, Dict, Any, Optional
from analysis.ceramic_analysis import (
    sample_curve_points,
    calculate_dimensions,
    identify_key_parts,
)
import math
from datetime import datetime


def assess_restoration(
    control_points: List[Dict[str, float]],
    original_points: Optional[List[Dict[str, float]]] = None,
    restored_points: Optional[List[Dict[str, float]]] = None,
    unit: str = "mm",
    restoration_method: Optional[str] = None,
    template_control_points: Optional[List[Dict[str, float]]] = None,
) -> Dict[str, Any]:
    if len(control_points) < 3:
        return {
            "success": False,
            "error": "控制点数量不足，至少需要3个控制点",
        }

    if original_points is None:
        original_points = list(control_points)

    all_points = restored_points if restored_points else control_points

    dims = calculate_dimensions(all_points, unit)
    key_parts = identify_key_parts(all_points, unit)

    sampled = sample_curve_points(all_points, 40)
    if not sampled:
        return {"success": False, "error": "无法采样曲线"}

    xs = [p["x"] for p in sampled]
    ys = [p["y"] for p in sampled]
    min_y = min(ys)
    max_y = max(ys)
    height_range = max_y - min_y

    original_sorted = sorted(original_points, key=lambda p: p["y"])
    restored_sorted = sorted(all_points, key=lambda p: p["y"])

    restored_point_count = len(restored_sorted) - len(original_sorted) if restored_points else 0
    original_y_set = set()
    for op in original_sorted:
        for y in range(int(op["y"] - 0.5), int(op["y"] + 1.5)):
            original_y_set.add(y)

    fragment_heights = []
    for p in original_sorted:
        fragment_heights.append(p["y"])
    fragment_coverage_pct = 0
    if height_range > 0 and len(fragment_heights) > 1:
        covered = 0
        for i in range(len(fragment_heights) - 1):
            gap = fragment_heights[i + 1] - fragment_heights[i]
            if gap <= height_range * 0.15:
                covered += gap
        covered += height_range * 0.05 * len(fragment_heights)
        fragment_coverage_pct = max(0, min(1, covered / height_range))

    gaps = []
    if height_range > 0 and len(original_sorted) > 1:
        for i in range(len(original_sorted) - 1):
            gap = original_sorted[i + 1]["y"] - original_sorted[i]["y"]
            relative_gap = gap / height_range
            if relative_gap > 0.1:
                gaps.append({
                    "startY": original_sorted[i]["y"],
                    "endY": original_sorted[i + 1]["y"],
                    "gapSize": gap,
                    "relativeSize": relative_gap,
                    "isCritical": relative_gap > 0.25,
                    "zone": _get_zone_name((original_sorted[i]["y"] - min_y) / height_range),
                })

        if original_sorted[0]["y"] > min_y + height_range * 0.02:
            gap = original_sorted[0]["y"] - min_y
            gaps.append({
                "startY": min_y,
                "endY": original_sorted[0]["y"],
                "gapSize": gap,
                "relativeSize": gap / height_range,
                "isCritical": gap > height_range * 0.2,
                "zone": "底部",
                "position": "bottom_missing"
            })

        if original_sorted[-1]["y"] < max_y - height_range * 0.02:
            gap = max_y - original_sorted[-1]["y"]
            gaps.append({
                "startY": original_sorted[-1]["y"],
                "endY": max_y,
                "gapSize": gap,
                "relativeSize": gap / height_range,
                "isCritical": gap > height_range * 0.2,
                "zone": "口沿",
                "position": "top_missing"
            })

    critical_gaps = [g for g in gaps if g["isCritical"]]

    part_confidences = {}
    key_parts_by_zone = {kp.get("zone"): kp for kp in key_parts}

    for zone_name in ["bottom", "foot", "belly", "shoulder", "neck", "mouth"]:
        kp = key_parts_by_zone.get(zone_name)
        if not kp:
            part_confidences[zone_name] = None
            continue

        zone_start = kp["startY"]
        zone_end = kp["endY"]
        zone_mid = (zone_start + zone_end) / 2

        has_original_data = False
        original_points_in_zone = 0
        for op in original_sorted:
            if zone_start - height_range * 0.02 <= op["y"] <= zone_end + height_range * 0.02:
                has_original_data = True
                original_points_in_zone += 1

        gap_in_zone = False
        for g in gaps:
            if not (g["endY"] < zone_start or g["startY"] > zone_end):
                overlap = min(g["endY"], zone_end) - max(g["startY"], zone_start)
                zone_height = zone_end - zone_start
                if zone_height > 0 and overlap / zone_height > 0.3:
                    gap_in_zone = True
                    break

        base_conf = 1.0

        if not has_original_data:
            base_conf -= 0.4
        elif original_points_in_zone == 1:
            base_conf -= 0.15
        elif original_points_in_zone == 2:
            base_conf -= 0.05

        if gap_in_zone:
            base_conf -= 0.2

        if zone_name in ["neck", "foot"] and restoration_method:
            if restoration_method == "保守":
                base_conf += 0.05
            elif restoration_method == "大胆":
                base_conf -= 0.1

        if template_control_points and has_original_data:
            try:
                template_dims = calculate_dimensions(template_control_points, unit)
                zone_diameter = kp.get("diameter")
                if zone_diameter and template_dims:
                    zone_ratio = _get_zone_diameter_ratio(zone_name, dims, template_dims)
                    if zone_ratio:
                        ratio_diff = abs(1 - zone_ratio)
                        if ratio_diff < 0.05:
                            base_conf += 0.05
                        elif ratio_diff > 0.2:
                            base_conf -= 0.1
            except Exception:
                pass

        part_confidences[zone_name] = max(0.1, min(0.99, base_conf))

    has_all_parts = all(v is not None for v in part_confidences.values())
    valid_confs = [v for v in part_confidences.values() if v is not None]
    overall_conf = sum(valid_confs) / len(valid_confs) if valid_confs else 0.5

    coverage_weight = 0.3
    gap_weight = 0.3
    part_weight = 0.4

    gap_penalty = 1.0 - (len(critical_gaps) * 0.15)
    gap_penalty = max(0.4, gap_penalty)

    overall_confidence = (
        fragment_coverage_pct * coverage_weight
        + gap_penalty * gap_weight
        + overall_conf * part_weight
    )
    overall_confidence = max(0.1, min(0.98, overall_confidence))

    supporting_evidence = []
    if fragment_coverage_pct >= 0.7:
        supporting_evidence.append({
            "type": "fragment_coverage",
            "label": "残片覆盖率高",
            "detail": f"现存残片高度覆盖率达到 {fragment_coverage_pct * 100:.1f}%",
            "positive": True,
        })
    elif fragment_coverage_pct >= 0.4:
        supporting_evidence.append({
            "type": "fragment_coverage",
            "label": "残片覆盖率中等",
            "detail": f"现存残片高度覆盖率为 {fragment_coverage_pct * 100:.1f}%",
            "positive": True,
        })
    else:
        supporting_evidence.append({
            "type": "fragment_coverage",
            "label": "残片覆盖率较低",
            "detail": f"现存残片高度覆盖率仅 {fragment_coverage_pct * 100:.1f}%，复原不确定性较高",
            "positive": False,
        })

    if len(original_sorted) >= 5:
        supporting_evidence.append({
            "type": "control_point_count",
            "label": "控制点充足",
            "detail": f"现存 {len(original_sorted)} 个剖面控制点，数据量充足",
            "positive": True,
        })

    if len(critical_gaps) == 0:
        supporting_evidence.append({
            "type": "gap_analysis",
            "label": "无严重缺失区段",
            "detail": "剖面缺失区段均在合理范围内",
            "positive": True,
        })
    else:
        supporting_evidence.append({
            "type": "gap_analysis",
            "label": f"存在 {len(critical_gaps)} 处严重缺失",
            "detail": "缺失区段占比较高，建议谨慎参考复原结果",
            "positive": False,
        })

    if template_control_points:
        supporting_evidence.append({
            "type": "template_reference",
            "label": "有标准器型模板参考",
            "detail": "复原过程参考了同类型标准器型模板",
            "positive": True,
        })

    risk_factors = []
    for g in critical_gaps:
        risk_factors.append({
            "type": "critical_gap",
            "zone": g["zone"],
            "severity": "高" if g["relativeSize"] > 0.3 else "中",
            "detail": f"{g['zone']}区段缺失 {g['relativeSize'] * 100:.1f}% 高度",
        })

    if fragment_coverage_pct < 0.4:
        risk_factors.append({
            "type": "low_coverage",
            "severity": "高",
            "detail": "整体残片覆盖率低于40%，复原结果高度推测性",
        })

    if restoration_method == "大胆":
        risk_factors.append({
            "type": "restoration_method",
            "severity": "中",
            "detail": "采用大胆复原方案，器型参数位于取值区间上限",
        })

    recommendations = []
    if overall_confidence >= 0.8:
        recommendations.append("复原结果可信度较高，可用于学术研究和展示参考。")
    elif overall_confidence >= 0.6:
        recommendations.append("复原结果可信度中等，建议结合其他考古证据综合判断。")
    elif overall_confidence >= 0.4:
        recommendations.append("复原结果可信度较低，仅可作为初步参考，标注为推测性复原。")
    else:
        recommendations.append("复原结果可信度很低，建议补充实物测量数据后重新进行复原。")

    if len(critical_gaps) > 0:
        zones_with_gaps = list(set(g["zone"] for g in critical_gaps))
        recommendations.append(f"建议在 {', '.join(zones_with_gaps)} 区域补充详细测量数据。")

    if not template_control_points:
        recommendations.append("建议查找同时期同类型标准器型作为参考模板。")

    return {
        "success": True,
        "overall_confidence": overall_confidence,
        "confidence_level": _confidence_level(overall_confidence),
        "part_confidences": {
            "bottom": part_confidences.get("bottom"),
            "mouth": part_confidences.get("mouth"),
            "belly": part_confidences.get("belly"),
            "neck": part_confidences.get("neck"),
            "shoulder": part_confidences.get("shoulder"),
            "foot": part_confidences.get("foot"),
        },
        "fragment_coverage": fragment_coverage_pct,
        "gap_count": len(gaps),
        "critical_gaps": critical_gaps,
        "all_gaps": gaps,
        "supporting_evidence": supporting_evidence,
        "risk_factors": risk_factors,
        "recommendations": recommendations,
        "assessment_method": "综合评估法",
        "dimensions": dims,
        "key_parts": key_parts,
    }


def _confidence_level(confidence: float) -> str:
    if confidence >= 0.85:
        return "极高"
    elif confidence >= 0.7:
        return "较高"
    elif confidence >= 0.55:
        return "中等"
    elif confidence >= 0.4:
        return "较低"
    else:
        return "极低"


def _get_zone_name(y_ratio: float) -> str:
    if y_ratio < 0.1:
        return "底部"
    elif y_ratio < 0.35:
        return "下腹/圈足"
    elif y_ratio < 0.65:
        return "腹部"
    elif y_ratio < 0.85:
        return "肩部/颈部"
    else:
        return "口沿"


def _get_zone_diameter_ratio(zone: str, dims_a: Dict, dims_b: Dict) -> Optional[float]:
    zone_map = {
        "bottom": "bottomDiameter",
        "mouth": "mouthDiameter",
        "belly": "bellyDiameter",
        "neck": "neckDiameter",
        "shoulder": "shoulderDiameter",
        "foot": "footDiameter",
    }
    key = zone_map.get(zone)
    if not key:
        return None
    va = dims_a.get(key)
    vb = dims_b.get(key)
    if va and vb and vb > 0:
        return va / vb
    return None


def generate_research_report(
    profile_data: Dict[str, Any],
    report_type: str = "器型分析报告",
    include_sections: Optional[List[str]] = None,
    author: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    custom_title: Optional[str] = None,
) -> Dict[str, Any]:
    default_sections = [
        "basic_info",
        "profile_description",
        "dimensions_analysis",
        "key_parts_analysis",
        "volume_estimation",
        "restoration_assessment",
        "template_comparison",
        "conclusions",
    ]

    if include_sections is None:
        include_sections = default_sections

    sections_to_include = [s for s in default_sections if s in include_sections]

    control_points = profile_data.get("control_points", [])
    cp_dicts = [{"id": p.get("id", i), "x": p.get("x"), "y": p.get("y")} for i, p in enumerate(control_points)]

    dims = calculate_dimensions(cp_dicts, profile_data.get("unit", "mm"))
    key_parts = identify_key_parts(cp_dicts, profile_data.get("unit", "mm"))

    profile_name = profile_data.get("name", "未命名器型")
    profile_code = profile_data.get("code", "N/A")

    title = custom_title or f"{profile_name} - {report_type}"

    sections = []
    content = {}

    if "basic_info" in sections_to_include:
        basic_info = {
            "title": "一、基本信息",
            "items": [
                {"label": "器物名称", "value": profile_name},
                {"label": "器物编号", "value": profile_code},
                {"label": "器型分类", "value": profile_data.get("vessel_type", "未分类")},
                {"label": "所属朝代", "value": profile_data.get("dynasty", "未知")},
                {"label": "出土地点", "value": profile_data.get("provenance", "未知")},
                {"label": "材质", "value": profile_data.get("material", "陶瓷")},
                {"label": "保存状态", "value": profile_data.get("condition_status", "完整")},
                {"label": "测量单位", "value": profile_data.get("unit", "mm")},
                {"label": "是否复原", "value": "是" if profile_data.get("is_restored") else "否"},
                {"label": "复原方法", "value": profile_data.get("restoration_method", "N/A")},
                {"label": "控制点数量", "value": len(control_points)},
            ],
        }
        sections.append(basic_info)
        content["basic_info"] = basic_info

    if "profile_description" in sections_to_include:
        profile_desc = {
            "title": "二、剖面描述",
            "paragraphs": _generate_profile_description(dims, key_parts, profile_data),
            "control_points": [
                {
                    "index": i + 1,
                    "id": p.get("id"),
                    "x": round(p.get("x", 0), 2),
                    "y": round(p.get("y", 0), 2),
                    "radius_mm": round(p.get("x", 0), 2),
                    "height_mm": round(p.get("y", 0), 2),
                    "zone": _get_zone_by_height(p.get("y", 0), dims),
                }
                for i, p in enumerate(sorted(cp_dicts, key=lambda x: x["y"]))
            ],
        }
        sections.append(profile_desc)
        content["profile_description"] = profile_desc

    if "dimensions_analysis" in sections_to_include:
        unit = profile_data.get("unit", "mm")
        dim_analysis = {
            "title": "三、尺寸分析",
            "primary_dimensions": [
                {"label": "通高", "value": round(dims["height"], 2), "unit": unit},
                {"label": "口径", "value": round(dims["mouthDiameter"], 2), "unit": unit},
                {"label": "腹径", "value": round(dims["bellyDiameter"], 2), "unit": unit},
                {"label": "底径", "value": round(dims["bottomDiameter"], 2), "unit": unit},
            ],
            "secondary_dimensions": [
                {"label": "颈径", "value": round(dims.get("neckDiameter") or 0, 2), "unit": unit, "available": dims.get("neckDiameter") is not None},
                {"label": "肩径", "value": round(dims.get("shoulderDiameter") or 0, 2), "unit": unit, "available": dims.get("shoulderDiameter") is not None},
                {"label": "足径", "value": round(dims.get("footDiameter") or 0, 2), "unit": unit, "available": dims.get("footDiameter") is not None},
            ],
            "ratios": _calculate_shape_ratios(dims),
        }
        sections.append(dim_analysis)
        content["dimensions_analysis"] = dim_analysis

    if "key_parts_analysis" in sections_to_include:
        kp_analysis = {
            "title": "四、关键部位分析",
            "parts": [
                {
                    "name": kp["name"],
                    "zone": kp.get("zone", ""),
                    "startHeight": round(kp["startY"], 2),
                    "endHeight": round(kp["endY"], 2),
                    "heightRange": round(kp["endY"] - kp["startY"], 2),
                    "diameter": round(kp.get("diameter") or 0, 2) if kp.get("diameter") else None,
                    "confidence": kp.get("confidence"),
                    "description": kp.get("description", ""),
                }
                for kp in key_parts
            ],
            "summary": f"共识别出 {len(key_parts)} 个关键解剖部位",
        }
        sections.append(kp_analysis)
        content["key_parts_analysis"] = kp_analysis

    if "volume_estimation" in sections_to_include:
        unit = profile_data.get("unit", "mm")
        vol = dims.get("volume")
        vol_analysis = {
            "title": "五、容量估算",
            "method": "旋转体体积积分法（基于剖面曲线的圆盘法积分）",
            "result": {
                "value_mL": round(vol, 2) if vol else None,
                "value_L": round(vol / 1000, 4) if vol else None,
                "unit": "mL",
            },
            "note": _generate_volume_note(dims, profile_data),
        }
        sections.append(vol_analysis)
        content["volume_estimation"] = vol_analysis

    restoration_data = profile_data.get("restoration_assessment")
    if "restoration_assessment" in sections_to_include:
        if not restoration_data:
            if profile_data.get("is_restored") or profile_data.get("condition_status") != "完整":
                restoration_data = assess_restoration(
                    cp_dicts,
                    unit=profile_data.get("unit", "mm"),
                    restoration_method=profile_data.get("restoration_method"),
                )

        if restoration_data and restoration_data.get("success"):
            ra_section = {
                "title": "六、复原可信度评估",
                "overall": {
                    "confidence": round(restoration_data["overall_confidence"], 4),
                    "level": restoration_data["confidence_level"],
                },
                "part_confidences": [
                    {"label": _zone_cn_label(k), "value": round(v, 4) if v else None}
                    for k, v in restoration_data["part_confidences"].items()
                ],
                "fragment_coverage": round(restoration_data["fragment_coverage"], 4),
                "gap_count": restoration_data["gap_count"],
                "supporting_evidence": restoration_data.get("supporting_evidence", []),
                "risk_factors": restoration_data.get("risk_factors", []),
                "recommendations": restoration_data.get("recommendations", []),
            }
            sections.append(ra_section)
            content["restoration_assessment"] = ra_section

    if "template_comparison" in sections_to_include:
        template = profile_data.get("template")
        tc_section = {
            "title": "七、与标准器型对比",
            "has_template": template is not None,
        }
        if template:
            template_points = template.get("control_points", [])
            t_dicts = [{"id": i, "x": p.get("x"), "y": p.get("y")} for i, p in enumerate(template_points)]
            t_dims = calculate_dimensions(t_dicts, profile_data.get("unit", "mm"))
            tc_section["template_info"] = {
                "name": template.get("name"),
                "code": template.get("code"),
                "category": template.get("category"),
                "dynasty": template.get("dynasty"),
            }
            tc_section["dimension_comparison"] = [
                {
                    "label": "通高",
                    "profile": round(dims["height"], 2),
                    "template": round(t_dims["height"], 2),
                    "diff_pct": round((dims["height"] - t_dims["height"]) / t_dims["height"] * 100, 2) if t_dims["height"] > 0 else None,
                },
                {
                    "label": "口径",
                    "profile": round(dims["mouthDiameter"], 2),
                    "template": round(t_dims["mouthDiameter"], 2),
                    "diff_pct": round((dims["mouthDiameter"] - t_dims["mouthDiameter"]) / t_dims["mouthDiameter"] * 100, 2) if t_dims["mouthDiameter"] > 0 else None,
                },
                {
                    "label": "腹径",
                    "profile": round(dims["bellyDiameter"], 2),
                    "template": round(t_dims["bellyDiameter"], 2),
                    "diff_pct": round((dims["bellyDiameter"] - t_dims["bellyDiameter"]) / t_dims["bellyDiameter"] * 100, 2) if t_dims["bellyDiameter"] > 0 else None,
                },
                {
                    "label": "底径",
                    "profile": round(dims["bottomDiameter"], 2),
                    "template": round(t_dims["bottomDiameter"], 2),
                    "diff_pct": round((dims["bottomDiameter"] - t_dims["bottomDiameter"]) / t_dims["bottomDiameter"] * 100, 2) if t_dims["bottomDiameter"] > 0 else None,
                },
            ]
        sections.append(tc_section)
        content["template_comparison"] = tc_section

    if "conclusions" in sections_to_include:
        conclusions = _generate_conclusions(dims, key_parts, restoration_data, profile_data)
        concl_section = {
            "title": "八、研究结论",
            "conclusions": conclusions,
        }
        sections.append(concl_section)
        content["conclusions"] = concl_section

    summary = _generate_summary(dims, key_parts, profile_data, restoration_data)

    default_keywords = [
        profile_data.get("vessel_type", "陶瓷器"),
        profile_data.get("dynasty", "未知朝代"),
        "器型分析",
        "剖面测量",
    ]
    if keywords:
        default_keywords.extend([k for k in keywords if k not in default_keywords])

    report_content = {
        "title": title,
        "report_type": report_type,
        "profile_name": profile_name,
        "profile_code": profile_code,
        "author": author or "系统自动生成",
        "created_at": datetime.utcnow().isoformat(),
        "keywords": default_keywords[:10],
        "summary": summary,
        "sections": sections,
        "content": content,
        "raw_dimensions": dims,
        "raw_key_parts": key_parts,
        "conclusions": conclusions,
    }

    return report_content


def _generate_profile_description(dims, key_parts, profile_data) -> List[str]:
    paragraphs = []
    unit = profile_data.get("unit", "mm")

    p1 = f"本器剖面共测得 {len(profile_data.get('control_points', []))} 个控制点，"
    p1 += f"通高约 {dims['height']:.1f}{unit}，"
    p1 += f"口径 {dims['mouthDiameter']:.1f}{unit}，"
    p1 += f"腹径 {dims['bellyDiameter']:.1f}{unit}，"
    p1 += f"底径 {dims['bottomDiameter']:.1f}{unit}。"
    paragraphs.append(p1)

    if dims.get("neckDiameter"):
        p2 = f"颈部内收明显，颈径约 {dims['neckDiameter']:.1f}{unit}，"
    else:
        p2 = "器型无明显颈部，"

    if dims.get("shoulderDiameter"):
        p2 += f"肩部圆润，肩径约 {dims['shoulderDiameter']:.1f}{unit}，"

    if dims.get("footDiameter"):
        p2 += f"下承圈足，足径 {dims['footDiameter']:.1f}{unit}。"
    else:
        p2 += "底部平实无足。"
    paragraphs.append(p2)

    kp_names = "、".join([kp["name"] for kp in key_parts])
    p3 = f"自动识别关键部位包括：{kp_names}。"
    paragraphs.append(p3)

    if profile_data.get("is_restored"):
        p4 = f"本器为残损复原器，复原方法：{profile_data.get('restoration_method', '适中')}方案。"
        paragraphs.append(p4)

    return paragraphs


def _calculate_shape_ratios(dims) -> List[Dict]:
    ratios = []
    h = dims["height"]
    if h > 0:
        ratios.append({"label": "口径/高度", "value": round(dims["mouthDiameter"] / h, 3)})
        ratios.append({"label": "腹径/高度", "value": round(dims["bellyDiameter"] / h, 3)})
        ratios.append({"label": "底径/高度", "value": round(dims["bottomDiameter"] / h, 3)})
    if dims["bellyDiameter"] > 0:
        ratios.append({"label": "口径/腹径", "value": round(dims["mouthDiameter"] / dims["bellyDiameter"], 3)})
        ratios.append({"label": "底径/腹径", "value": round(dims["bottomDiameter"] / dims["bellyDiameter"], 3)})
    return ratios


def _generate_volume_note(dims, profile_data) -> str:
    if not dims.get("volume"):
        return "容量估算不可用：底部未闭合或数据不足。"
    vol = dims["volume"]
    note = f"基于剖面曲线旋转积分计算，"
    if vol < 500:
        note += f"估算容量约 {vol:.1f} 毫升，属于小型器。"
    elif vol < 2000:
        note += f"估算容量约 {vol:.1f} 毫升（{vol/1000:.2f} 升），属于中型器。"
    else:
        note += f"估算容量约 {vol:.1f} 毫升（{vol/1000:.2f} 升），属于大型器。"

    if profile_data.get("is_restored"):
        note += " [注意：本器为复原器，容量值具有推测性]"
    return note


def _zone_cn_label(zone_key: str) -> str:
    return {
        "bottom": "底部",
        "mouth": "口沿",
        "belly": "腹部",
        "neck": "颈部",
        "shoulder": "肩部",
        "foot": "圈足",
    }.get(zone_key, zone_key)


def _get_zone_by_height(y: float, dims) -> str:
    h = dims["height"]
    if h <= 0:
        return "未知"
    ratio = y / (h * 10) if dims.get("_unit_factor_cm") else y / h
    return _get_zone_name(ratio)


def _generate_summary(dims, key_parts, profile_data, restoration_data) -> str:
    name = profile_data.get("name", "本器")
    unit = profile_data.get("unit", "mm")
    summary = f"{name}为{profile_data.get('vessel_type', '陶瓷器')}，"
    summary += f"通高{dims['height']:.1f}{unit}，腹径{dims['bellyDiameter']:.1f}{unit}，"
    summary += f"高腹比{dims['height']/dims['bellyDiameter']:.2f}。"

    if restoration_data and restoration_data.get("success"):
        conf = restoration_data["overall_confidence"]
        summary += f"复原综合可信度{conf*100:.1f}%（{restoration_data['confidence_level']}）。"

    if dims.get("volume"):
        summary += f"估算容量约{dims['volume']:.0f}毫升。"

    return summary


def _generate_conclusions(dims, key_parts, restoration_data, profile_data) -> List[str]:
    conclusions = []
    unit = profile_data.get("unit", "mm")

    hb_ratio = dims["height"] / dims["bellyDiameter"] if dims["bellyDiameter"] > 0 else 0
    if hb_ratio > 1.5:
        shape_type = "瘦高型"
    elif hb_ratio < 0.8:
        shape_type = "矮胖型"
    else:
        shape_type = "均衡型"
    conclusions.append(f"器型整体为{shape_type}，高腹比 {hb_ratio:.2f}。")

    mb_ratio = dims["mouthDiameter"] / dims["bellyDiameter"] if dims["bellyDiameter"] > 0 else 0
    if mb_ratio > 0.9:
        conclusions.append("口腹尺寸接近，为广口/直壁类器型。")
    elif mb_ratio < 0.5:
        conclusions.append("口径明显小于腹径，为小口鼓腹类器型，敛口特征显著。")
    else:
        conclusions.append("口腹尺寸比例适中，器型内敛而不失舒展。")

    if dims.get("neckDiameter"):
        conclusions.append(f"存在明显颈部，颈径 {dims['neckDiameter']:.1f}{unit}，属有颈类器。")

    if restoration_data and restoration_data.get("success"):
        conf = restoration_data["overall_confidence"]
        if conf >= 0.7:
            conclusions.append(f"复原可信度{restoration_data['confidence_level']}（{conf*100:.0f}%），复原结果较为可靠。")
        elif conf >= 0.5:
            conclusions.append(f"复原可信度{restoration_data['confidence_level']}（{conf*100:.0f}%），使用时需注意其推测性质。")
        else:
            conclusions.append(f"复原可信度{restoration_data['confidence_level']}（{conf*100:.0f}%），建议仅作参考，结合更多证据。")

        for rec in restoration_data.get("recommendations", [])[:2]:
            conclusions.append(rec)

    return conclusions
