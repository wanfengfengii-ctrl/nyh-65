from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
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
