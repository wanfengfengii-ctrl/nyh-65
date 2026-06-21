import requests
import json

BASE_URL = "http://localhost:8001/api"

def test_api():
    print("=" * 60)
    print("古城地下排水暗渠管理系统 API 测试")
    print("=" * 60)

    try:
        print("\n1. 测试根路径...")
        response = requests.get("http://localhost:8001/")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)[:200]}...")

        print("\n2. 测试健康检查...")
        response = requests.get(f"{BASE_URL}/health")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {json.dumps(response.json(), ensure_ascii=False)}")

        print("\n3. 测试获取暗渠列表...")
        response = requests.get(f"{BASE_URL}/culverts/")
        print(f"   状态码: {response.status_code}")
        culverts = response.json()
        print(f"   暗渠数量: {len(culverts)}")
        if culverts:
            print(f"   第一个暗渠: {culverts[0]['name']} (ID: {culverts[0]['id']})")
            culvert_id = culverts[0]['id']

        print("\n4. 测试获取断面列表...")
        response = requests.get(f"{BASE_URL}/sections/?culvert_id={culvert_id}")
        print(f"   状态码: {response.status_code}")
        sections = response.json()
        print(f"   断面数量: {len(sections)}")

        print("\n5. 测试获取检查井列表...")
        response = requests.get(f"{BASE_URL}/manholes/?culvert_id={culvert_id}")
        print(f"   状态码: {response.status_code}")
        manholes = response.json()
        print(f"   检查井数量: {len(manholes)}")

        print("\n6. 测试获取淤积记录...")
        response = requests.get(f"{BASE_URL}/sediment/?culvert_id={culvert_id}")
        print(f"   状态码: {response.status_code}")
        sediment = response.json()
        print(f"   淤积记录数量: {len(sediment)}")

        print("\n7. 测试获取降雨情景...")
        response = requests.get(f"{BASE_URL}/scenarios/")
        print(f"   状态码: {response.status_code}")
        scenarios = response.json()
        print(f"   降雨情景数量: {len(scenarios)}")
        scenario_ids = [s['id'] for s in scenarios[:3]]
        print(f"   情景ID: {scenario_ids}")

        print("\n8. 测试排水能力分析...")
        response = requests.post(
            f"{BASE_URL}/analysis/drainage-capacity",
            json={"culvert_id": culvert_id, "scenario_ids": scenario_ids}
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"   分析结果数量: {len(results)}")
            for r in results[:2]:
                print(f"   - {r['scenario_name']}: 流量 {r['design_flow']:.2f} m³/s, 能力 {r['actual_capacity']:.2f} m³/s, 满足: {r['is_sufficient']}")

        print("\n9. 测试淤积趋势分析...")
        response = requests.post(
            f"{BASE_URL}/analysis/sediment-trend",
            json={"culvert_id": culvert_id, "months": 12}
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   暗渠名称: {result['culvert_name']}")
            print(f"   风险等级: {result['risk_level']}")
            print(f"   平均淤积速率: {result['avg_sediment_rate']*1000:.2f} mm/月")
            print(f"   12个月预测: {result['predicted_thickness_12m']*100:.1f} cm")

        print("\n10. 测试风险预警...")
        response = requests.get(f"{BASE_URL}/analysis/risk-warnings/{culvert_id}")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   风险区段总数: {result['total_risk_sections']}")
            print(f"   高风险: {result['high_risk_count']}, 中风险: {result['medium_risk_count']}, 低风险: {result['low_risk_count']}")

        print("\n11. 测试方案模拟 - 清淤...")
        response = requests.post(
            f"{BASE_URL}/analysis/simulate",
            json={"culvert_id": culvert_id, "plan_type": "cleaning", "parameters": {"cleaning_ratio": 1.0}}
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   方案类型: {result['plan_type']}")
            print(f"   原能力: {result['original_capacity']:.2f} m³/s")
            print(f"   模拟后: {result['simulated_capacity']:.2f} m³/s")
            print(f"   提升比例: +{result['capacity_improvement']*100/result['original_capacity']:.1f}%")
            print(f"   预估费用: {result['cost_estimate']:.0f} 元")

        print("\n12. 测试纵断面图...")
        response = requests.get(f"{BASE_URL}/analysis/profile/{culvert_id}")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   暗渠名称: {result['culvert_name']}")
            print(f"   最高高程: {result['max_elevation']:.2f} m")
            print(f"   最低高程: {result['min_elevation']:.2f} m")
            print(f"   平均坡度: {result['avg_slope']*1000:.2f}‰")
            print(f"   剖面点数: {len(result['profile_points'])}")

        print("\n13. 测试生成风险报告...")
        response = requests.post(
            f"{BASE_URL}/reports/generate",
            json={"culvert_id": culvert_id, "report_type": "risk", "include_charts": True}
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   报告ID: {result['report_id']}")
            print(f"   文件名: {result['filename']}")
            print(f"   下载链接: {result['file_url']}")

        print("\n" + "=" * 60)
        print("所有API测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_api()
