from pydantic import BaseModel, Field
from typing import Optional, List
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
    parameters: Optional[dict] = None


class ReportResult(BaseModel):
    report_id: str
    filename: str
    file_url: str
    created_at: datetime
