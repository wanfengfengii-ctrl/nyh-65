from typing import List, Dict, Any, Tuple, Optional
from math import atan2, degrees
import math


def catmull_rom_to_bezier(p0, p1, p2, p3):
    cp1x = p1["x"] + (p2["x"] - p0["x"]) / 6
    cp1y = p1["y"] + (p2["y"] - p0["y"]) / 6
    cp2x = p2["x"] - (p3["x"] - p1["x"]) / 6
    cp2y = p2["y"] - (p3["y"] - p1["y"]) / 6
    return {"cp1x": cp1x, "cp1y": cp1y, "cp2x": cp2x, "cp2y": cp2y}


def sample_curve_points(
    points: List[Dict[str, float]],
    samples_per_segment: int = 20
) -> List[Dict[str, float]]:
    if len(points) < 2:
        return []
    result: List[Dict[str, float]] = []
    extended = [points[0]] + list(points) + [points[-1]]

    for i in range(len(extended) - 3):
        p0 = extended[i]
        p1 = extended[i + 1]
        p2 = extended[i + 2]
        p3 = extended[i + 3]
        b = catmull_rom_to_bezier(p0, p1, p2, p3)

        for s in range(samples_per_segment + 1):
            t = s / samples_per_segment
            mt = 1 - t
            mt2 = mt * mt
            mt3 = mt2 * mt
            t2 = t * t
            t3 = t2 * t

            x = mt3 * p1["x"] + 3 * mt2 * t * b["cp1x"] + 3 * mt * t2 * b["cp2x"] + t3 * p2["x"]
            y = mt3 * p1["y"] + 3 * mt2 * t * b["cp1y"] + 3 * mt * t2 * b["cp2y"] + t3 * p2["y"]
            result.append({"x": x, "y": y})

    return result


def calculate_dimensions(points: List[Dict[str, float]], unit: str = "mm") -> Dict[str, Any]:
    if len(points) < 2:
        return {
            "height": 0,
            "mouthDiameter": 0,
            "bellyDiameter": 0,
            "bottomDiameter": 0,
            "volume": None,
            "isValid": False,
            "errors": ["控制点数量不足"],
        }

    unit_factor = 10 if unit == "cm" else 1
    sampled = sample_curve_points(points, 50)
    if not sampled:
        return {
            "height": 0,
            "mouthDiameter": 0,
            "bellyDiameter": 0,
            "bottomDiameter": 0,
            "volume": None,
            "isValid": False,
            "errors": ["无法生成采样曲线"],
        }

    ys = [p["y"] for p in sampled]
    xs = [p["x"] for p in sampled]
    min_y = min(ys)
    max_y = max(ys)
    height = (max_y - min_y) / unit_factor
    max_x = max(xs)
    belly_diameter = (2 * max_x) / unit_factor

    top_point = max(sampled, key=lambda p: p["y"])
    bottom_point = min(sampled, key=lambda p: p["y"])

    mouth_diameter = (2 * top_point["x"]) / unit_factor
    bottom_diameter = (2 * bottom_point["x"]) / unit_factor

    volume = None
    if bottom_point["x"] > 0:
        sorted_sampled = sorted(sampled, key=lambda p: p["y"])
        integral = 0.0
        for i in range(1, len(sorted_sampled)):
            dy = sorted_sampled[i]["y"] - sorted_sampled[i - 1]["y"]
            r1 = sorted_sampled[i - 1]["x"]
            r2 = sorted_sampled[i]["x"]
            avg_r2 = (r1 * r1 + r2 * r2) / 2
            integral += math.pi * avg_r2 * dy
        volume_mm3 = integral
        volume = volume_mm3 / 1000

    neck_diameter = None
    shoulder_diameter = None
    foot_diameter = None

    if len(sampled) >= 10:
        x_vals = xs
        y_vals = ys

        local_mins = []
        for i in range(2, len(x_vals) - 2):
            if x_vals[i] < x_vals[i - 1] and x_vals[i] <= x_vals[i + 1]:
                local_mins.append({"x": x_vals[i], "y": y_vals[i], "idx": i})

        if len(local_mins) >= 1:
            height_range = max_y - min_y
            upper_mins = [m for m in local_mins if m["y"] > min_y + height_range * 0.55]
            if upper_mins:
                neck = min(upper_mins, key=lambda m: abs(m["y"] - (min_y + height_range * 0.75)))
                neck_diameter = (2 * neck["x"]) / unit_factor

            lower_mins = [m for m in local_mins if m["y"] < min_y + height_range * 0.35]
            if lower_mins:
                foot = min(lower_mins, key=lambda m: abs(m["y"] - (min_y + height_range * 0.15)))
                foot_diameter = (2 * foot["x"]) / unit_factor

        local_maxes = []
        for i in range(2, len(x_vals) - 2):
            if x_vals[i] >= x_vals[i - 1] and x_vals[i] > x_vals[i + 1]:
                local_maxes.append({"x": x_vals[i], "y": y_vals[i], "idx": i})

        if len(local_maxes) >= 1:
            height_range = max_y - min_y
            mid_maxes = [m for m in local_maxes if min_y + height_range * 0.35 < m["y"] < min_y + height_range * 0.75]
            if mid_maxes:
                shoulder = max(mid_maxes, key=lambda m: m["x"])
                shoulder_diameter = (2 * shoulder["x"]) / unit_factor

    return {
        "height": height,
        "mouthDiameter": mouth_diameter,
        "bellyDiameter": belly_diameter,
        "bottomDiameter": bottom_diameter,
        "neckDiameter": neck_diameter,
        "shoulderDiameter": shoulder_diameter,
        "footDiameter": foot_diameter,
        "volume": volume,
        "isValid": True,
        "errors": [],
    }


