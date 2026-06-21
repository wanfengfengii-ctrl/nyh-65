import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ControlPoint, ProfileScheme, RepairMark, Unit, RestorationScheme, RestorationResult } from '@/types'
import { generateDefaultPoints, generateId } from '@/utils/geometry'
import { generateRestorationSchemes, updateRestorationPoint, exportRestorationData } from '@/utils/restoration'

const STORAGE_KEY = 'ceramic_profile_schemes'
const CURRENT_KEY = 'ceramic_profile_current'

export const useProfileStore = defineStore('profile', () => {
  const schemes = ref<ProfileScheme[]>([])
  const currentSchemeId = ref<string | null>(null)
  const selectedPointId = ref<number | null>(null)
  const nextPointId = ref<number>(100)

  const restorationSchemes = ref<RestorationScheme[]>([])
  const currentRestorationId = ref<string | null>(null)
  const restorationResult = ref<RestorationResult | null>(null)

  const currentScheme = computed<ProfileScheme | null>(() => {
    if (!currentSchemeId.value) return null
    return schemes.value.find(s => s.id === currentSchemeId.value) || null
  })

  const controlPoints = computed<ControlPoint[]>(() => {
    return currentScheme.value?.controlPoints || []
  })

  const repairMarks = computed<RepairMark[]>(() => {
    return currentScheme.value?.repairMarks || []
  })

  const unit = computed<Unit>(() => {
    return currentScheme.value?.unit || 'mm'
  })

  const currentRestoration = computed<RestorationScheme | null>(() => {
    if (!currentRestorationId.value) return null
    return restorationSchemes.value.find(s => s.id === currentRestorationId.value) || null
  })

  const hasRestoration = computed(() => restorationSchemes.value.length > 0)

  function loadFromStorage() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const raw = JSON.parse(saved)
        schemes.value = migrateSchemes(raw)
      }
      const savedCurrent = localStorage.getItem(CURRENT_KEY)
      if (savedCurrent && schemes.value.find(s => s.id === savedCurrent)) {
        currentSchemeId.value = savedCurrent
      }
      if (schemes.value.length === 0) {
        createNewScheme('默认罐型')
      } else if (!currentSchemeId.value) {
        currentSchemeId.value = schemes.value[0].id
      }
      syncMaxPointId()
    } catch (e) {
      console.error('加载数据失败', e)
      createNewScheme('默认罐型')
    }
  }

  function migrateSchemes(rawSchemes: any[]): ProfileScheme[] {
    rawSchemes.forEach(s => {
      if (!s.controlPoints || !Array.isArray(s.controlPoints)) {
        s.controlPoints = []
        s.repairMarks = []
        return
      }

      if (s.repairMarks && Array.isArray(s.repairMarks)) {
        s.repairMarks = s.repairMarks
          .map((r: any) => {
            if (r.pointId !== undefined && r.pointId !== null) {
              return r
            }
            if (r.pointIndex !== undefined && r.pointIndex !== null) {
              const point = s.controlPoints[r.pointIndex]
              if (point && point.id !== undefined) {
                return { pointId: point.id, description: r.description }
              }
            }
            return null
          })
          .filter(Boolean)
      } else {
        s.repairMarks = []
      }

      s.controlPoints.sort((a: any, b: any) => {
        return a.y - b.y
      })
    })
    return rawSchemes as ProfileScheme[]
  }

  function syncMaxPointId() {
    let max = 0
    for (const s of schemes.value) {
      for (const p of s.controlPoints) {
        if (p.id > max) max = p.id
      }
    }
    nextPointId.value = max + 1
  }

  function saveToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(schemes.value))
      if (currentSchemeId.value) {
        localStorage.setItem(CURRENT_KEY, currentSchemeId.value)
      }
    } catch (e) {
      console.error('保存失败', e)
    }
  }

  function createNewScheme(name: string = '新方案') {
    const now = Date.now()
    const scheme: ProfileScheme = {
      id: generateId(),
      name,
      unit: 'mm',
      controlPoints: generateDefaultPoints().map(p => ({ ...p, id: nextPointId.value++ })),
      repairMarks: [],
      createdAt: now,
      updatedAt: now,
    }
    schemes.value.push(scheme)
    currentSchemeId.value = scheme.id
    saveToStorage()
    return scheme
  }

  function selectScheme(id: string) {
    if (schemes.value.find(s => s.id === id)) {
      currentSchemeId.value = id
      selectedPointId.value = null
      saveToStorage()
    }
  }

  function deleteScheme(id: string) {
    const idx = schemes.value.findIndex(s => s.id === id)
    if (idx < 0) return
    schemes.value.splice(idx, 1)
    if (currentSchemeId.value === id) {
      currentSchemeId.value = schemes.value.length > 0 ? schemes.value[0].id : null
      if (!currentSchemeId.value) {
        createNewScheme('新方案')
      }
    }
    saveToStorage()
  }

  function renameScheme(id: string, name: string) {
    const s = schemes.value.find(s => s.id === id)
    if (s) {
      s.name = name
      s.updatedAt = Date.now()
      saveToStorage()
    }
  }

  function duplicateScheme(id: string) {
    const s = schemes.value.find(s => s.id === id)
    if (!s) return
    const now = Date.now()
    const idMap = new Map<number, number>()
    const newPoints = s.controlPoints.map(p => {
      const newId = nextPointId.value++
      idMap.set(p.id, newId)
      return { ...p, id: newId }
    })
    const newRepairMarks = s.repairMarks
      .filter(r => idMap.has(r.pointId))
      .map(r => ({ ...r, pointId: idMap.get(r.pointId)! }))
    const copy: ProfileScheme = {
      id: generateId(),
      name: s.name + ' (副本)',
      unit: s.unit,
      controlPoints: newPoints,
      repairMarks: newRepairMarks,
      createdAt: now,
      updatedAt: now,
    }
    schemes.value.push(copy)
    currentSchemeId.value = copy.id
    saveToStorage()
  }

  function setUnit(u: Unit) {
    if (currentScheme.value) {
      currentScheme.value.unit = u
      currentScheme.value.updatedAt = Date.now()
      saveToStorage()
    }
  }

  function updatePoint(id: number, x: number, y: number) {
    if (!currentScheme.value) return
    const p = currentScheme.value.controlPoints.find(p => p.id === id)
    if (p) {
      const oldX = p.x
      const oldY = p.y
      p.x = Math.max(0, x)
      p.y = Math.max(0, y)
      if (Math.abs(oldY - p.y) > 0.001 || Math.abs(oldX - p.x) > 0.001) {
        currentScheme.value.controlPoints.sort((a, b) => a.y - b.y)
        currentScheme.value.updatedAt = Date.now()
        saveToStorage()
      }
    }
  }

  function selectPoint(id: number | null) {
    selectedPointId.value = id
  }

  function addPoint(x: number, y: number) {
    if (!currentScheme.value) return
    const newP: ControlPoint = {
      id: nextPointId.value++,
      x: Math.max(0, x),
      y: Math.max(0, y),
    }
    const pts = currentScheme.value.controlPoints

    let lo = 0
    let hi = pts.length
    while (lo < hi) {
      const mid = (lo + hi) >> 1
      if (pts[mid].y < newP.y) {
        lo = mid + 1
      } else {
        hi = mid
      }
    }
    pts.splice(lo, 0, newP)

    currentScheme.value.updatedAt = Date.now()
    saveToStorage()
    return newP.id
  }

  function deletePoint(id: number) {
    if (!currentScheme.value) return
    if (currentScheme.value.controlPoints.length <= 3) return
    const idx = currentScheme.value.controlPoints.findIndex(p => p.id === id)
    if (idx >= 0) {
      currentScheme.value.controlPoints.splice(idx, 1)
      currentScheme.value.repairMarks = currentScheme.value.repairMarks.filter(
        r => r.pointId !== id
      )
      if (selectedPointId.value === id) {
        selectedPointId.value = null
      }
      currentScheme.value.updatedAt = Date.now()
      saveToStorage()
    }
  }

  function resetPoints() {
    if (!currentScheme.value) return
    currentScheme.value.controlPoints = generateDefaultPoints().map(p => ({
      ...p,
      id: nextPointId.value++,
    }))
    currentScheme.value.repairMarks = []
    selectedPointId.value = null
    currentScheme.value.updatedAt = Date.now()
    saveToStorage()
  }

  function toggleRepairMark(pointId: number, description?: string) {
    if (!currentScheme.value) return
    const existing = currentScheme.value.repairMarks.find(r => r.pointId === pointId)
    if (existing) {
      currentScheme.value.repairMarks = currentScheme.value.repairMarks.filter(
        r => r.pointId !== pointId
      )
    } else {
      currentScheme.value.repairMarks.push({ pointId, description })
    }
    currentScheme.value.updatedAt = Date.now()
    saveToStorage()
  }

  function exportScheme(id: string): string {
    const s = schemes.value.find(s => s.id === id)
    if (!s) return ''
    const sortedPoints = [...s.controlPoints].sort((a, b) => a.y - b.y)
    const repairMarkPointIds = new Set(s.repairMarks.map(r => r.pointId))
    const repairMarkMap = new Map(s.repairMarks.map(r => [r.pointId, r]))
    return JSON.stringify(
      {
        name: s.name,
        unit: s.unit,
        exportTime: new Date().toISOString(),
        totalPoints: sortedPoints.length,
        totalRepairMarks: s.repairMarks.length,
        controlPoints: sortedPoints.map((p, i) => {
          const mark = repairMarkMap.get(p.id)
          return {
            index: i,
            position: i === 0 ? '底部' : i === sortedPoints.length - 1 ? '口沿' : '中间',
            id: p.id,
            x: Number(p.x.toFixed(3)),
            y: Number(p.y.toFixed(3)),
            radius: Number(p.x.toFixed(3)),
            height: Number(p.y.toFixed(3)),
            isRepairMark: repairMarkPointIds.has(p.id),
            repairDescription: mark?.description || null,
          }
        }),
        repairMarks: s.repairMarks.map(r => {
          const pointIdx = sortedPoints.findIndex(p => p.id === r.pointId)
          const point = sortedPoints[pointIdx]
          return {
            pointIndex: pointIdx,
            pointNumber: pointIdx >= 0 ? pointIdx + 1 : null,
            pointId: r.pointId,
            pointX: point ? point.x : null,
            pointY: point ? point.y : null,
            description: r.description,
          }
        }),
        orderNote: '控制点按高度从低到高排序（底部→口沿），为剖面曲线标准顺序。index从0开始，pointNumber从1开始。',
      },
      null,
      2
    )
  }

  function generateRestorations(): RestorationResult {
    if (!currentScheme.value) {
      return {
        schemes: [],
        originalPoints: [],
        isValid: false,
        errors: ['请先选择或创建一个剖面方案'],
      }
    }

    const result = generateRestorationSchemes(
      currentScheme.value.controlPoints,
      currentScheme.value.unit,
      nextPointId.value
    )

    restorationResult.value = result
    restorationSchemes.value = result.schemes
    currentRestorationId.value = result.schemes.length > 0 ? result.schemes[0].id : null

    let maxId = nextPointId.value
    for (const s of result.schemes) {
      for (const p of s.restoredPoints) {
        if (p.id > maxId) maxId = p.id
      }
    }
    nextPointId.value = maxId + 1

    return result
  }

  function selectRestoration(id: string | null) {
    if (id === null || restorationSchemes.value.find(s => s.id === id)) {
      currentRestorationId.value = id
    }
  }

  function updateRestorationPointPos(pointId: number, x: number, y: number) {
    if (!currentRestoration.value) return

    const updated = updateRestorationPoint(currentRestoration.value, pointId, x, y)
    const idx = restorationSchemes.value.findIndex(s => s.id === updated.id)
    if (idx >= 0) {
      restorationSchemes.value[idx] = updated
    }
  }

  function clearRestorations() {
    restorationSchemes.value = []
    currentRestorationId.value = null
    restorationResult.value = null
  }

  function setRestorationConfidence(schemeId: string, confidence: number) {
    const scheme = restorationSchemes.value.find(s => s.id === schemeId)
    if (scheme) {
      scheme.confidence = Math.max(0, Math.min(1, confidence))
    }
  }

  function exportRestoration(): string {
    if (!currentScheme.value) return ''
    return exportRestorationData(
      { name: currentScheme.value.name, unit: currentScheme.value.unit },
      restorationSchemes.value
    )
  }

  function deleteRestoration(id: string) {
    const idx = restorationSchemes.value.findIndex(s => s.id === id)
    if (idx >= 0) {
      restorationSchemes.value.splice(idx, 1)
      if (currentRestorationId.value === id) {
        currentRestorationId.value = restorationSchemes.value.length > 0 ? restorationSchemes.value[0].id : null
      }
    }
  }

  return {
    schemes,
    currentSchemeId,
    selectedPointId,
    currentScheme,
    controlPoints,
    repairMarks,
    unit,
    restorationSchemes,
    currentRestorationId,
    currentRestoration,
    restorationResult,
    hasRestoration,
    loadFromStorage,
    saveToStorage,
    createNewScheme,
    selectScheme,
    deleteScheme,
    renameScheme,
    duplicateScheme,
    setUnit,
    updatePoint,
    selectPoint,
    addPoint,
    deletePoint,
    resetPoints,
    toggleRepairMark,
    exportScheme,
    generateRestorations,
    selectRestoration,
    updateRestorationPointPos,
    clearRestorations,
    setRestorationConfidence,
    exportRestoration,
    deleteRestoration,
  }
})
