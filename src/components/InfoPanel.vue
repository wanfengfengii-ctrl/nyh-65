<script setup lang="ts">
import { computed } from 'vue'
import { Ruler, CircleDot, FlaskConical, AlertTriangle, CheckCircle2, XCircle } from 'lucide-vue-next'
import { useProfileStore } from '@/stores/profile'
import { calculateDimensions, validateProfile, isBottomClosed } from '@/utils/geometry'

const store = useProfileStore()

const validation = computed(() => validateProfile(store.controlPoints))
const result = computed(() => calculateDimensions(store.controlPoints, store.unit))

const repairMarksDisplay = computed(() => {
  const sortedPoints = [...store.controlPoints].sort((a, b) => a.y - b.y)
  return store.repairMarks
    .map(m => {
      const idx = sortedPoints.findIndex(p => p.id === m.pointId)
      return {
        ...m,
        pointIndex: idx,
        pointNumber: idx >= 0 ? idx + 1 : null,
      }
    })
    .filter(m => m.pointNumber !== null)
    .sort((a, b) => (a.pointIndex ?? 0) - (b.pointIndex ?? 0))
})

const canCalculateVolume = computed(() => {
  const bottom = store.controlPoints.length > 0
    ? store.controlPoints.reduce((best, p) => (p.y < best.y ? p : best), store.controlPoints[0])
    : null
  return bottom ? bottom.x > 0 : false
})

const volumeBlockReason = computed(() => {
  if (store.controlPoints.length < 2) return null
  const bottom = store.controlPoints.reduce((best, p) => (p.y < best.y ? p : best), store.controlPoints[0])
  const mouth = store.controlPoints.reduce((best, p) => (p.y > best.y ? p : best), store.controlPoints[0])
  const bottomR = bottom ? bottom.x : 0
  const mouthR = mouth ? mouth.x : 0
  if (bottomR === 0 && mouthR === 0) return '底径和口径均为0，请检查控制点位置'
  if (bottomR === 0) return '底部未闭合（底径为0），暂无法计算容量'
  return null
})

function formatNumber(v: number | null, digits: number = 1): string {
  if (v === null || v === undefined || isNaN(v)) return '--'
  return v.toFixed(digits)
}