def identify_key_parts(
    control_points: List[Dict[str, float]],
    unit: str = "mm",
    vessel_type_hint: Optional[str] = None
) -> List[Dict[str, Any]]:
    if len(control_points) < 3:
        return []

    sorted_points = sorted(control_points, key=lambda p: p["y"])
    sampled = sample_curve_points(control_points, 30)
    if not sampled:
        return []

    dims = calculate_dimensions(control_points, unit)

    ys = [p["y"] for p in sampled]
    xs = [p["x"] for p in sampled]
    min_y = min(ys)
    max_y = max(ys)
    height_range = max_y - min_y

    if height_range <= 0:
        return []

    key_parts: List[Dict[str, Any]] = []

    key_parts.append({
        "name": "底部",
        "startPointIndex": 0,
        "endPointIndex": min(2, len(sorted_points) - 1),
        "startY": min_y,
        "endY": min_y + height_range * 0.1,
        "description": "器物底座区域，支撑整个器身",
        "confidence": 0.9,
        "diameter": dims["bottomDiameter"],
        "zone": "bottom"
    })

    if dims.get("footDiameter"):
        foot_y_ratio = None
        for p in sampled:
            if abs(2 * p["x"] - (dims["footDiameter"] * (10 if unit == "cm" else 1))) < 1:
                foot_y_ratio = (p["y"] - min_y) / height_range
                break
        if foot_y_ratio:
            start_y = min_y + max(0, (foot_y_ratio - 0.08)) * height_range
            end_y = min_y + min(0.35, (foot_y_ratio + 0.05)) * height_range
            start_idx = max(0, int(len(sorted_points) * max(0, foot_y_ratio - 0.1)))
            end_idx = min(len(sorted_points) - 1, int(len(sorted_points) * min(0.4, foot_y_ratio + 0.05)))
            key_parts.append({
                "name": "圈足",
                "startPointIndex": start_idx,
                "endPointIndex": end_idx,
                "startY": start_y,
                "endY": end_y,
                "description": "器物足部，常见于高规格瓷器",
                "confidence": 0.75,
                "diameter": dims["footDiameter"],
                "zone": "foot"
            })

    belly_idx = xs.index(max(xs))
    belly_y = ys[belly_idx]
    belly_y_ratio = (belly_y - min_y) / height_range

    start_idx = max(1, int(len(sorted_points) * max(0.15, belly_y_ratio - 0.2)))
    end_idx = min(len(sorted_points) - 1, int(len(sorted_points) * min(0.75, belly_y_ratio + 0.15)))
    key_parts.append({
        "name": "腹部",
        "startPointIndex": start_idx,
        "endPointIndex": end_idx,
        "startY": min_y + height_range * max(0.15, belly_y_ratio - 0.2),
        "endY": min_y + height_range * min(0.8, belly_y_ratio + 0.15),
        "description": "器身最宽处，决定容量的主要区域",
        "confidence": 0.95,
        "diameter": dims["bellyDiameter"],
        "zone": "belly"
    })

    if dims.get("shoulderDiameter"):
        shoulder_y_ratio = None
        for p in sampled:
            if abs(2 * p["x"] - (dims["shoulderDiameter"] * (10 if unit == "cm" else 1))) < 1.5:
                shoulder_y_ratio = (p["y"] - min_y) / height_range
                break
        if shoulder_y_ratio is None:
            shoulder_y_ratio = belly_y_ratio + 0.15
        if 0.3 < shoulder_y_ratio < 0.9:
            start_s = min(shoulder_y_ratio, belly_y_ratio + 0.05)
            end_s = min(0.95, shoulder_y_ratio + 0.12)
            key_parts.append({
                "name": "肩部",
                "startPointIndex": max(0, int(len(sorted_points) * start_s)),
                "endPointIndex": min(len(sorted_points) - 1, int(len(sorted_points) * end_s)),
                "startY": min_y + height_range * start_s,
                "endY": min_y + height_range * end_s,
                "description": "腹部与颈部过渡区域",
                "confidence": 0.8,
                "diameter": dims["shoulderDiameter"],
                "zone": "shoulder"
            })

    if dims.get("neckDiameter"):
        neck_y_ratio = None
        target_val = dims["neckDiameter"] * (10 if unit == "cm" else 1)
        closest = None
        closest_dist = float("inf")
        for p in sampled:
            d = abs(2 * p["x"] - target_val)
            if d < closest_dist:
                closest_dist = d
                closest = p
        if closest:
            neck_y_ratio = (closest["y"] - min_y) / height_range
        if neck_y_ratio and 0.5 < neck_y_ratio < 1.0:
            start_n = max(0.55, neck_y_ratio - 0.1)
            end_n = min(1.0, neck_y_ratio + 0.1)
            key_parts.append({
                "name": "颈部",
                "startPointIndex": max(0, int(len(sorted_points) * start_n)),
                "endPointIndex": min(len(sorted_points) - 1, int(len(sorted_points) * end_n)),
                "startY": min_y + height_range * start_n,
                "endY": min_y + height_range * end_n,
                "description": "口沿与肩部之间的收缩部分",
                "confidence": 0.78,
                "diameter": dims["neckDiameter"],
                "zone": "neck"
            })

    key_parts.append({
        "name": "口沿",
        "startPointIndex": max(0, len(sorted_points) - 3),
        "endPointIndex": len(sorted_points) - 1,
        "startY": max_y - height_range * 0.08,
        "endY": max_y,
        "description": "器物最顶端开口边缘",
        "confidence": 0.92,
        "diameter": dims["mouthDiameter"],
        "zone": "mouth"
    })

    return key_parts


