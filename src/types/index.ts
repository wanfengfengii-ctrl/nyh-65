export interface ControlPoint {
  id: number
  x: number
  y: number
}

export interface RepairMark {
  pointId: number
  description?: string
}

export type Unit = 'mm' | 'cm'

export interface ProfileScheme {
  id: string
  name: string
  unit: Unit
  controlPoints: ControlPoint[]
  repairMarks: RepairMark[]
  createdAt: number
  updatedAt: number
}

export interface CalculationResult {
  mouthDiameter: number
  bellyDiameter: number
  bottomDiameter: number
  height: number
  volume: number | null
  isValid: boolean
  errors: string[]
}

export interface ValidationResult {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

export interface Culvert {
  id: number
  name: string
  code: string
  location: string | null
  length: number
  material: string | null
  construction_year: number | null
  status: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Section {
  id: number
  culvert_id: number
  station: number
  shape: string
  width: number
  height: number | null
  diameter: number | null
  area: number | null
  perimeter: number | null
  hydraulic_radius: number | null
  description: string | null
  created_at: string
}

export interface Slope {
  id: number
  section_id: number
  start_station: number
  end_station: number
  slope_value: number
  start_elevation: number | null
  end_elevation: number | null
  description: string | null
  created_at: string
}

export interface Manhole {
  id: number
  culvert_id: number
  name: string
  code: string
  station: number
  elevation: number | null
  depth: number | null
  diameter: number | null
  material: string | null
  condition: string
  has_inlet: boolean
  has_outlet: boolean
  description: string | null
  created_at: string
  updated_at: string
}

export interface SedimentRecord {
  id: number
  culvert_id: number
  record_date: string
  start_station: number
  end_station: number
  sediment_thickness: number
  sediment_volume: number | null
  sediment_type: string | null
  survey_method: string | null
  operator: string | null
  description: string | null
  created_at: string
}

export interface RainScenario {
  id: number
  name: string
  description: string | null
  return_period: number
  rainfall_duration: number
  total_rainfall: number
  rainfall_distribution: string | null
  is_default: boolean
  created_at: string
}

export interface DrainageCapacityResult {
  scenario_id: number
  scenario_name: string
  return_period: number
  total_rainfall: number
  design_flow: number
  actual_capacity: number
  overflow: number
  overflow_ratio: number
  is_sufficient: boolean
}

export interface SedimentTrendPoint {
  date: string
  avg_thickness: number
  accumulated_volume: number
}

export interface SedimentTrendResult {
  culvert_id: number
  culvert_name: string
  trend_points: SedimentTrendPoint[]
  avg_sediment_rate: number
  max_thickness: number
  predicted_thickness_6m: number
  predicted_thickness_12m: number
  risk_level: string
}

export interface RiskSection {
  start_station: number
  end_station: number
  risk_level: string
  risk_score: number
  description: string
  suggestion: string
}

export interface RiskWarningResult {
  culvert_id: number
  culvert_name: string
  total_risk_sections: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  risk_sections: RiskSection[]
}

export interface SimulationResult {
  plan_type: string
  original_capacity: number
  simulated_capacity: number
  capacity_improvement: number
  cost_estimate: number
  construction_period: string
  suggestion: string
}

export type PointSource = 'original' | 'restored'

export interface RestorationPoint extends ControlPoint {
  source: PointSource
  confidence: number
}

export interface RestorationScheme {
  id: string
  name: string
  originalPoints: ControlPoint[]
  restoredPoints: RestorationPoint[]
  method: string
  confidence: number
  mouthDiameter: { min: number; max: number; estimated: number }
  bellyDiameter: { min: number; max: number; estimated: number }
  bottomDiameter: { min: number; max: number; estimated: number }
  height: { min: number; max: number; estimated: number }
  volume: { min: number; max: number; estimated: number } | null
  unit: 'mm' | 'cm'
  createdAt: number
  specIntervalStart?: number
  specIntervalEnd?: number
}

export interface RestorationResult {
  schemes: RestorationScheme[]
  originalPoints: ControlPoint[]
  isValid: boolean
  errors: string[]
}

export interface ProfilePoint {
  station: number
  elevation: number
  section_width: number
  section_height: number | null
  sediment_thickness: number | null
  manhole_name: string | null
}

export interface ProfileResult {
  culvert_id: number
  culvert_name: string
  profile_points: ProfilePoint[]
  max_elevation: number
  min_elevation: number
  avg_slope: number
}

export interface ReportResult {
  report_id: string
  filename: string
  file_url: string
  created_at: string
}
