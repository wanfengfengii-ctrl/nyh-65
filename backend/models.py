from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Culvert(Base):
    __tablename__ = "culverts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    location = Column(String(255))
    length = Column(Float, nullable=False)
    material = Column(String(50))
    construction_year = Column(Integer)
    status = Column(String(20), default="正常")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sections = relationship("Section", back_populates="culvert", cascade="all, delete-orphan")
    manholes = relationship("Manhole", back_populates="culvert", cascade="all, delete-orphan")
    sediment_records = relationship("SedimentRecord", back_populates="culvert", cascade="all, delete-orphan")


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    culvert_id = Column(Integer, ForeignKey("culverts.id"), nullable=False)
    station = Column(Float, nullable=False)
    shape = Column(String(30), nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float)
    diameter = Column(Float)
    area = Column(Float)
    perimeter = Column(Float)
    hydraulic_radius = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    culvert = relationship("Culvert", back_populates="sections")
    slopes = relationship("Slope", back_populates="section", cascade="all, delete-orphan")


class Slope(Base):
    __tablename__ = "slopes"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    start_station = Column(Float, nullable=False)
    end_station = Column(Float, nullable=False)
    slope_value = Column(Float, nullable=False)
    start_elevation = Column(Float)
    end_elevation = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    section = relationship("Section", back_populates="slopes")


class Manhole(Base):
    __tablename__ = "manholes"

    id = Column(Integer, primary_key=True, index=True)
    culvert_id = Column(Integer, ForeignKey("culverts.id"), nullable=False)
    name = Column(String(50), nullable=False)
    code = Column(String(50), nullable=False)
    station = Column(Float, nullable=False)
    elevation = Column(Float)
    depth = Column(Float)
    diameter = Column(Float)
    material = Column(String(50))
    condition = Column(String(20), default="良好")
    has_inlet = Column(Boolean, default=False)
    has_outlet = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    culvert = relationship("Culvert", back_populates="manholes")


class SedimentRecord(Base):
    __tablename__ = "sediment_records"

    id = Column(Integer, primary_key=True, index=True)
    culvert_id = Column(Integer, ForeignKey("culverts.id"), nullable=False)
    record_date = Column(DateTime, nullable=False)
    start_station = Column(Float, nullable=False)
    end_station = Column(Float, nullable=False)
    sediment_thickness = Column(Float, nullable=False)
    sediment_volume = Column(Float)
    sediment_type = Column(String(50))
    survey_method = Column(String(50))
    operator = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    culvert = relationship("Culvert", back_populates="sediment_records")


class RainScenario(Base):
    __tablename__ = "rain_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    return_period = Column(Integer, nullable=False)
    rainfall_duration = Column(Float, nullable=False)
    total_rainfall = Column(Float, nullable=False)
    rainfall_distribution = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SimulationPlan(Base):
    __tablename__ = "simulation_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    culvert_id = Column(Integer, ForeignKey("culverts.id"), nullable=False)
    plan_type = Column(String(20), nullable=False)
    description = Column(Text)
    parameters = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskWarning(Base):
    __tablename__ = "risk_warnings"

    id = Column(Integer, primary_key=True, index=True)
    culvert_id = Column(Integer, ForeignKey("culverts.id"), nullable=False)
    warning_type = Column(String(50), nullable=False)
    warning_level = Column(String(20), nullable=False)
    start_station = Column(Float)
    end_station = Column(Float)
    description = Column(Text)
    suggestion = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_acknowledged = Column(Boolean, default=False)


class CeramicVesselTemplate(Base):
    __tablename__ = "ceramic_vessel_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    dynasty = Column(String(50))
    region = Column(String(100))
    material = Column(String(50))
    typical_height = Column(Float)
    typical_mouth_diameter = Column(Float)
    typical_belly_diameter = Column(Float)
    typical_bottom_diameter = Column(Float)
    typical_volume = Column(Float)
    control_points = Column(JSON, nullable=False)
    key_parts = Column(JSON)
    parameters = Column(JSON)
    description = Column(Text)
    references = Column(Text)
    image_url = Column(String(255))
    is_public = Column(Boolean, default=True)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("VesselVersion", back_populates="template", cascade="all, delete-orphan")