function exportJson() {
  if (!store.currentScheme) return
  const data = store.exportScheme(store.currentScheme.id)
  const blob = new Blob([data], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${store.currentScheme.name}_剖面数据_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

defineExpose({ exportJson })
</script>

<template>
  <div class="w-full h-full flex flex-col gap-3 p-4 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9] overflow-y-auto">
    <div class="flex items-center justify-between pb-2 border-b border-[#E8DFC9]">
      <h3 class="text-base font-bold text-[#5D4E2B] flex items-center gap-2">
        <Ruler class="w-4 h-4 text-[#8B6914]" />
        尺寸与容量
      </h3>
      <div class="flex items-center gap-1 text-xs">
        <button
          :class="[
            'px-2 py-0.5 rounded border transition-all',
            store.unit === 'mm' ? 'bg-[#5D8A66] text-white border-[#5D8A66]' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
          ]"
          @click="store.setUnit('mm')"
        >mm</button>
        <button
          :class="[
            'px-2 py-0.5 rounded border transition-all',
            store.unit === 'cm' ? 'bg-[#5D8A66] text-white border-[#5D8A66]' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
          ]"
          @click="store.setUnit('cm')"
        >cm</button>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-2">
      <div class="p-3 bg-white rounded-lg border border-[#E8DFC9]">
        <div class="text-[11px] text-gray-500 mb-1 flex items-center gap-1">
          <CircleDot class="w-3 h-3" />口径
        </div>
        <div class="text-lg font-bold text-[#5D4E2B]">
          {{ formatNumber(result.mouthDiameter) }}
          <span class="text-xs font-normal text-gray-500">{{ store.unit }}</span>
        </div>
      </div>
      <div class="p-3 bg-white rounded-lg border border-[#E8DFC9]">
        <div class="text-[11px] text-gray-500 mb-1 flex items-center gap-1">
          <CircleDot class="w-3 h-3" />腹径
        </div>
        <div class="text-lg font-bold text-[#5D4E2B]">
          {{ formatNumber(result.bellyDiameter) }}
          <span class="text-xs font-normal text-gray-500">{{ store.unit }}</span>
        </div>
      </div>
      <div class="p-3 bg-white rounded-lg border border-[#E8DFC9]">
        <div class="text-[11px] text-gray-500 mb-1 flex items-center gap-1">
          <CircleDot class="w-3 h-3" />底径
        </div>
        <div class="text-lg font-bold text-[#5D4E2B]">
          {{ formatNumber(result.bottomDiameter) }}
          <span class="text-xs font-normal text-gray-500">{{ store.unit }}</span>
        </div>
      </div>
      <div class="p-3 bg-white rounded-lg border border-[#E8DFC9]">
        <div class="text-[11px] text-gray-500 mb-1 flex items-center gap-1">
          <Ruler class="w-3 h-3" />高度
        </div>
        <div class="text-lg font-bold text-[#5D4E2B]">
          {{ formatNumber(result.height) }}
          <span class="text-xs font-normal text-gray-500">{{ store.unit }}</span>
        </div>
      </div>
    </div>

    <div :class="[
      'p-4 rounded-lg border',
      canCalculateVolume && result.isValid
        ? 'bg-gradient-to-br from-[#5D8A66]/10 to-[#8B6914]/10 border-[#5D8A66]/30'
        : 'bg-gray-50 border-gray-200 opacity-70'
    ]">
      <div class="text-sm text-gray-600 mb-1 flex items-center gap-1">
        <FlaskConical class="w-4 h-4" />容量估算
      </div>
      <div class="text-2xl font-bold text-[#5D4E2B]">
        {{ canCalculateVolume && result.isValid ? formatNumber(result.volume, 1) : '--' }}
        <span class="text-sm font-normal text-gray-500 ml-1">mL</span>
      </div>
      <div v-if="volumeBlockReason" class="mt-2 text-xs text-amber-600 flex items-start gap-1">
        <AlertTriangle class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
        <span>{{ volumeBlockReason }}</span>
      </div>
      <div v-else-if="!result.isValid && result.errors.length > 0" class="mt-2 text-xs text-amber-600 flex items-start gap-1">
        <AlertTriangle class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
        <span>{{ result.errors[0] }}</span>
      </div>
      <div v-if="validation.warnings.length > 0" class="mt-2 space-y-1">
        <div v-for="(w, i) in validation.warnings" :key="i" class="text-xs text-amber-600 flex items-start gap-1">
          <AlertTriangle class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>{{ w }}</span>
        </div>
      </div>
    </div>

    <div class="mt-2">
      <div class="text-xs font-semibold text-gray-600 mb-2">数据校验状态</div>
      <div class="space-y-1.5">
        <div class="flex items-center gap-2 text-xs">
          <component
            :is="store.controlPoints.length >= 3 ? CheckCircle2 : XCircle"
            :class="['w-4 h-4', store.controlPoints.length >= 3 ? 'text-green-600' : 'text-red-500']"
          />
          <span :class="store.controlPoints.length >= 3 ? 'text-gray-700' : 'text-red-600'">
            控制点数量 ≥ 3（当前 {{ store.controlPoints.length }} 个）
          </span>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <component
            :is="validation.errors.filter(e => e.includes('负数')).length === 0 ? CheckCircle2 : XCircle"
            :class="['w-4 h-4', validation.errors.filter(e => e.includes('负数')).length === 0 ? 'text-green-600' : 'text-red-500']"
          />
          <span :class="validation.errors.filter(e => e.includes('负数')).length === 0 ? 'text-gray-700' : 'text-red-600'">
            高度、半径均为非负数
          </span>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <component
            :is="validation.errors.filter(e => e.includes('自交')).length === 0 ? CheckCircle2 : XCircle"
            :class="['w-4 h-4', validation.errors.filter(e => e.includes('自交')).length === 0 ? 'text-green-600' : 'text-red-500']"
          />
          <span :class="validation.errors.filter(e => e.includes('自交')).length === 0 ? 'text-gray-700' : 'text-red-600'">
            剖面曲线无自交
          </span>
        </div>
      </div>
    </div>

    <div v-if="repairMarksDisplay.length > 0" class="mt-2">
      <div class="text-xs font-semibold text-gray-600 mb-2">修坯标记（{{ repairMarksDisplay.length }}）</div>
      <div class="space-y-1">
        <div
          v-for="m in repairMarksDisplay"
          :key="m.pointId"
          class="flex items-center justify-between px-2 py-1.5 bg-orange-50 rounded border border-orange-200 text-xs"
        >
          <span class="text-orange-700">⚒ 控制点 {{ m.pointNumber }}</span>
          <span v-if="m.description" class="text-gray-500 truncate max-w-[120px]">{{ m.description }}</span>
        </div>
      </div>
    </div>

    <button
      class="mt-auto w-full py-2.5 rounded-lg bg-[#5D8A66] text-white text-sm font-medium hover:bg-[#4a6f52] transition-colors flex items-center justify-center gap-2"
      @click="exportJson"
    >
      导出剖面数据
    </button>
  </div>
</template>
