import type {
  Culvert, Section, Slope, Manhole, SedimentRecord, RainScenario,
  DrainageCapacityResult, SedimentTrendResult, RiskWarningResult,
  SimulationResult, ProfileResult, ReportResult
} from '@/types'

const API_BASE_URL = 'http://localhost:8001/api'

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return response.json()
}

export const api = {
  culverts: {
    list: () => request<Culvert[]>('/culverts/'),
    get: (id: number) => request<Culvert>(`/culverts/${id}`),
    create: (data: Omit<Culvert, 'id' | 'created_at' | 'updated_at'>) =>
      request<Culvert>('/culverts/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Omit<Culvert, 'id' | 'created_at' | 'updated_at'>) =>
      request<Culvert>(`/culverts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request(`/culverts/${id}`, { method: 'DELETE' }),
  },

  sections: {
    list: (culvertId?: number) =>
      request<Section[]>(`/sections/${culvertId ? `?culvert_id=${culvertId}` : ''}`),
    get: (id: number) => request<Section>(`/sections/${id}`),
    create: (data: Omit<Section, 'id' | 'created_at'>) =>
      request<Section>('/sections/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Omit<Section, 'id' | 'created_at'>) =>
      request<Section>(`/sections/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request(`/sections/${id}`, { method: 'DELETE' }),
  },

  slopes: {
    list: (sectionId?: number) =>
      request<Slope[]>(`/slopes/${sectionId ? `?section_id=${sectionId}` : ''}`),
    get: (id: number) => request<Slope>(`/slopes/${id}`),
    create: (data: Omit<Slope, 'id' | 'created_at'>) =>
      request<Slope>('/slopes/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Omit<Slope, 'id' | 'created_at'>) =>
      request<Slope>(`/slopes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request(`/slopes/${id}`, { method: 'DELETE' }),
  },

  manholes: {
    list: (culvertId?: number) =>
      request<Manhole[]>(`/manholes/${culvertId ? `?culvert_id=${culvertId}` : ''}`),
    get: (id: number) => request<Manhole>(`/manholes/${id}`),
    create: (data: Omit<Manhole, 'id' | 'created_at' | 'updated_at'>) =>
      request<Manhole>('/manholes/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Omit<Manhole, 'id' | 'created_at' | 'updated_at'>) =>
      request<Manhole>(`/manholes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request(`/manholes/${id}`, { method: 'DELETE' }),
  },

  sediment: {
    list: (culvertId?: number) =>
      request<SedimentRecord[]>(`/sediment/${culvertId ? `?culvert_id=${culvertId}` : ''}`),
    get: (id: number) => request<SedimentRecord>(`/sediment/${id}`),
    create: (data: Omit<SedimentRecord, 'id' | 'created_at'>) =>
      request<SedimentRecord>('/sediment/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Omit<SedimentRecord, 'id' | 'created_at'>) =>
      request<SedimentRecord>(`/sediment/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request(`/sediment/${id}`, { method: 'DELETE' }),
  },

  scenarios: {
    list: () => request<RainScenario[]>('/scenarios/'),
    getDefault: () => request<RainScenario>('/scenarios/default'),
    get: (id: number) => request<RainScenario>(`/scenarios/${id}`),
    create: (data: Omit<RainScenario, 'id' | 'created_at'>) =>
      request<RainScenario>('/scenarios/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Omit<RainScenario, 'id' | 'created_at'>) =>
      request<RainScenario>(`/scenarios/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request(`/scenarios/${id}`, { method: 'DELETE' }),
  },

  analysis: {
    drainageCapacity: (culvertId: number, scenarioIds: number[]) =>
      request<DrainageCapacityResult[]>('/analysis/drainage-capacity', {
        method: 'POST',
        body: JSON.stringify({ culvert_id: culvertId, scenario_ids: scenarioIds }),
      }),
    sedimentTrend: (culvertId: number, months: number = 12) =>
      request<SedimentTrendResult>('/analysis/sediment-trend', {
        method: 'POST',
        body: JSON.stringify({ culvert_id: culvertId, months }),
      }),
    riskWarnings: (culvertId: number) =>
      request<RiskWarningResult>(`/analysis/risk-warnings/${culvertId}`),
    simulate: (culvertId: number, planType: string, parameters: Record<string, any>) =>
      request<SimulationResult>('/analysis/simulate', {
        method: 'POST',
        body: JSON.stringify({ culvert_id: culvertId, plan_type: planType, parameters }),
      }),
    profile: (culvertId: number) =>
      request<ProfileResult>(`/analysis/profile/${culvertId}`),
  },

  reports: {
    generate: (culvertId: number, reportType: string, includeCharts: boolean = true) =>
      request<ReportResult>('/reports/generate', {
        method: 'POST',
        body: JSON.stringify({ culvert_id: culvertId, report_type: reportType, include_charts: includeCharts }),
      }),
    list: () => request('/reports/list'),
    download: (filename: string) => `${API_BASE_URL}/reports/download/${filename}`,
  },
}