def parametric_edit(
    control_points: List[Dict[str, float]],
    dimension_type: str,
    target_value: float,
    unit: str = "mm",
    preserve_proportions: bool = True
) -> Dict[str, Any]:
    if len(control_points) < 2:
        return {
            "success": False,
            "control_points": control_points,
            "error": "控制点数量不足",
        }

    dims = calculate_dimensions(control_points, unit)
    if not dims["isValid"]:
        return {
            "success": False,
            "control_points": control_points,
            "error": "当前器型无效",
        }

    unit_factor = 10 if unit == "cm" else 1
    sorted_points = sorted(control_points, key=lambda p: p["y"])
    ys = [p["y"] for p in sorted_points]
    xs = [p["x"] for p in sorted_points]
    min_y = min(ys)
    max_y = max(ys)
    height_range = max_y - min_y

    new_points = [{"id": p["id"], "x": p["x"], "y": p["y"]} for p in control_points]

    if dimension_type == "height" and dims["height"] > 0:
        scale_y = (target_value * unit_factor) / (height_range if height_range > 0 else 1)
        for p in new_points:
            if preserve_proportions:
                scale_x = scale_y
                p["x"] = p["x"] * scale_x
            p["y"] = min_y + (p["y"] - min_y) * scale_y

    elif dimension_type == "mouthDiameter" and dims["mouthDiameter"] > 0:
        current_radius = (dims["mouthDiameter"] * unit_factor) / 2
        target_radius = (target_value * unit_factor) / 2
        scale_mouth = target_radius / current_radius if current_radius > 0 else 1
        mouth_zone_start = min_y + height_range * 0.75
        for p in new_points:
            if p["y"] >= mouth_zone_start:
                ratio = (p["y"] - mouth_zone_start) / max(1, (max_y - mouth_zone_start))
                ratio = max(0, min(1, ratio))
                eff_scale = 1 + (scale_mouth - 1) * ratio
                p["x"] = p["x"] * eff_scale

    elif dimension_type == "bellyDiameter" and dims["bellyDiameter"] > 0:
        current_radius = (dims["bellyDiameter"] * unit_factor) / 2
        target_radius = (target_value * unit_factor) / 2
        scale_belly = target_radius / current_radius if current_radius > 0 else 1
        belly_y = min_y + height_range * 0.5
        spread = height_range * 0.4
        for p in new_points:
            dist = abs(p["y"] - belly_y) / spread if spread > 0 else 0
            ratio = max(0, 1 - dist)
            eff_scale = 1 + (scale_belly - 1) * ratio
            p["x"] = p["x"] * eff_scale

    elif dimension_type == "bottomDiameter" and dims["bottomDiameter"] > 0:
        current_radius = (dims["bottomDiameter"] * unit_factor) / 2
        target_radius = (target_value * unit_factor) / 2
        scale_bottom = target_radius / current_radius if current_radius > 0 else 1
        bottom_zone_end = min_y + height_range * 0.25
        for p in new_points:
            if p["y"] <= bottom_zone_end:
                ratio = 1 - (p["y"] - min_y) / max(1, (bottom_zone_end - min_y))
                ratio = max(0, min(1, ratio))
                eff_scale = 1 + (scale_bottom - 1) * ratio
                p["x"] = p["x"] * eff_scale

    elif dimension_type == "volume" and dims["volume"] and dims["volume"] > 0:
        volume_scale = (target_value / dims["volume"]) ** (1/3)
        for p in new_points:
            p["x"] = p["x"] * volume_scale
            if preserve_proportions:
                p["y"] = min_y + (p["y"] - min_y) * volume_scale

    else:
        return {
            "success": False,
            "control_points": control_points,
            "error": f"不支持的尺寸类型: {dimension_type}",
        }

    for p in new_points:
        p["x"] = max(0, p["x"])
        p["y"] = max(0, p["y"])

    new_dims = calculate_dimensions(new_points, unit)

    return {
        "success": True,
        "control_points": new_points,
        "old_dimensions": dims,
        "new_dimensions": new_dims,
        "dimension_type": dimension_type,
        "target_value": target_value,
    }


