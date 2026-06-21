import type {
  Culvert, Section, Slope, Manhole, SedimentRecord, RainScenario,
  DrainageCapacityResult, SedimentTrendResult, RiskWarningResult,
  SimulationResult, ProfileResult, ReportResult,
  CeramicVesselTemplate, VesselProfile, VesselVersion,
  RestorationAssessment, ResearchReport,
  ParametricEditResult, TemplateApplyResult,
  DifferenceAnalysisResult, ReportGenerationResult,
  ControlPoint, KeyPart, DifferenceAnalysis
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

  templates: {
    list: (params?: { category?: string; dynasty?: string; keyword?: string }) => {
      const qs = params ? Object.entries(params).filter(([, v]) => v).map(([k, v]) => `${k}=${encodeURIComponent(v as string)}`).join('&') : ''
      return request<CeramicVesselTemplate[]>(`/templates/${qs ? '?' + qs : ''}`)
    },
    categories: () => request<{ categories: Record<string, string[]>; total: number }>('/templates/categories'),
    get: (id: number) => request<CeramicVesselTemplate>(`/templates/${id}`),
    preview: (id: number) => request<{ id: number; name: string; code: string; category: string; dynasty?: string; control_points: ControlPoint[]; dimensions: any; key_parts: KeyPart[]; description?: string }>(`/templates/${id}/preview`),
    create: (data: any) =>
      request<CeramicVesselTemplate>('/templates/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: any) =>
      request<CeramicVesselTemplate>(`/templates/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request(`/templates/${id}`, { method: 'DELETE' }),
    apply: (templateId: number, data: { scale_factor?: number; target_height?: number; target_belly_diameter?: number }) =>
      request<TemplateApplyResult>(`/templates/${templateId}/apply`, { method: 'POST', body: JSON.stringify(data) }),
  },

  vesselProfiles: {
    list: (params?: { condition_status?: string; vessel_type?: string; dynasty?: string; keyword?: string }) => {
      const qs = params ? Object.entries(params).filter(([, v]) => v).map(([k, v]) => `${k}=${encodeURIComponent(v as string)}`).join('&') : ''
      return request<VesselProfile[]>(`/vessel-profiles/${qs ? '?' + qs : ''}`)
    },
    get: (id: number) => request<VesselProfile>(`/vessel-profiles/${id}`),
    create: (data: any) =>
      request<VesselProfile>('/vessel-profiles/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: any) =>
      request<VesselProfile>(`/vessel-profiles/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request(`/vessel-profiles/${id}`, { method: 'DELETE' }),
    identifyKeyParts: (data: { control_points: ControlPoint[]; unit?: string; vessel_type_hint?: string }) =>
      request<{ success: boolean; key_parts: KeyPart[]; dimensions: any; count: number }>('/vessel-profiles/identify-key-parts', { method: 'POST', body: JSON.stringify(data) }),
    parametricEdit: (data: { control_points: ControlPoint[]; dimension_type: string; target_value: number; unit?: string; preserve_proportions?: boolean }) =>
      request<ParametricEditResult>('/vessel-profiles/parametric-edit', { method: 'POST', body: JSON.stringify(data) }),
    versions: {
      list: (profileId: number) => request<VesselVersion[]>(`/vessel-profiles/${profileId}/versions`),
      create: (profileId: number, data: any) =>
        request<VesselVersion>(`/vessel-profiles/${profileId}/versions`, { method: 'POST', body: JSON.stringify(data) }),
      get: (profileId: number, versionId: number) =>
        request<VesselVersion>(`/vessel-profiles/${profileId}/versions/${versionId}`),
      restore: (profileId: number, versionId: number) =>
        request<VesselProfile>(`/vessel-profiles/${profileId}/restore-version/${versionId}`, { method: 'POST' }),
    },
    assessments: {
      create: (profileId: number, data?: any) =>
        request<RestorationAssessment>(`/vessel-profiles/${profileId}/assess-restoration`, { method: 'POST', body: data ? JSON.stringify(data) : '{}' }),
      list: (profileId: number) =>
        request<RestorationAssessment[]>(`/vessel-profiles/${profileId}/assessments`),
    },
  },

  ceramicAnalysis: {
    differenceAnalysis: (data: { profile_a_control_points: ControlPoint[]; profile_b_control_points: ControlPoint[]; profile_a_name?: string; profile_b_name?: string; unit?: string; sample_count?: number }) =>
      request<DifferenceAnalysisResult>('/ceramic-analysis/difference-analysis', { method: 'POST', body: JSON.stringify(data) }),
    saveDifferenceAnalysis: (data: any) =>
      request<DifferenceAnalysis>('/ceramic-analysis/difference-analysis/save', { method: 'POST', body: JSON.stringify(data) }),
    listDifferenceAnalyses: (profileId?: number) => {
      const qs = profileId ? `?profile_id=${profileId}` : ''
      return request<DifferenceAnalysis[]>(`/ceramic-analysis/difference-analyses${qs}`)
    },
    getDifferenceAnalysis: (id: number) =>
      request<DifferenceAnalysis>(`/ceramic-analysis/difference-analyses/${id}`),
    deleteDifferenceAnalysis: (id: number) =>
      request(`/ceramic-analysis/difference-analyses/${id}`, { method: 'DELETE' }),
    generateReport: (data: { profile_id: number; report_type?: string; include_sections?: string[]; author?: string; keywords?: string[]; custom_title?: string }) =>
      request<ReportGenerationResult>('/ceramic-analysis/generate-report', { method: 'POST', body: JSON.stringify(data) }),
    reports: {
      list: (params?: { profile_id?: number; report_type?: string }) => {
        const qs = params ? Object.entries(params).filter(([, v]) => v).map(([k, v]) => `${k}=${encodeURIComponent(v as string)}`).join('&') : ''
        return request<ResearchReport[]>(`/ceramic-analysis/reports/${qs ? '?' + qs : ''}`)
      },
      get: (id: number) => request<any>(`/ceramic-analysis/reports/${id}`),
      delete: (id: number) => request(`/ceramic-analysis/reports/${id}`, { method: 'DELETE' }),
      export: (id: number, format: string = 'json') =>
        `${API_BASE_URL}/ceramic-analysis/reports/${id}/export?format=${format}`,
      download: (id: number) =>
        `${API_BASE_URL}/ceramic-analysis/reports/${id}/download`,
    },
  },
}
