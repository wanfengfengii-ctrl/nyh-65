import type { ControlPoint, RestorationPoint, RestorationScheme, RestorationResult, SpecInterval } from '@/types'
import { sampleCurvePoints, generateId, validateProfile, calculateDimensions } from './geometry'

export function analyzeProfileGaps(points: ControlPoint[]): {
  hasBottomGap: boolean
  hasTopGap: boolean
  hasMiddleGap: boolean
  bottomY: number
  topY: number
  minY: number
  maxY: number
  avgSpacing: number
} {
  if (points.length < 2) {
    return {
      hasBottomGap: false,
      hasTopGap: false,
      hasMiddleGap: false,
      bottomY: 0,
      topY: 0,
      minY: 0,
      maxY: 0,
      avgSpacing: 0,
    }
  }

  const sorted = [...points].sort((a, b) => a.y - b.y)
  const minY = sorted[0].y
  const maxY = sorted[sorted.length - 1].y

  let totalSpacing = 0
  for (let i = 1; i < sorted.length; i++) {
    totalSpacing += sorted[i].y - sorted[i - 1].y
  }
  const avgSpacing = totalSpacing / (sorted.length - 1)

  const bottomPoint = sorted[0]
  const topPoint = sorted[sorted.length - 1]

  const hasBottomGap = bottomPoint.y > 5 || bottomPoint.x <= 0.001
  const hasTopGap = topPoint.x <= 0.001

  let hasMiddleGap = false
  for (let i = 1; i < sorted.length; i++) {
    const gap = sorted[i].y - sorted[i - 1].y
    if (gap > avgSpacing * 2.5) {
      hasMiddleGap = true
      break
    }
  }

  return {
    hasBottomGap,
    hasTopGap,
    hasMiddleGap,
    bottomY: bottomPoint.y,
    topY: topPoint.y,
    minY,
    maxY,
    avgSpacing,
  }
}

export function estimateMissingBottom(
  points: ControlPoint[],
  variant: 'conservative' | 'moderate' | 'bold' = 'moderate'
): { point: ControlPoint; confidence: number } {
  const sorted = [...points].sort((a, b) => a.y - b.y)
  const bottom2 = sorted.slice(0, Math.min(3, sorted.length))

  if (bottom2.length < 2) {
    return {
      point: { id: -1, x: 40, y: 0 },
      confidence: 0.5,
    }
  }

  const p1 = bottom2[bottom2.length - 2]
  const p2 = bottom2[bottom2.length - 1]

  const slope = (p2.x - p1.x) / (p2.y - p1.y || 1)

  const variantMultipliers = {
    conservative: 0.7,
    moderate: 1.0,
    bold: 1.3,
  }

  const mult = variantMultipliers[variant]
  const extrapY = 0
  const extrapX = Math.max(0, p2.x + slope * (extrapY - p2.y) * mult)

  const bottomX = Math.max(10, extrapX)

  let confidence = 0.7
  if (variant === 'conservative') confidence = 0.85
  if (variant === 'bold') confidence = 0.55
  if (bottom2.length >= 3) confidence += 0.1

  return {
    point: { id: -1, x: bottomX, y: 0 },
    confidence: Math.min(0.95, confidence),
  }
}

export function estimateMissingTop(
  points: ControlPoint[],
  variant: 'conservative' | 'moderate' | 'bold' = 'moderate'
): { point: ControlPoint; confidence: number } {
  const sorted = [...points].sort((a, b) => a.y - b.y)
  const top2 = sorted.slice(-Math.min(3, sorted.length))

  if (top2.length < 2) {
    const maxY = Math.max(...points.map(p => p.y))
    return {
      point: { id: -1, x: 50, y: maxY * 1.2 },
      confidence: 0.5,
    }
  }

  const p1 = top2[0]
  const p2 = top2[top2.length - 1]

  const slope = (p2.x - p1.x) / (p2.y - p1.y || 1)

  const variantMultipliers = {
    conservative: 0.8,
    moderate: 1.1,
    bold: 1.4,
  }

  const mult = variantMultipliers[variant]
  const heightExtension = (p2.y - p1.y) * mult
  const extrapY = p2.y + heightExtension
  const extrapX = Math.max(0, p2.x + slope * heightExtension)

  const mouthX = Math.max(20, extrapX)

  let confidence = 0.65
  if (variant === 'conservative') confidence = 0.8
  if (variant === 'bold') confidence = 0.5
  if (top2.length >= 3) confidence += 0.1

  return {
    point: { id: -1, x: mouthX, y: extrapY },
    confidence: Math.min(0.95, confidence),
  }
}

