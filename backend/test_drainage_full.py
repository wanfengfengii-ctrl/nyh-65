import requests
response = requests.post('http://localhost:8001/api/analysis/drainage-capacity', json={'culvert_id': 1, 'scenario_ids': [1,2,3,4,5]})
results = response.json()
print("=" * 80)
print("排水能力对比分析结果")
print("=" * 80)
print(f"{'降雨情景':<15} {'设计流量(m³/s)':<15} {'实际能力(m³/s)':<15} {'溢流(m³/s)':<12} {'溢流比例':<12} {'状态':<10}")
print("-" * 80)
for r in results:
    status = "✓ 充足" if r['is_sufficient'] else "✗ 不足"
    print(f"{r['scenario_name']:<15} {r['design_flow']:<15.4f} {r['actual_capacity']:<15.4f} {r['overflow']:<12.4f} {r['overflow_ratio']*100:<12.2f}% {status:<10}")
print("=" * 80)
