export interface ControlPoint {
  id: number
  x: number
  y: number
}

export interface RepairMark {
  pointIndex: number
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