export function interpolateMiddlePoints(
  points: ControlPoint[],
  startIdx: number,
  endIdx: number,
  count: number = 2
): { points: ControlPoint[]; confidence: number } {
  const sorted = [...points].sort((a, b) => a.y - b.y)
  const p1 = sorted[startIdx]
  const p2 = sorted[endIdx]

  if (!p1 || !p2 || count <= 0) {
    return { points: [], confidence: 0 }
  }

  const result: ControlPoint[] = []
  const dy = (p2.y - p1.y) / (count + 1)
  const dx = (p2.x - p1.x) / (count + 1)

  for (let i = 1; i <= count; i++) {
    result.push({
      id: -1,
      x: p1.x + dx * i,
      y: p1.y + dy * i,
    })
  }

  const gapRatio = (p2.y - p1.y) / Math.max(p2.y - p1.y, 1)
  let confidence = 0.8 - gapRatio * 0.3
  confidence = Math.max(0.4, Math.min(0.9, confidence))

  return { points: result, confidence }
}

export function generateRestorationScheme(
  originalPoints: ControlPoint[],
  variant: 'conservative' | 'moderate' | 'bold',
  methodName: string,
  unit: 'mm' | 'cm',
  nextPointId: number
): { scheme: RestorationScheme; nextId: number } {
  const sorted = [...originalPoints].sort((a, b) => a.y - b.y)
  const analysis = analyzeProfileGaps(originalPoints)

  const restoredPoints: RestorationPoint[] = sorted.map(p => ({
    ...p,
    source: 'original',
    confidence: 1.0,
  }))

  let currentId = nextPointId
  let totalConfidence = 0
  let confidenceCount = 0

  if (analysis.hasBottomGap) {
    const bottomEstimate = estimateMissingBottom(originalPoints, variant)
    restoredPoints.unshift({
      ...bottomEstimate.point,
      id: currentId++,
      source: 'restored',
      confidence: bottomEstimate.confidence,
    })
    totalConfidence += bottomEstimate.confidence
    confidenceCount++
  }

  if (analysis.hasTopGap) {
    const topEstimate = estimateMissingTop(originalPoints, variant)
    restoredPoints.push({
      ...topEstimate.point,
      id: currentId++,
      source: 'restored',
      confidence: topEstimate.confidence,
    })
    totalConfidence += topEstimate.confidence
    confidenceCount++
  }

  if (analysis.hasMiddleGap) {
    const sortedRestored = [...restoredPoints].sort((a, b) => a.y - b.y)
    const newMiddlePoints: RestorationPoint[] = []

    for (let i = 0; i < sortedRestored.length - 1; i++) {
      const gap = sortedRestored[i + 1].y - sortedRestored[i].y
      if (gap > analysis.avgSpacing * 2) {
        const neededPoints = Math.min(3, Math.floor(gap / analysis.avgSpacing) - 1)
        const middleResult = interpolateMiddlePoints(
          sortedRestored,
          i,
          i + 1,
          neededPoints
        )
        for (const mp of middleResult.points) {
          newMiddlePoints.push({
            ...mp,
            id: currentId++,
            source: 'restored' as const,
            confidence: middleResult.confidence,
          })
        }
        totalConfidence += middleResult.confidence
        confidenceCount++
      }
    }

    restoredPoints.push(...newMiddlePoints)
  }

  restoredPoints.sort((a, b) => a.y - b.y)

  const avgConfidence = confidenceCount > 0
    ? totalConfidence / confidenceCount
    : 1.0

  const originalConfidence = 0.6
  const overallConfidence = (avgConfidence * confidenceCount + originalConfidence * sorted.length) / (confidenceCount + sorted.length)

  const validation = validateProfile(restoredPoints)
  const dims = calculateDimensions(restoredPoints, unit)

  const toleranceFactors = {
    conservative: 0.05,
    moderate: 0.1,
    bold: 0.15,
  }
  const tol = toleranceFactors[variant]

  const createRange = (value: number) => ({
    min: value * (1 - tol),
    max: value * (1 + tol),
    estimated: value,
  })

  const specIntervals: SpecInterval[] = []
  if (analysis.hasBottomGap) {
    const bottomRestoredY = restoredPoints.find(p => p.source === 'restored' && p.y <= analysis.bottomY)?.y ?? 0
    specIntervals.push({
      yStart: bottomRestoredY,
      yEnd: analysis.bottomY,
      label: '底部推测',
    })
  }
  if (analysis.hasTopGap) {
    const topOriginalY = analysis.topY
    const topRestoredY = restoredPoints[restoredPoints.length - 1]?.y ?? topOriginalY
    specIntervals.push({
      yStart: topOriginalY,
      yEnd: topRestoredY,
      label: '口沿推测',
    })
  }

  const scheme: RestorationScheme = {
    id: generateId(),
    name: `${methodName}方案`,
    originalPoints: sorted,
    restoredPoints,
    method: methodName,
    confidence: Math.max(0.3, Math.min(0.98, overallConfidence)),
    mouthDiameter: createRange(dims.mouthDiameter),
    bellyDiameter: createRange(dims.bellyDiameter),
    bottomDiameter: createRange(dims.bottomDiameter),
    height: createRange(dims.height),
    volume: dims.volume !== null ? createRange(dims.volume) : null,
    unit,
    createdAt: Date.now(),
    specIntervals,
  }

  return { scheme, nextId: currentId }
}

