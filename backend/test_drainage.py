import requests
response = requests.post('http://localhost:8001/api/analysis/drainage-capacity', json={'culvert_id': 1, 'scenario_ids': [1,2,3]})
results = response.json()
for r in results:
    print(f"{r['scenario_name']}: 设计流量={r['design_flow']:.4f} m³/s, 实际能力={r['actual_capacity']:.4f} m³/s, 溢流={r['overflow']:.4f} m³/s, 满足={r['is_sufficient']}")
