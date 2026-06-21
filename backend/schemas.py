from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class CulvertBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    location: Optional[str] = None
    length: float
    material: Optional[str] = None
    construction_year: Optional[int] = None
    status: Optional[str] = "正常"
    description: Optional[str] = None


class CulvertCreate(CulvertBase):
    pass


class CulvertUpdate(CulvertBase):
    pass


class Culvert(CulvertBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SectionBase(BaseModel):
    culvert_id: int
    station: float
    shape: str = Field(..., max_length=30)
    width: float
    height: Optional[float] = None
    diameter: Optional[float] = None
    area: Optional[float] = None
    perimeter: Optional[float] = None
    hydraulic_radius: Optional[float] = None
    description: Optional[str] = None


class SectionCreate(SectionBase):
    pass


class SectionUpdate(SectionBase):
    pass


class Section(SectionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SlopeBase(BaseModel):
    section_id: int
    start_station: float
    end_station: float
    slope_value: float
    start_elevation: Optional[float] = None
    end_elevation: Optional[float] = None
    description: Optional[str] = None


class SlopeCreate(SlopeBase):
    pass


class SlopeUpdate(SlopeBase):
    pass


class Slope(SlopeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ManholeBase(BaseModel):
    culvert_id: int
    name: str = Field(..., max_length=50)
    code: str = Field(..., max_length=50)
    station: float
    elevation: Optional[float] = None
    depth: Optional[float] = None
    diameter: Optional[float] = None
    material: Optional[str] = None
    condition: Optional[str] = "良好"
    has_inlet: Optional[bool] = False
    has_outlet: Optional[bool] = False
    description: Optional[str] = None


class ManholeCreate(ManholeBase):
    pass


class ManholeUpdate(ManholeBase):
    pass


class Manhole(ManholeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SedimentRecordBase(BaseModel):
    culvert_id: int
    record_date: datetime
    start_station: float
    end_station: float
    sediment_thickness: float
    sediment_volume: Optional[float] = None
    sediment_type: Optional[str] = None
    survey_method: Optional[str] = None
    operator: Optional[str] = None
    description: Optional[str] = None


class SedimentRecordCreate(SedimentRecordBase):
    pass


class SedimentRecordUpdate(SedimentRecordBase):
    pass


class SedimentRecord(SedimentRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RainScenarioBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    return_period: int
    rainfall_duration: float
    total_rainfall: float
    rainfall_distribution: Optional[str] = None
    is_default: Optional[bool] = False


class RainScenarioCreate(RainScenarioBase):
    pass


class RainScenarioUpdate(RainScenarioBase):
    pass


class RainScenario(RainScenarioBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DrainageCapacityRequest(BaseModel):
    culvert_id: int
    scenario_ids: List[int]


class DrainageCapacityResult(BaseModel):
    scenario_id: int
    scenario_name: str
    return_period: int
    total_rainfall: float
    design_flow: float
    actual_capacity: float
    overflow: float
    overflow_ratio: float
    is_sufficient: bool


class SedimentTrendRequest(BaseModel):
    culvert_id: int
    months: Optional[int] = 12


class SedimentTrendPoint(BaseModel):
    date: str
    avg_thickness: float
    accumulated_volume: float


class SedimentTrendResult(BaseModel):
    culvert_id: int
    culvert_name: str
    trend_points: List[SedimentTrendPoint]
    avg_sediment_rate: float
    max_thickness: float
    predicted_thickness_6m: float
    predicted_thickness_12m: float
    risk_level: str


class RiskSection(BaseModel):
    start_station: float
    end_station: float
    risk_level: str
    risk_score: float
    description: str
    suggestion: str


class RiskWarningResult(BaseModel):
    culvert_id: int
    culvert_name: str
    total_risk_sections: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    risk_sections: List[RiskSection]


class SimulationRequest(BaseModel):
    culvert_id: int
    plan_type: str
    parameters: dict


class SimulationResult(BaseModel):
    plan_type: str
    original_capacity: float
    simulated_capacity: float
    capacity_improvement: float
    cost_estimate: float
    construction_period: str
    suggestion: str


class ProfilePoint(BaseModel):
    station: float
    elevation: float
    section_width: float
    section_height: Optional[float] = None
    sediment_thickness: Optional[float] = None
    manhole_name: Optional[str] = None


class ProfileResult(BaseModel):
    culvert_id: int
    culvert_name: str
    profile_points: List[ProfilePoint]
    max_elevation: float
    min_elevation: float
    avg_slope: float


class ReportRequest(BaseModel):
    culvert_id: int
    report_type: str
    include_charts: Optional[bool] = True


class ReportResult(BaseModel):
    report_id: str
    filename: str
    file_url: str
    created_at: datetime


class ControlPointSchema(BaseModel):
    id: int
    x: float
    y: float


class RepairMarkSchema(BaseModel):
    pointId: int
    description: Optional[str] = None


class KeyPartSchema(BaseModel):
    name: str
    startPointIndex: int
    endPointIndex: int
    startY: float
    endY: float
    description: Optional[str] = None
    confidence: Optional[float] = None


class DimensionsSchema(BaseModel):
    height: Optional[float] = None
    mouthDiameter: Optional[float] = None
    bellyDiameter: Optional[float] = None
    bottomDiameter: Optional[float] = None
    volume: Optional[float] = None
    neckDiameter: Optional[float] = None
    shoulderDiameter: Optional[float] = None
    footDiameter: Optional[float] = None


class ParameterSchema(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None


class CeramicVesselTemplateBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    category: str = Field(..., max_length=50)
    dynasty: Optional[str] = None
    region: Optional[str] = None
    material: Optional[str] = None
    typical_height: Optional[float] = None
    typical_mouth_diameter: Optional[float] = None
    typical_belly_diameter: Optional[float] = None
    typical_bottom_diameter: Optional[float] = None
    typical_volume: Optional[float] = None
    control_points: List[ControlPointSchema]
    key_parts: Optional[List[KeyPartSchema]] = None
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    references: Optional[str] = None
    image_url: Optional[str] = None
    is_public: Optional[bool] = True
    created_by: Optional[str] = None


class CeramicVesselTemplateCreate(CeramicVesselTemplateBase):
    pass


class CeramicVesselTemplateUpdate(CeramicVesselTemplateBase):
    pass


class CeramicVesselTemplate(CeramicVesselTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VesselProfileBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    template_id: Optional[int] = None
    unit: str = "mm"
    vessel_type: Optional[str] = None
    dynasty: Optional[str] = None
    provenance: Optional[str] = None
    material: Optional[str] = None
    condition_status: str = "完整"
    control_points: List[ControlPointSchema]
    repair_marks: Optional[List[RepairMarkSchema]] = None
    key_parts_identified: Optional[List[KeyPartSchema]] = None
    dimensions: Optional[DimensionsSchema] = None
    parameters: Optional[Dict[str, Any]] = None
    is_restored: bool = False
    restoration_method: Optional[str] = None
    restoration_confidence: Optional[float] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: Optional[str] = None


class VesselProfileCreate(VesselProfileBase):
    pass


class VesselProfileUpdate(VesselProfileBase):
    pass


class VesselProfile(VesselProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VesselVersionBase(BaseModel):
    profile_id: Optional[int] = None
    template_id: Optional[int] = None
    version_number: int
    version_label: Optional[str] = None
    change_summary: Optional[str] = None
    control_points: Optional[List[ControlPointSchema]] = None
    repair_marks: Optional[List[RepairMarkSchema]] = None
    dimensions: Optional[DimensionsSchema] = None
    key_parts_identified: Optional[List[KeyPartSchema]] = None
    parameters: Optional[Dict[str, Any]] = None
    restoration_confidence: Optional[float] = None
    parent_version_id: Optional[int] = None
    created_by: Optional[str] = None


class VesselVersionCreate(VesselVersionBase):
    pass


class VesselVersion(VesselVersionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class HeatmapPoint(BaseModel):
    y: float
    difference: float
    normalized: float
    zone: str


class KeyDifference(BaseModel):
    zone: str
    y_start: float
    y_end: float
    avg_diff: float
    max_diff: float
    significance: str


class DifferenceAnalysisBase(BaseModel):
    name: str = Field(..., max_length=100)
    profile_a_id: Optional[int] = None
    profile_b_id: Optional[int] = None
    template_id: Optional[int] = None
    analysis_type: str = "profile"
    heatmap_data: Optional[List[HeatmapPoint]] = None
    key_differences: Optional[List[KeyDifference]] = None
    overall_similarity: Optional[float] = None
    dimension_differences: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    created_by: Optional[str] = None


class DifferenceAnalysisCreate(DifferenceAnalysisBase):
    pass


class DifferenceAnalysis(DifferenceAnalysisBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DifferenceAnalysisRequest(BaseModel):
    profile_a_control_points: List[ControlPointSchema]
    profile_b_control_points: List[ControlPointSchema]
    profile_a_name: Optional[str] = "A"
    profile_b_name: Optional[str] = "B"
    unit: str = "mm"
    sample_count: int = 100


class RestorationAssessmentBase(BaseModel):
    profile_id: int
    overall_confidence: float
    bottom_confidence: Optional[float] = None
    mouth_confidence: Optional[float] = None
    belly_confidence: Optional[float] = None
    neck_confidence: Optional[float] = None
    shoulder_confidence: Optional[float] = None
    foot_confidence: Optional[float] = None
    fragment_coverage: Optional[float] = None
    gap_count: Optional[int] = None
    critical_gaps: Optional[List[Dict[str, Any]]] = None
    supporting_evidence: Optional[List[Dict[str, Any]]] = None
    risk_factors: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[str]] = None
    assessment_method: Optional[str] = None
    assessed_by: Optional[str] = None


class RestorationAssessmentCreate(RestorationAssessmentBase):
    pass


class RestorationAssessment(RestorationAssessmentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RestorationAssessmentRequest(BaseModel):
    control_points: List[ControlPointSchema]
    original_points: Optional[List[ControlPointSchema]] = None
    restored_points: Optional[List[ControlPointSchema]] = None
    unit: str = "mm"
    restoration_method: Optional[str] = None
    template_control_points: Optional[List[ControlPointSchema]] = None


class KeyPartsIdentificationRequest(BaseModel):
    control_points: List[ControlPointSchema]
    unit: str = "mm"
    vessel_type_hint: Optional[str] = None


class ParametricEditRequest(BaseModel):
    control_points: List[ControlPointSchema]
    dimension_type: str
    target_value: float
    unit: str = "mm"
    preserve_proportions: bool = True


class ResearchReportBase(BaseModel):
    profile_id: int
    title: str = Field(..., max_length=255)
    report_type: str = "器型分析报告"
    content: Dict[str, Any]
    sections: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    conclusions: Optional[List[str]] = None
    file_path: Optional[str] = None
    file_format: str = "json"
    author: Optional[str] = None
    keywords: Optional[List[str]] = None


class ResearchReportCreate(ResearchReportBase):
    pass


class ResearchReport(ResearchReportBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchReportGenerateRequest(BaseModel):
    profile_id: int
    report_type: str = "器型分析报告"
    include_sections: Optional[List[str]] = None
    author: Optional[str] = None
    keywords: Optional[List[str]] = None
    custom_title: Optional[str] = None


class TemplateApplyRequest(BaseModel):
    template_id: int
    scale_factor: Optional[float] = None
    target_height: Optional[float] = None
    target_belly_diameter: Optional[float] = None