export function generateRestorationSchemes(
  originalPoints: ControlPoint[],
  unit: 'mm' | 'cm',
  nextPointId: number
): RestorationResult {
  const validation = validateProfile(originalPoints)
  if (!validation.isValid) {
    return {
      schemes: [],
      originalPoints,
      isValid: false,
      errors: validation.errors,
    }
  }

  if (originalPoints.length < 3) {
    return {
      schemes: [],
      originalPoints,
      isValid: false,
      errors: ['控制点数量不足，至少需要3个控制点才能进行复原'],
    }
  }

  const variants: Array<{ variant: 'conservative' | 'moderate' | 'bold'; name: string }> = [
    { variant: 'conservative', name: '保守' },
    { variant: 'moderate', name: '适中' },
    { variant: 'bold', name: '大胆' },
  ]

  const schemes: RestorationScheme[] = []
  let currentId = nextPointId

  for (const v of variants) {
    const result = generateRestorationScheme(
      originalPoints,
      v.variant,
      v.name,
      unit,
      currentId
    )
    schemes.push(result.scheme)
    currentId = result.nextId
  }

  return {
    schemes,
    originalPoints,
    isValid: true,
    errors: [],
  }
}

export function updateRestorationPoint(
  scheme: RestorationScheme,
  pointId: number,
  x: number,
  y: number
): RestorationScheme {
  const newPoints = scheme.restoredPoints.map(p => {
    if (p.id === pointId) {
      return {
        ...p,
        x: Math.max(0, x),
        y: Math.max(0, y),
        confidence: p.source === 'restored' ? Math.max(0.3, p.confidence - 0.05) : p.confidence,
      }
    }
    return p
  })

  newPoints.sort((a, b) => a.y - b.y)

  const validation = validateProfile(newPoints)
  const dims = calculateDimensions(newPoints, scheme.unit)

  const tol = 0.1
  const createRange = (value: number) => ({
    min: value * (1 - tol),
    max: value * (1 + tol),
    estimated: value,
  })

  return {
    ...scheme,
    restoredPoints: newPoints,
    mouthDiameter: createRange(dims.mouthDiameter),
    bellyDiameter: createRange(dims.bellyDiameter),
    bottomDiameter: createRange(dims.bottomDiameter),
    height: createRange(dims.height),
    volume: dims.volume !== null ? createRange(dims.volume) : null,
    confidence: Math.max(0.3, scheme.confidence - 0.02),
    createdAt: Date.now(),
  }
}

export function exportRestorationData(
  originalScheme: { name: string; unit: 'mm' | 'cm' },
  restorationSchemes: RestorationScheme[]
): string {
  const data = {
    exportTime: new Date().toISOString(),
    originalProfile: {
      name: originalScheme.name,
      unit: originalScheme.unit,
    },
    restorationSchemes: restorationSchemes.map(s => ({
      id: s.id,
      name: s.name,
      method: s.method,
      confidence: s.confidence,
      unit: s.unit,
      specIntervals: s.specIntervals,
      dimensions: {
        mouthDiameter: s.mouthDiameter,
        bellyDiameter: s.bellyDiameter,
        bottomDiameter: s.bottomDiameter,
        height: s.height,
        volume: s.volume,
      },
      originalPoints: s.originalPoints.map((p, i) => ({
        index: i,
        x: Number(p.x.toFixed(3)),
        y: Number(p.y.toFixed(3)),
      })),
      restoredPoints: s.restoredPoints.map((p, i) => ({
        index: i,
        x: Number(p.x.toFixed(3)),
        y: Number(p.y.toFixed(3)),
        source: p.source,
        confidence: p.confidence,
      })),
    })),
  }

  return JSON.stringify(data, null, 2)
}
