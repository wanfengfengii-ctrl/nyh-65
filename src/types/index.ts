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

export interface SpecInterval {
  yStart: number
  yEnd: number
  label: string
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
  specIntervals: SpecInterval[]
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

export interface ControlPoint {
  id: number
  x: number
  y: number
}

export interface RepairMark {
  pointId: number
  description?: string
}

export interface KeyPart {
  name: string
  startPointIndex: number
  endPointIndex: number
  startY: number
  endY: number
  description?: string
  confidence?: number
  diameter?: number
  zone?: string
}

export interface Dimensions {
  height?: number
  mouthDiameter?: number
  bellyDiameter?: number
  bottomDiameter?: number
  volume?: number
  neckDiameter?: number
  shoulderDiameter?: number
  footDiameter?: number
  isValid?: boolean
  errors?: string[]
}

export interface CeramicVesselTemplate {
  id: number
  name: string
  code: string
  category: string
  dynasty?: string
  region?: string
  material?: string
  typical_height?: number
  typical_mouth_diameter?: number
  typical_belly_diameter?: number
  typical_bottom_diameter?: number
  typical_volume?: number
  control_points: ControlPoint[]
  key_parts?: KeyPart[]
  parameters?: Record<string, any>
  description?: string
  references?: string
  image_url?: string
  is_public?: boolean
  created_by?: string
  created_at: string
  updated_at: string
}

export interface VesselProfile {
  id: number
  name: string
  code: string
  template_id?: number
  unit: string
  vessel_type?: string
  dynasty?: string
  provenance?: string
  origin_site?: string
  material?: string
  condition_status: string
  condition_detail?: string
  museum_no?: string
  profile_data?: Record<string, any>
  control_points: ControlPoint[]
  repair_marks?: RepairMark[]
  key_parts_identified?: KeyPart[]
  dimensions?: Dimensions
  parameters?: Record<string, any>
  is_restored: boolean
  restoration_method?: string
  restoration_confidence?: number
  description?: string
  tags?: string[]
  version_count?: number
  created_by?: string
  created_at: string
  updated_at: string
  template?: CeramicVesselTemplate
}

export interface VesselVersion {
  id: number
  profile_id?: number
  template_id?: number
  version_number: number
  version_label?: string
  change_summary?: string
  control_points?: ControlPoint[]
  repair_marks?: RepairMark[]
  dimensions?: Dimensions
  key_parts_identified?: KeyPart[]
  parameters?: Record<string, any>
  restoration_confidence?: number
  parent_version_id?: number
  created_by?: string
  created_at: string
}

export interface HeatmapPoint {
  y: number
  yRatio?: number
  xA?: number
  xB?: number
  radiusDifference?: number
  difference: number
  diameter_diff?: number
  normalized: number
  normalized_height?: number
  zone: string
}

export interface KeyDifference {
  zone: string
  y_start: number
  y_end: number
  avg_diff: number
  max_diff: number
  significance: string
  relative_intensity?: number
  section_name?: string
  height_start?: number
  height_end?: number
  avg_difference?: number
  severity?: 'low' | 'medium' | 'high' | string
  description?: string
}

export interface DifferenceAnalysis {
  id: number
  name: string
  profile_a_id?: number
  profile_b_id?: number
  template_id?: number
  analysis_type: string
  heatmap_data?: HeatmapPoint[]
  key_differences?: KeyDifference[]
  overall_similarity?: number
  dimension_differences?: Record<string, any>
  description?: string
  created_by?: string
  created_at: string
}

export interface RestorationAssessment {
  id: number
  profile_id: number
  overall_confidence: number
  bottom_confidence?: number
  mouth_confidence?: number
  belly_confidence?: number
  neck_confidence?: number
  shoulder_confidence?: number
  foot_confidence?: number
  part_confs_bottom?: number
  part_confs_mouth?: number
  part_confs_belly?: number
  part_confs_neck?: number
  part_confs_shoulder?: number
  part_confs_foot?: number
  fragment_coverage?: number
  gap_count?: number
  critical_gaps?: any[]
  supporting_evidence?: any[]
  risk_factors?: any[]
  recommendations?: string[]
  assessment_method?: string
  assessed_by?: string
  created_at: string
}

export interface ResearchReport {
  id: number
  profile_id: number
  title: string
  report_type: string
  content: Record<string, any>
  sections?: any[]
  summary?: string
  conclusions?: string[]
  file_path?: string
  file_format: string
  report_code?: string
  custom_title?: string
  section_count?: number
  author?: string
  keywords?: string[]
  created_at: string
  updated_at: string
}

export interface ConfidenceLevelInfo {
  overall: number
  level: string
  part_confidences: {
    bottom?: number
    mouth?: number
    belly?: number
    neck?: number
    shoulder?: number
    foot?: number
  }
  fragment_coverage: number
  gap_count: number
  critical_gaps: any[]
  supporting_evidence: any[]
  risk_factors: any[]
  recommendations: string[]
}

export interface ParametricEditResult {
  success: boolean
  control_points: ControlPoint[]
  old_dimensions?: Dimensions
  new_dimensions?: Dimensions
  dimension_type?: string
  target_value?: number
  dimensions?: Dimensions
  scale_applied?: number
  message?: string
  error?: string
}

export interface TemplateApplyResult {
  success: boolean
  template_id: number
  template_name: string
  template_code: string
  category: string
  control_points: ControlPoint[]
  scale_factor: number
  original_dimensions?: Dimensions
  new_dimensions?: Dimensions
  error?: string
}

export interface DifferenceAnalysisResult {
  success: boolean
  heatmap_data: HeatmapPoint[]
  key_differences: KeyDifference[]
  overall_similarity: number
  dimension_differences: Record<string, any>
  y_range?: { min: number; max: number }
  profile_a_dimensions?: Dimensions
  profile_b_dimensions?: Dimensions
  profile_a_name?: string
  profile_b_name?: string
  profile_a_sample?: ControlPoint[]
  profile_b_sample?: ControlPoint[]
  statistics?: {
    mean_diameter_diff?: number
    max_diameter_diff?: number
    min_diameter_diff?: number
    height_diff_pct?: number
    width_diff_pct?: number
  }
  error?: string
}

export interface ReportGenerationResult {
  report_id: number
  report_code?: string
  title: string
  report_type?: string
  filename: string
  created_at: string
  summary: string
  conclusions: string[]
  sections_count: number
  section_count?: number
}