class VesselProfile(Base):
    __tablename__ = "vessel_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    template_id = Column(Integer, ForeignKey("ceramic_vessel_templates.id"))
    unit = Column(String(10), default="mm")
    vessel_type = Column(String(50))
    dynasty = Column(String(50))
    provenance = Column(String(255))
    material = Column(String(50))
    condition_status = Column(String(20), default="完整")
    control_points = Column(JSON, nullable=False)
    repair_marks = Column(JSON)
    key_parts_identified = Column(JSON)
    dimensions = Column(JSON)
    parameters = Column(JSON)
    is_restored = Column(Boolean, default=False)
    restoration_method = Column(String(50))
    restoration_confidence = Column(Float)
    description = Column(Text)
    tags = Column(JSON)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    template = relationship("CeramicVesselTemplate")
    versions = relationship("VesselVersion", back_populates="profile", cascade="all, delete-orphan", foreign_keys="VesselVersion.profile_id")
    reports = relationship("ResearchReport", back_populates="profile", cascade="all, delete-orphan")


class VesselVersion(Base):
    __tablename__ = "vessel_versions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("vessel_profiles.id"))
    template_id = Column(Integer, ForeignKey("ceramic_vessel_templates.id"))
    version_number = Column(Integer, nullable=False)
    version_label = Column(String(100))
    change_summary = Column(Text)
    control_points = Column(JSON)
    repair_marks = Column(JSON)
    dimensions = Column(JSON)
    key_parts_identified = Column(JSON)
    parameters = Column(JSON)
    restoration_confidence = Column(Float)
    parent_version_id = Column(Integer, ForeignKey("vessel_versions.id"))
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("VesselProfile", back_populates="versions", foreign_keys=[profile_id])
    template = relationship("CeramicVesselTemplate", back_populates="versions", foreign_keys=[template_id])
    parent = relationship("VesselVersion", remote_side=[id])


class DifferenceAnalysis(Base):
    __tablename__ = "difference_analyses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    profile_a_id = Column(Integer, ForeignKey("vessel_profiles.id"))
    profile_b_id = Column(Integer, ForeignKey("vessel_profiles.id"))
    template_id = Column(Integer, ForeignKey("ceramic_vessel_templates.id"))
    analysis_type = Column(String(30), default="profile")
    heatmap_data = Column(JSON)
    key_differences = Column(JSON)
    overall_similarity = Column(Float)
    dimension_differences = Column(JSON)
    description = Column(Text)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    profile_a = relationship("VesselProfile", foreign_keys=[profile_a_id])
    profile_b = relationship("VesselProfile", foreign_keys=[profile_b_id])
    template = relationship("CeramicVesselTemplate", foreign_keys=[template_id])


class RestorationAssessment(Base):
    __tablename__ = "restoration_assessments"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("vessel_profiles.id"), nullable=False)
    overall_confidence = Column(Float, nullable=False)
    bottom_confidence = Column(Float)
    mouth_confidence = Column(Float)
    belly_confidence = Column(Float)
    neck_confidence = Column(Float)
    shoulder_confidence = Column(Float)
    foot_confidence = Column(Float)
    fragment_coverage = Column(Float)
    gap_count = Column(Integer)
    critical_gaps = Column(JSON)
    supporting_evidence = Column(JSON)
    risk_factors = Column(JSON)
    recommendations = Column(JSON)
    assessment_method = Column(String(50))
    assessed_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("VesselProfile")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("vessel_profiles.id"), nullable=False)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), default="器型分析报告")
    content = Column(JSON, nullable=False)
    sections = Column(JSON)
    summary = Column(Text)
    conclusions = Column(JSON)
    file_path = Column(String(255))
    file_format = Column(String(20), default="json")
    author = Column(String(50))
    keywords = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("VesselProfile", back_populates="reports")
