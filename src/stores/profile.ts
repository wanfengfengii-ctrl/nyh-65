import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ControlPoint, ProfileScheme, RepairMark, Unit } from '@/types'
import { generateDefaultPoints, generateId } from '@/utils/geometry'

const STORAGE_KEY = 'ceramic_profile_schemes'
const CURRENT_KEY = 'ceramic_profile_current'

export const useProfileStore = defineStore('profile', () => {
  const schemes = ref<ProfileScheme[]>([])
  const currentSchemeId = ref<string | null>(null)
  const selectedPointId = ref<number | null>(null)
  const nextPointId = ref<number>(100)

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
      if (!s.controlPoints || !Array.isArray(s.controlPoints)) return
      s.controlPoints.sort((a: any, b: any) => a.y - b.y)
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
      p.x = Math.max(0, x)
      const oldY = p.y
      p.y = Math.max(0, y)
      if (Math.abs(oldY - p.y) > 0.1) {
        currentScheme.value.controlPoints.sort((a, b) => a.y - b.y)
      }
      currentScheme.value.updatedAt = Date.now()
      saveToStorage()
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
    return JSON.stringify(
      {
        name: s.name,
        unit: s.unit,
        exportTime: new Date().toISOString(),
        controlPoints: sortedPoints.map((p, i) => ({
          index: i,
          id: p.id,
          x: p.x,
          y: p.y,
          isRepairMark: repairMarkPointIds.has(p.id),
        })),
        repairMarks: s.repairMarks.map(r => {
          const pointIdx = sortedPoints.findIndex(p => p.id === r.pointId)
          return {
            pointIndex: pointIdx,
            pointId: r.pointId,
            description: r.description,
          }
        }),
        orderNote: '控制点按高度从低到高排序（底部到口沿），为剖面曲线标准顺序',
      },
      null,
      2
    )
  }

  return {
    schemes,
    currentSchemeId,
    selectedPointId,
    currentScheme,
    controlPoints,
    repairMarks,
    unit,
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
  }
})
