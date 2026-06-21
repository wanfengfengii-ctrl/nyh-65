from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from datetime import datetime

from routers import culverts, sections, slopes, manholes, sediment, scenarios, analysis, reports
from routers import templates as templates_router
from routers import vessel_profiles as vessel_profiles_router
from routers import ceramic as ceramic_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="陶瓷器型智能分析系统",
    description="面向陶瓷研究人员的器型智能分析系统。支持剖面绘制、3D预览、尺寸估算、容量计算、方案对比、修坯标记、残损复原、标准器型模板库、关键部位自动识别、参数化尺寸联动编辑、复原方案可信度评估、器型差异热区分析、历史版本追踪和研究报告导出等功能，支持对完整器与残损器进行统一建模、复原、比对和结构化数据输出。",
    version="3.0.0"
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
app.include_router(templates_router.router)
app.include_router(vessel_profiles_router.router)
app.include_router(ceramic_router.router)


@app.get("/")
def root():
    return {
        "name": "陶瓷器型智能分析系统",
        "version": "3.0.0",
        "description": "面向陶瓷研究人员的器型智能分析系统",
        "status": "running",
        "start_time": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "api_prefix": "/api",
        "modules": [
            "剖面绘制", "3D预览", "尺寸估算", "容量计算",
            "方案对比", "修坯标记", "残损复原",
            "标准器型模板库", "关键部位识别", "参数化尺寸联动",
            "可信度评估", "差异热区分析", "历史版本追踪", "研究报告导出"
        ]
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


def init_ceramic_sample_data():
    from database import SessionLocal
    from models import CeramicVesselTemplate, VesselProfile

    db = SessionLocal()
    try:
        if db.query(CeramicVesselTemplate).count() == 0:
            standard_templates = [
                {
                    "name": "唐代典型罐型",
                    "code": "TPL-TANG-GUAN-001",
                    "category": "罐",
                    "dynasty": "唐代",
                    "region": "中原地区",
                    "material": "青瓷",
                    "points": [
                        {"id": 1, "x": 50, "y": 0},
                        {"id": 2, "x": 65, "y": 30},
                        {"id": 3, "x": 90, "y": 80},
                        {"id": 4, "x": 110, "y": 150},
                        {"id": 5, "x": 100, "y": 220},
                        {"id": 6, "x": 75, "y": 270},
                        {"id": 7, "x": 55, "y": 300},
                    ],
                    "description": "唐代典型圆腹罐，鼓腹、短颈、平底，常见于中原窑口。",
                    "references": "《中国陶瓷史》唐代部分",
                },
                {
                    "name": "宋代梅瓶",
                    "code": "TPL-SONG-MEIPING-001",
                    "category": "瓶",
                    "dynasty": "宋代",
                    "region": "景德镇窑系",
                    "material": "青白瓷",
                    "points": [
                        {"id": 1, "x": 35, "y": 0},
                        {"id": 2, "x": 45, "y": 40},
                        {"id": 3, "x": 60, "y": 80},
                        {"id": 4, "x": 95, "y": 150},
                        {"id": 5, "x": 100, "y": 220},
                        {"id": 6, "x": 80, "y": 280},
                        {"id": 7, "x": 50, "y": 320},
                        {"id": 8, "x": 25, "y": 350},
                        {"id": 9, "x": 20, "y": 380},
                    ],
                    "description": "宋代梅瓶标准器型，小口、短颈、丰肩、敛腹、圈足。",
                    "references": "宋代景德镇青白瓷梅瓶标准参考",
                },
                {
                    "name": "元代青花大盘",
                    "code": "TPL-YUAN-PAN-001",
                    "category": "盘",
                    "dynasty": "元代",
                    "region": "景德镇",
                    "material": "青花瓷",
                    "points": [
                        {"id": 1, "x": 90, "y": 0},
                        {"id": 2, "x": 105, "y": 15},
                        {"id": 3, "x": 120, "y": 25},
                        {"id": 4, "x": 180, "y": 35},
                        {"id": 5, "x": 200, "y": 45},
                    ],
                    "description": "元代青花大盘，折沿、浅腹、平底，口径通常在40cm以上。",
                    "references": "元青花典型器型参考",
                },
                {
                    "name": "明代玉壶春瓶",
                    "code": "TPL-MING-YUHUCHUN-001",
                    "category": "瓶",
                    "dynasty": "明代",
                    "region": "景德镇官窑",
                    "material": "青花/釉里红",
                    "points": [
                        {"id": 1, "x": 45, "y": 0},
                        {"id": 2, "x": 55, "y": 30},
                        {"id": 3, "x": 60, "y": 60},
                        {"id": 4, "x": 40, "y": 90},
                        {"id": 5, "x": 30, "y": 130},
                        {"id": 6, "x": 25, "y": 170},
                        {"id": 7, "x": 30, "y": 210},
                        {"id": 8, "x": 50, "y": 240},
                        {"id": 9, "x": 45, "y": 270},
                        {"id": 10, "x": 30, "y": 290},
                        {"id": 11, "x": 35, "y": 310},
                    ],
                    "description": "玉壶春瓶为明代经典器型，撇口、细颈、垂腹、圈足。",
                    "references": "明代官窑瓷器标准器型",
                },
                {
                    "name": "清代康熙将军罐",
                    "code": "TPL-QING-JIANGJUN-001",
                    "category": "罐",
                    "dynasty": "清代康熙",
                    "region": "景德镇",
                    "material": "青花/五彩",
                    "points": [
                        {"id": 1, "x": 55, "y": 0},
                        {"id": 2, "x": 75, "y": 50},
                        {"id": 3, "x": 105, "y": 120},
                        {"id": 4, "x": 115, "y": 200},
                        {"id": 5, "x": 100, "y": 280},
                        {"id": 6, "x": 70, "y": 340},
                        {"id": 7, "x": 50, "y": 380},
                        {"id": 8, "x": 55, "y": 410},
                    ],
                    "description": "将军罐，直口、丰肩、敛腹、平底，器型高大挺拔，因宝珠顶盖形似将军盔帽得名。",
                    "references": "清代康熙青花瓷器研究",
                },
                {
                    "name": "龙山文化蛋壳黑陶杯",
                    "code": "TPL-LONGSHAN-EGGSHELL-001",
                    "category": "杯",
                    "dynasty": "新石器时代龙山",
                    "region": "山东龙山",
                    "material": "黑陶",
                    "points": [
                        {"id": 1, "x": 20, "y": 0},
                        {"id": 2, "x": 18, "y": 40},
                        {"id": 3, "x": 22, "y": 70},
                        {"id": 4, "x": 28, "y": 90},
                        {"id": 5, "x": 35, "y": 110},
                        {"id": 6, "x": 40, "y": 125},
                    ],
                    "description": "龙山文化蛋壳黑陶高柄杯，器薄如蛋壳，代表史前制陶最高水平。",
                    "references": "《山东龙山文化陶器研究》",
                },
                {
                    "name": "宋代官窑鬲式炉",
                    "code": "TPL-SONG-GEYAO-LISHILU-001",
                    "category": "炉",
                    "dynasty": "宋代",
                    "region": "官窑",
                    "material": "青瓷",
                    "points": [
                        {"id": 1, "x": 15, "y": 0},
                        {"id": 2, "x": 25, "y": 20},
                        {"id": 3, "x": 45, "y": 40},
                        {"id": 4, "x": 65, "y": 60},
                        {"id": 5, "x": 60, "y": 80},
                        {"id": 6, "x": 40, "y": 100},
                    ],
                    "description": "鬲式炉仿青铜器鬲造型，宋代官窑常见器型，用于焚香。",
                    "references": "宋代官窑瓷器标准参考",
                },
            ]

            for tpl_data in standard_templates:
                tpl = CeramicVesselTemplate(
                    name=tpl_data["name"],
                    code=tpl_data["code"],
                    category=tpl_data["category"],
                    dynasty=tpl_data["dynasty"],
                    region=tpl_data["region"],
                    material=tpl_data["material"],
                    control_points=tpl_data["points"],
                    description=tpl_data["description"],
                    references=tpl_data["references"],
                    is_public=True,
                    created_by="system",
                )
                db.add(tpl)

            if db.query(VesselProfile).count() == 0:
                sample_profiles = [
                    {
                        "name": "XX窑出土唐代青瓷罐",
                        "code": "VP-TANG-001",
                        "template_idx": 0,
                        "vessel_type": "罐",
                        "dynasty": "唐代",
                        "provenance": "河南省XX市XX窑址",
                        "material": "青瓷",
                        "condition_status": "完整",
                        "description": "1985年窑址发掘出土，器型规整，釉色青中泛黄。",
                        "tags": ["出土品", "青瓷", "唐代", "窑址"],
                        "scale_factor": 0.95,
                    },
                    {
                        "name": "馆藏宋代青白瓷梅瓶",
                        "code": "VP-SONG-002",
                        "template_idx": 1,
                        "vessel_type": "瓶",
                        "dynasty": "南宋",
                        "provenance": "江西省XX市",
                        "material": "青白瓷",
                        "condition_status": "残损",
                        "is_restored": True,
                        "restoration_method": "适中",
                        "description": "口沿有残损，经复原处理，肩部有开片纹。",
                        "tags": ["馆藏", "青白瓷", "宋代", "残损复原"],
                        "scale_factor": 1.05,
                    },
                ]

                db.flush()
                all_templates = db.query(CeramicVesselTemplate).all()
                tpl_list = list(all_templates)

                for prof_data in sample_profiles:
                    tpl = tpl_list[prof_data.get("template_idx", 0)]
                    scale = prof_data.get("scale_factor", 1.0)
                    cps = [
                        {"id": i, "x": p["x"] * scale, "y": p["y"] * scale}
                        for i, p in enumerate(tpl.control_points, start=1)
                    ]
                    if prof_data.get("condition_status") == "残损":
                        cps = cps[:max(3, len(cps) - 2)]

                    profile = VesselProfile(
                        name=prof_data["name"],
                        code=prof_data["code"],
                        template_id=tpl.id,
                        unit="mm",
                        vessel_type=prof_data.get("vessel_type"),
                        dynasty=prof_data.get("dynasty"),
                        provenance=prof_data.get("provenance"),
                        material=prof_data.get("material"),
                        condition_status=prof_data.get("condition_status", "完整"),
                        control_points=cps,
                        repair_marks=[],
                        is_restored=prof_data.get("is_restored", False),
                        restoration_method=prof_data.get("restoration_method"),
                        description=prof_data.get("description"),
                        tags=prof_data.get("tags"),
                        created_by="system",
                    )
                    db.add(profile)

            db.commit()
            print("陶瓷器型示例数据初始化完成（7个模板，2个档案）")

    except Exception as e:
        db.rollback()
        print(f"初始化陶瓷数据时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


init_sample_data()
init_ceramic_sample_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
