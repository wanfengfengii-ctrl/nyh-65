import type { ControlPoint, ValidationResult, CalculationResult } from '@/types'

export function catmullRomToBezier(
  p0: ControlPoint,
  p1: ControlPoint,
  p2: ControlPoint,
  p3: ControlPoint
) {
  const cp1x = p1.x + (p2.x - p0.x) / 6
  const cp1y = p1.y + (p2.y - p0.y) / 6
  const cp2x = p2.x - (p3.x - p1.x) / 6
  const cp2y = p2.y - (p3.y - p1.y) / 6
  return { cp1x, cp1y, cp2x, cp2y }
}

export function sampleCurvePoints(
  points: ControlPoint[],
  samplesPerSegment: number = 20
): { x: number; y: number }[] {
  if (points.length < 2) return []
  const result: { x: number; y: number }[] = []
  const extended = [points[0], ...points, points[points.length - 1]]

  for (let i = 0; i < extended.length - 3; i++) {
    const p0 = extended[i]
    const p1 = extended[i + 1]
    const p2 = extended[i + 2]
    const p3 = extended[i + 3]
    const { cp1x, cp1y, cp2x, cp2y } = catmullRomToBezier(p0, p1, p2, p3)

    for (let s = 0; s <= samplesPerSegment; s++) {
      const t = s / samplesPerSegment
      const mt = 1 - t
      const mt2 = mt * mt
      const mt3 = mt2 * mt
      const t2 = t * t
      const t3 = t2 * t

      const x = mt3 * p1.x + 3 * mt2 * t * cp1x + 3 * mt * t2 * cp2x + t3 * p2.x
      const y = mt3 * p1.y + 3 * mt2 * t * cp1y + 3 * mt * t2 * cp2y + t3 * p2.y
      result.push({ x, y })
    }
  }
  return result
}

function segmentsIntersect(
  a1: { x: number; y: number },
  a2: { x: number; y: number },
  b1: { x: number; y: number },
  b2: { x: number; y: number }
): boolean {
  const ccw = (A: { x: number; y: number }, B: { x: number; y: number }, C: { x: number; y: number }) => {
    return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)
  }
  return (
    ccw(a1, b1, b2) !== ccw(a2, b1, b2) && ccw(a1, a2, b1) !== ccw(a1, a2, b2)
  )
}

export function checkSelfIntersection(sampled: { x: number; y: number }[]): boolean {
  if (sampled.length < 4) return false
  for (let i = 0; i < sampled.length - 2; i++) {
    for (let j = i + 2; j < sampled.length - 1; j++) {
      if (i === 0 && j === sampled.length - 2) continue
      if (segmentsIntersect(sampled[i], sampled[i + 1], sampled[j], sampled[j + 1])) {
        return true
      }
    }
  }
  return false
}

export function isBottomClosed(points: ControlPoint[]): boolean {
  if (points.length < 2) return false
  return points[0].x > 0 && points[points.length - 1].x > 0
}

export function validateProfile(points: ControlPoint[]): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  if (points.length < 3) {
    errors.push(`控制点数量为 ${points.length}，不能少于 3 个`)
  }

  for (let i = 0; i < points.length; i++) {
    const p = points[i]
    if (p.x < 0) {
      errors.push(`控制点 ${i + 1}: 半径（x）不能为负数 (${p.x.toFixed(1)})`)
    }
    if (p.y < 0) {
      errors.push(`控制点 ${i + 1}: 高度（y）不能为负数 (${p.y.toFixed(1)})`)
    }
  }

  if (errors.length === 0 && points.length >= 2) {
    const sampled = sampleCurvePoints(points, 15)
    if (checkSelfIntersection(sampled)) {
      errors.push('剖面曲线存在自交，请调整控制点位置')
    }
  }

  if (errors.length === 0 && !isBottomClosed(points)) {
    warnings.push('底部未闭合，容量估算暂不可用（需底径>0且口径>0）')
  }

  return { isValid: errors.length === 0, errors, warnings }
}

export function calculateDimensions(
  points: ControlPoint[],
  unit: 'mm' | 'cm'
): CalculationResult {
  const validation = validateProfile(points)
  const unitFactor = unit === 'cm' ? 10 : 1

  if (!validation.isValid || points.length < 2) {
    return {
      mouthDiameter: 0,
      bellyDiameter: 0,
      bottomDiameter: 0,
      height: 0,
      volume: null,
      isValid: false,
      errors: validation.errors,
    }
  }

  const sampled = sampleCurvePoints(points, 50)
  if (sampled.length === 0) {
    return {
      mouthDiameter: 0,
      bellyDiameter: 0,
      bottomDiameter: 0,
      height: 0,
      volume: null,
      isValid: false,
      errors: ['无法生成采样曲线'],
    }
  }

  const ys = sampled.map(p => p.y)
  const xs = sampled.map(p => p.x)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const height = (maxY - minY) / unitFactor
  const maxX = Math.max(...xs)
  const bellyDiameter = (2 * maxX) / unitFactor

  const topPoint = sampled.reduce((best, p) => (p.y > best.y ? p : best), sampled[0])
  const bottomPoint = sampled.reduce((best, p) => (p.y < best.y ? p : best), sampled[0])

  const mouthDiameter = (2 * topPoint.x) / unitFactor
  const bottomDiameter = (2 * bottomPoint.x) / unitFactor

  let volume: number | null = null
  if (isBottomClosed(points)) {
    const sorted = [...sampled].sort((a, b) => a.y - b.y)
    let integral = 0
    for (let i = 1; i < sorted.length; i++) {
      const dy = sorted[i].y - sorted[i - 1].y
      const r1 = sorted[i - 1].x
      const r2 = sorted[i].x
      const avgR2 = (r1 * r1 + r2 * r2) / 2
      integral += Math.PI * avgR2 * dy
    }
    const volumeMm3 = integral
    const volumeMl = volumeMm3 / 1000
    volume = unit === 'cm' ? volumeMl : volumeMl
  }

  return {
    mouthDiameter,
    bellyDiameter,
    bottomDiameter,
    height,
    volume,
    isValid: true,
    errors: [],
  }
}

export function generateDefaultPoints(): ControlPoint[] {
  return [
    { id: 1, x: 40, y: 0 },
    { id: 2, x: 70, y: 50 },
    { id: 3, x: 85, y: 110 },
    { id: 4, x: 75, y: 170 },
    { id: 5, x: 55, y: 220 },
  ]
}

export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 9)
}
