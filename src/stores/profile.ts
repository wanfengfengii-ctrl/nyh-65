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
        schemes.value = JSON.parse(saved)
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
      createNewScheme('默认罐型')
    }
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
    const copy: ProfileScheme = {
      id: generateId(),
      name: s.name + ' (副本)',
      unit: s.unit,
      controlPoints: s.controlPoints.map(p => ({ ...p, id: nextPointId.value++ })),
      repairMarks: s.repairMarks.map(r => ({ ...r })),
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
      p.y = Math.max(0, y)
      currentScheme.value.updatedAt = Date.now()
      saveToStorage()
    }
  }

  function selectPoint(id: number | null) {
    selectedPointId.value = id
  }

  function addPoint(x: number, y: number, insertIndex?: number) {
    if (!currentScheme.value) return
    const newP: ControlPoint = {
      id: nextPointId.value++,
      x: Math.max(0, x),
      y: Math.max(0, y),
    }
    const pts = currentScheme.value.controlPoints
    if (typeof insertIndex === 'number' && insertIndex >= 0 && insertIndex < pts.length) {
      pts.splice(insertIndex, 0, newP)
    } else {
      pts.push(newP)
    }
    pts.sort((a, b) => a.y - b.y)
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
        r => r.pointIndex !== idx
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

  function toggleRepairMark(pointIndex: number, description?: string) {
    if (!currentScheme.value) return
    const existing = currentScheme.value.repairMarks.find(r => r.pointIndex === pointIndex)
    if (existing) {
      currentScheme.value.repairMarks = currentScheme.value.repairMarks.filter(
        r => r.pointIndex !== pointIndex
      )
    } else {
      currentScheme.value.repairMarks.push({ pointIndex, description })
    }
    currentScheme.value.updatedAt = Date.now()
    saveToStorage()
  }

  function exportScheme(id: string): string {
    const s = schemes.value.find(s => s.id === id)
    if (!s) return ''
    return JSON.stringify(
      {
        name: s.name,
        unit: s.unit,
        exportTime: new Date().toISOString(),
        controlPoints: s.controlPoints.map((p, i) => ({
          index: i,
          x: p.x,
          y: p.y,
          isRepairMark: s.repairMarks.some(r => r.pointIndex === i),
        })),
        repairMarks: s.repairMarks,
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
