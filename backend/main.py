from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from datetime import datetime

from routers import culverts, sections, slopes, manholes, sediment, scenarios, analysis, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="古城地下排水暗渠管理与风险分析系统",
    description="面向多情景研判的古城地下排水暗渠管理系统，支持暗渠、检查井、断面尺寸、坡度及淤积记录管理，提供降雨情景排水能力对比、淤积趋势分析、高风险区段预警、清淤或断面调整方案模拟、纵断面图展示及风险报告输出等功能。",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(culverts.router)
app.include_router(sections.router)
app.include_router(slopes.router)
app.include_router(manholes.router)
app.include_router(sediment.router)
app.include_router(scenarios.router)
app.include_router(analysis.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "name": "古城地下排水暗渠管理与风险分析系统",
        "version": "2.0.0",
        "description": "面向多情景研判的古城地下排水暗渠管理系统",
        "status": "running",
        "start_time": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "api_prefix": "/api"
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


def init_sample_data():
    from database import SessionLocal
    from models import Culvert, Section, Slope, Manhole, SedimentRecord, RainScenario

    db = SessionLocal()

    try:
        if db.query(Culvert).count() == 0:
            culvert1 = Culvert(
                name="东大街排水暗渠",
                code="DD-001",
                location="古城东大街",
                length=520.0,
                material="砖石结构",
                construction_year=1958,
                status="正常",
                description="东大街主排水暗渠，历史悠久，保护价值高"
            )
            culvert2 = Culvert(
                name="西大街排水暗渠",
                code="DD-002",
                location="古城西大街",
                length=480.0,
                material="钢筋混凝土",
                construction_year=1985,
                status="正常",
                description="西大街主排水暗渠，80年代改造"
            )
            db.add_all([culvert1, culvert2])
            db.flush()

            section1_0 = Section(
                culvert_id=culvert1.id,
                station=0,
                shape="拱形",
                width=2.0,
                height=2.5,
                area=4.35,
                perimeter=7.14,
                hydraulic_radius=0.61,
                description="起点断面"
            )
            section1_200 = Section(
                culvert_id=culvert1.id,
                station=200,
                shape="拱形",
                width=2.0,
                height=2.5,
                area=4.35,
                perimeter=7.14,
                hydraulic_radius=0.61,
                description="中段断面"
            )
            section1_520 = Section(
                culvert_id=culvert1.id,
                station=520,
                shape="拱形",
                width=2.0,
                height=2.5,
                area=4.35,
                perimeter=7.14,
                hydraulic_radius=0.61,
                description="终点断面"
            )
            db.add_all([section1_0, section1_200, section1_520])
            db.flush()

            slope1 = Slope(
                section_id=section1_0.id,
                start_station=0,
                end_station=260,
                slope_value=0.003,
                start_elevation=12.5,
                end_elevation=11.72,
                description="上段坡度"
            )
            slope2 = Slope(
                section_id=section1_520.id,
                start_station=260,
                end_station=520,
                slope_value=0.004,
                start_elevation=11.72,
                end_elevation=10.68,
                description="下段坡度"
            )
            db.add_all([slope1, slope2])

            manhole1 = Manhole(
                culvert_id=culvert1.id,
                name="1号检查井",
                code="MH-001",
                station=0,
                elevation=12.5,
                depth=2.5,
                diameter=1.2,
                material="砖砌",
                condition="良好",
                has_inlet=True,
                has_outlet=False,
                description="暗渠起点检查井"
            )
            manhole2 = Manhole(
                culvert_id=culvert1.id,
                name="2号检查井",
                code="MH-002",
                station=200,
                elevation=11.9,
                depth=2.5,
                diameter=1.2,
                material="砖砌",
                condition="良好",
                has_inlet=False,
                has_outlet=False,
                description="中段检查井"
            )
            manhole3 = Manhole(
                culvert_id=culvert1.id,
                name="3号检查井",
                code="MH-003",
                station=520,
                elevation=10.68,
                depth=2.5,
                diameter=1.2,
                material="砖砌",
                condition="一般",
                has_inlet=False,
                has_outlet=True,
                description="暗渠终点检查井"
            )
            db.add_all([manhole1, manhole2, manhole3])

            sediment1 = SedimentRecord(
                culvert_id=culvert1.id,
                record_date=datetime(2025, 1, 15),
                start_station=0,
                end_station=200,
                sediment_thickness=0.35,
                sediment_volume=105.0,
                sediment_type="泥沙混合",
                survey_method="人工测量",
                operator="张工",
                description="上段淤积测量"
            )
            sediment2 = SedimentRecord(
                culvert_id=culvert1.id,
                record_date=datetime(2025, 1, 15),
                start_station=200,
                end_station=400,
                sediment_thickness=0.65,
                sediment_volume=195.0,
                sediment_type="泥沙混合",
                survey_method="人工测量",
                operator="张工",
                description="中段淤积测量"
            )
            sediment3 = SedimentRecord(
                culvert_id=culvert1.id,
                record_date=datetime(2025, 1, 15),
                start_station=400,
                end_station=520,
                sediment_thickness=0.85,
                sediment_volume=153.0,
                sediment_type="泥沙混合",
                survey_method="人工测量",
                operator="张工",
                description="下段淤积测量"
            )
            sediment4 = SedimentRecord(
                culvert_id=culvert1.id,
                record_date=datetime(2025, 6, 20),
                start_station=0,
                end_station=200,
                sediment_thickness=0.42,
                sediment_volume=126.0,
                sediment_type="泥沙混合",
                survey_method="人工测量",
                operator="李工",
                description="上段淤积复测"
            )
            sediment5 = SedimentRecord(
                culvert_id=culvert1.id,
                record_date=datetime(2025, 6, 20),
                start_station=200,
                end_station=400,
                sediment_thickness=0.72,
                sediment_volume=216.0,
                sediment_type="泥沙混合",
                survey_method="人工测量",
                operator="李工",
                description="中段淤积复测"
            )
            sediment6 = SedimentRecord(
                culvert_id=culvert1.id,
                record_date=datetime(2025, 6, 20),
                start_station=400,
                end_station=520,
                sediment_thickness=0.92,
                sediment_volume=165.6,
                sediment_type="泥沙混合",
                survey_method="人工测量",
                operator="李工",
                description="下段淤积复测"
            )
            db.add_all([sediment1, sediment2, sediment3, sediment4, sediment5, sediment6])

            if db.query(RainScenario).count() == 0:
                scenario1 = RainScenario(
                    name="1年一遇降雨",
                    description="小雨，年平均降雨强度",
                    return_period=1,
                    rainfall_duration=24,
                    total_rainfall=50,
                    rainfall_distribution="均匀分布",
                    is_default=False
                )
                scenario2 = RainScenario(
                    name="5年一遇降雨",
                    description="中雨，常规排水设计标准",
                    return_period=5,
                    rainfall_duration=24,
                    total_rainfall=100,
                    rainfall_distribution="雨峰在前",
                    is_default=True
                )
                scenario3 = RainScenario(
                    name="10年一遇降雨",
                    description="大雨，重要区域排水设计标准",
                    return_period=10,
                    rainfall_duration=24,
                    total_rainfall=150,
                    rainfall_distribution="雨峰在中",
                    is_default=False
                )
                scenario4 = RainScenario(
                    name="50年一遇降雨",
                    description="暴雨，防洪标准",
                    return_period=50,
                    rainfall_duration=24,
                    total_rainfall=250,
                    rainfall_distribution="雨峰在后",
                    is_default=False
                )
                scenario5 = RainScenario(
                    name="100年一遇降雨",
                    description="特大暴雨，校核标准",
                    return_period=100,
                    rainfall_duration=24,
                    total_rainfall=350,
                    rainfall_distribution="雨峰在后",
                    is_default=False
                )
                db.add_all([scenario1, scenario2, scenario3, scenario4, scenario5])

            db.commit()
            print("示例数据初始化完成")

    except Exception as e:
        db.rollback()
        print(f"初始化数据时出错: {e}")
    finally:
        db.close()


init_sample_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