def analyze_differences(
    profile_a: List[Dict[str, float]],
    profile_b: List[Dict[str, float]],
    profile_a_name: str = "A",
    profile_b_name: str = "B",
    unit: str = "mm",
    sample_count: int = 100
) -> Dict[str, Any]:
    if len(profile_a) < 2 or len(profile_b) < 2:
        return {
            "success": False,
            "error": "控制点数量不足",
        }

    sampled_a = sample_curve_points(profile_a, max(10, sample_count // max(1, len(profile_a) - 1)))
    sampled_b = sample_curve_points(profile_b, max(10, sample_count // max(1, len(profile_b) - 1)))

    if not sampled_a or not sampled_b:
        return {"success": False, "error": "无法采样曲线"}

    ya = [p["y"] for p in sampled_a]
    yb = [p["y"] for p in sampled_b]
    min_y = min(min(ya), min(yb))
    max_y = max(max(ya), max(yb))

    if max_y <= min_y:
        return {"success": False, "error": "高度范围无效"}

    n_samples = sample_count
    target_ys = [min_y + i * (max_y - min_y) / (n_samples - 1) for i in range(n_samples)]

    def interp_x(sampled, target_y):
        for i in range(len(sampled) - 1):
            y1, y2 = sampled[i]["y"], sampled[i + 1]["y"]
            x1, x2 = sampled[i]["x"], sampled[i + 1]["x"]
            if y1 <= target_y <= y2 or y2 <= target_y <= y1:
                if y2 == y1:
                    return (x1 + x2) / 2
                t = (target_y - y1) / (y2 - y1)
                return x1 + t * (x2 - x1)
        if target_y < min(ya if sampled == sampled_a else yb):
            return sampled[0]["x"]
        return sampled[-1]["x"]

    heatmap_data = []
    all_diffs = []

    for y in target_ys:
        xa = interp_x(sampled_a, y)
        xb = interp_x(sampled_b, y)
        diff = xa - xb
        diameter_diff = 2 * diff
        all_diffs.append(abs(diameter_diff))

        y_ratio = (y - min_y) / (max_y - min_y) if max_y > min_y else 0
        if y_ratio < 0.1:
            zone = "底部"
        elif y_ratio < 0.35:
            zone = "下腹/圈足"
        elif y_ratio < 0.65:
            zone = "腹部"
        elif y_ratio < 0.85:
            zone = "肩部/颈部"
        else:
            zone = "口沿"

        heatmap_data.append({
            "y": y,
            "yRatio": y_ratio,
            "xA": xa,
            "xB": xb,
            "radiusDifference": diff,
            "difference": diameter_diff,
            "normalized": 0,
            "zone": zone,
        })

    max_diff = max(all_diffs) if all_diffs else 1
    if max_diff > 0:
        for hd in heatmap_data:
            hd["normalized"] = abs(hd["difference"]) / max_diff

    unit_factor = 10 if unit == "cm" else 1
    dims_a = calculate_dimensions(profile_a, unit)
    dims_b = calculate_dimensions(profile_b, unit)

    dimension_differences = {}
    for key in ["height", "mouthDiameter", "bellyDiameter", "bottomDiameter", "volume",
                "neckDiameter", "shoulderDiameter", "footDiameter"]:
        va = dims_a.get(key)
        vb = dims_b.get(key)
        if va is not None and vb is not None and va > 0:
            dimension_differences[key] = {
                profile_a_name: va,
                profile_b_name: vb,
                "absoluteDiff": va - vb,
                "relativeDiff": (va - vb) / va * 100,
            }

    zones = {}
    for hd in heatmap_data:
        z = hd["zone"]
        if z not in zones:
            zones[z] = {"diffs": [], "y_start": hd["y"], "y_end": hd["y"]}
        zones[z]["diffs"].append(abs(hd["difference"]))
        zones[z]["y_start"] = min(zones[z]["y_start"], hd["y"])
        zones[z]["y_end"] = max(zones[z]["y_end"], hd["y"])

    key_differences = []
    for zone_name, zone_data in zones.items():
        if zone_data["diffs"]:
            avg_d = sum(zone_data["diffs"]) / len(zone_data["diffs"])
            max_d = max(zone_data["diffs"])
            rel_avg = (avg_d / (max_diff * unit_factor)) if max_diff > 0 else 0

            if rel_avg < 0.15:
                sig = "细微"
            elif rel_avg < 0.4:
                sig = "中等"
            else:
                sig = "显著"

            key_differences.append({
                "zone": zone_name,
                "y_start": zone_data["y_start"],
                "y_end": zone_data["y_end"],
                "avg_diff": avg_d / unit_factor,
                "max_diff": max_d / unit_factor,
                "significance": sig,
                "relative_intensity": rel_avg,
            })

    key_differences.sort(key=lambda x: x["avg_diff"], reverse=True)

    if all_diffs:
        avg_abs_diff = sum(all_diffs) / len(all_diffs)
        max_xa = max(p["x"] for p in sampled_a)
        max_xb = max(p["x"] for p in sampled_b)
        ref = max(max_xa, max_xb) * 2
        similarity = 1 - min(1, avg_abs_diff / (ref * 0.5)) if ref > 0 else 0
    else:
        similarity = 0

    return {
        "success": True,
        "heatmap_data": heatmap_data,
        "key_differences": key_differences,
        "overall_similarity": max(0, min(1, similarity)),
        "dimension_differences": dimension_differences,
        "y_range": {"min": min_y, "max": max_y},
        "profile_a_dimensions": dims_a,
        "profile_b_dimensions": dims_b,
    }


def apply_template(
    template_points: List[Dict[str, float]],
    scale_factor: Optional[float] = None,
    target_height: Optional[float] = None,
    target_belly_diameter: Optional[float] = None,
) -> Dict[str, Any]:
    if not template_points or len(template_points) < 2:
        return {"success": False, "error": "模板数据无效"}

    dims = calculate_dimensions(template_points, "mm")
    if not dims["isValid"]:
        return {"success": False, "error": "模板器型无效"}

    sorted_points = sorted(template_points, key=lambda p: p["y"])
    min_y = sorted_points[0]["y"]

    if scale_factor is None:
        if target_height and dims["height"] > 0:
            scale_factor = target_height / dims["height"]
        elif target_belly_diameter and dims["bellyDiameter"] > 0:
            scale_factor = target_belly_diameter / dims["bellyDiameter"]
        else:
            scale_factor = 1.0

    new_points = []
    for p in template_points:
        new_points.append({
            "id": p.get("id", 0),
            "x": p["x"] * scale_factor,
            "y": min_y + (p["y"] - min_y) * scale_factor,
        })

    new_dims = calculate_dimensions(new_points, "mm")

    return {
        "success": True,
        "control_points": new_points,
        "scale_factor": scale_factor,
        "original_dimensions": dims,
        "new_dimensions": new_dims,
    }
