<script setup lang="ts">
import { computed } from 'vue'
import {
  Ruler,
  CircleDot,
  FlaskConical,
  TrendingUp,
  Download,
  Eye,
  EyeOff,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Target,
  Layers,
} from 'lucide-vue-next'
import { useProfileStore } from '@/stores/profile'

const props = defineProps<{
  showOriginal: boolean
  showRestored: boolean
  showSpeculation: boolean
}>()

const emit = defineEmits<{
  (e: 'generate'): void
  (e: 'clear'): void
  (e: 'export'): void
  (e: 'update:showOriginal', value: boolean): void
  (e: 'update:showRestored', value: boolean): void
  (e: 'update:showSpeculation', value: boolean): void
}>()

const store = useProfileStore()

const restorationResult = computed(() => store.restorationResult)
const schemes = computed(() => store.restorationSchemes)
const currentScheme = computed(() => store.currentRestoration)
const currentProfile = computed(() => store.currentScheme)

const selectedIndex = computed(() =>
  schemes.value.findIndex(s => s.id === currentScheme.value?.id)
)

const restoredPointCount = computed(() =>
  currentScheme.value?.restoredPoints.filter(p => p.source === 'restored').length || 0
)

const originalPointCount = computed(() =>
  currentScheme.value?.restoredPoints.filter(p => p.source === 'original').length || 0
)

function formatNumber(v: number | null, digits: number = 1): string {
  if (v === null || v === undefined || isNaN(v)) return '--'
  return v.toFixed(digits)
}

function formatRange(range: { min: number; max: number; estimated: number } | null): string {
  if (!range) return '--'
  return `${formatNumber(range.min)} - ${formatNumber(range.max)}`
}

function formatEstimated(range: { min: number; max: number; estimated: number } | null): string {
  if (!range) return '--'
  return formatNumber(range.estimated)
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'text-green-600'
  if (confidence >= 0.6) return 'text-amber-600'
  if (confidence >= 0.4) return 'text-orange-600'
  return 'text-red-600'
}

function getConfidenceBg(confidence: number): string {
  if (confidence >= 0.8) return 'bg-green-50 border-green-200'
  if (confidence >= 0.6) return 'bg-amber-50 border-amber-200'
  if (confidence >= 0.4) return 'bg-orange-50 border-orange-200'
  return 'bg-red-50 border-red-200'
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.8) return '高'
  if (confidence >= 0.6) return '中高'
  if (confidence >= 0.4) return '中等'
  return '较低'
}

function getMethodDescription(method: string): string {
  switch (method) {
    case '保守':
      return '基于现有曲线最小范围外推，误差风险最小'
    case '适中':
      return '基于标准曲线趋势外推，平衡准确性与完整性'
    case '大胆':
      return '基于最大可能范围外推，适合缺损严重的器物'
    default:
      return ''
  }
}

function handleExport() {
  if (!currentProfile.value) return
  const data = store.exportRestoration()
  const blob = new Blob([data], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${currentProfile.value.name}_复原分析_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="w-full h-full flex flex-col gap-3 p-4 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9] overflow-y-auto">
    <div class="flex items-center justify-between pb-2 border-b border-[#E8DFC9]">
      <h3 class="text-base font-bold text-[#5D4E2B] flex items-center gap-2">
        <Layers class="w-4 h-4 text-[#8B6914]" />
        器型复原方案
      </h3>
      <div class="flex items-center gap-2">
        <button
          v-if="schemes.length > 0"
          class="px-2 py-1 text-xs rounded bg-white border border-gray-300 text-gray-600 hover:bg-gray-50 flex items-center gap-1"
          @click="emit('clear')"
        >
          <RefreshCw class="w-3 h-3" />
          重置
        </button>
        <button
          class="px-3 py-1.5 text-xs rounded bg-[#5D8A66] text-white hover:bg-[#4a6f52] flex items-center gap-1"
          @click="emit('generate')"
        >
          <RefreshCw class="w-3.5 h-3.5" />
          生成复原方案
        </button>
      </div>
    </div>

    <div v-if="restorationResult && !restorationResult.isValid" class="p-3 bg-red-50 rounded-lg border border-red-200">
      <div class="flex items-start gap-2">
        <AlertTriangle class="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
        <div class="text-xs text-red-700">
          <div class="font-semibold mb-1">无法生成复原方案</div>
          <div v-for="(err, i) in restorationResult.errors" :key="i" class="opacity-80">· {{ err }}</div>
        </div>
      </div>
    </div>

    <div v-else-if="schemes.length === 0" class="flex-1 flex flex-col items-center justify-center text-center p-6">
      <div class="w-16 h-16 rounded-full bg-[#5D8A66]/10 flex items-center justify-center mb-3">
        <TrendingUp class="w-8 h-8 text-[#5D8A66]" />
      </div>
      <div class="text-sm font-medium text-[#5D4E2B] mb-1">点击生成复原方案</div>
      <div class="text-xs text-gray-500 max-w-[200px]">
        系统将基于现存剖面曲线走势，自动生成 1-3 个复原方案供选择
      </div>
    </div>

    <template v-else>
      <div class="flex gap-2 mb-1">
        <button
          v-for="(s, idx) in schemes"
          :key="s.id"
          :class="[
            'flex-1 py-2 px-3 rounded-lg border text-xs font-medium transition-all',
            currentScheme?.id === s.id
              ? 'bg-[#5D8A66] text-white border-[#5D8A66]'
              : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
          ]"
          @click="store.selectRestoration(s.id)"
        >
          <div class="flex items-center justify-center gap-1 mb-0.5">
            <span>{{ s.name }}</span>
            <span
              :class="[
                'text-[10px] px-1.5 py-0.5 rounded-full',
                currentScheme?.id === s.id ? 'bg-white/20' : 'bg-gray-100'
              ]"
            >
              {{ (s.confidence * 100).toFixed(0) }}%
            </span>
          </div>
          <div :class="currentScheme?.id === s.id ? 'text-white/70' : 'text-gray-400'">
            方案 {{ idx + 1 }}
          </div>
        </button>
      </div>

      <div v-if="currentScheme" :class="['p-3 rounded-lg border', getConfidenceBg(currentScheme.confidence)]">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <Target class="w-4 h-4 text-[#5D4E2B]" />
            <span class="text-sm font-semibold text-[#5D4E2B]">{{ currentScheme.name }}方案说明</span>
          </div>
          <div :class="['text-xs font-semibold', getConfidenceColor(currentScheme.confidence)]">
            可信度: {{ getConfidenceLabel(currentScheme.confidence) }} ({{ (currentScheme.confidence * 100).toFixed(0) }}%)
          </div>
        </div>
        <p class="text-xs text-gray-600 mb-2">{{ getMethodDescription(currentScheme.method) }}</p>
        <div class="flex gap-4 text-[11px] text-gray-500">
          <span>原始控制点: {{ originalPointCount }} 个</span>
          <span>复原控制点: {{ restoredPointCount }} 个</span>
        </div>
      </div>

      <div class="space-y-2">
        <div class="text-xs font-semibold text-gray-600 flex items-center gap-1">
          <Eye class="w-3 h-3" />
          显示选项
        </div>
        <div class="flex gap-2">
          <button
            :class="[
              'flex-1 py-1.5 px-2 rounded border text-xs flex items-center justify-center gap-1 transition-all',
              showOriginal ? 'bg-[#5D8A66] text-white border-[#5D8A66]' : 'bg-white text-gray-600 border-gray-200'
            ]"
            @click="emit('update:showOriginal', !showOriginal)"
          >
            <component :is="showOriginal ? Eye : EyeOff" class="w-3 h-3" />
            原始剖面
          </button>
          <button
            :class="[
              'flex-1 py-1.5 px-2 rounded border text-xs flex items-center justify-center gap-1 transition-all',
              showRestored ? 'bg-[#8B6914] text-white border-[#8B6914]' : 'bg-white text-gray-600 border-gray-200'
            ]"
            @click="emit('update:showRestored', !showRestored)"
          >
            <component :is="showRestored ? Eye : EyeOff" class="w-3 h-3" />
            复原结果
          </button>
          <button
            :class="[
              'flex-1 py-1.5 px-2 rounded border text-xs flex items-center justify-center gap-1 transition-all',
              showSpeculation ? 'bg-[#E65100] text-white border-[#E65100]' : 'bg-white text-gray-600 border-gray-200'
            ]"
            @click="emit('update:showSpeculation', !showSpeculation)"
          >
            <component :is="showSpeculation ? Eye : EyeOff" class="w-3 h-3" />
            推测区间
          </button>
        </div>
      </div>

      <div class="space-y-2">
        <div class="text-xs font-semibold text-gray-600 flex items-center gap-1">
          <Ruler class="w-3 h-3" />
          尺寸参数范围
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div class="p-2.5 bg-white rounded-lg border border-[#E8DFC9]">
            <div class="text-[10px] text-gray-500 mb-0.5 flex items-center gap-1">
              <CircleDot class="w-3 h-3" />口径
            </div>
            <div class="text-sm font-bold text-[#5D4E2B]">
              {{ formatEstimated(currentScheme.mouthDiameter) }}
              <span class="text-xs font-normal text-gray-500">{{ currentScheme.unit }}</span>
            </div>
            <div class="text-[10px] text-gray-400 mt-0.5">
              范围: {{ formatRange(currentScheme.mouthDiameter) }}
            </div>
          </div>
          <div class="p-2.5 bg-white rounded-lg border border-[#E8DFC9]">
            <div class="text-[10px] text-gray-500 mb-0.5 flex items-center gap-1">
              <CircleDot class="w-3 h-3" />腹径
            </div>
            <div class="text-sm font-bold text-[#5D4E2B]">
              {{ formatEstimated(currentScheme.bellyDiameter) }}
              <span class="text-xs font-normal text-gray-500">{{ currentScheme.unit }}</span>
            </div>
            <div class="text-[10px] text-gray-400 mt-0.5">
              范围: {{ formatRange(currentScheme.bellyDiameter) }}
            </div>
          </div>
          <div class="p-2.5 bg-white rounded-lg border border-[#E8DFC9]">
            <div class="text-[10px] text-gray-500 mb-0.5 flex items-center gap-1">
              <CircleDot class="w-3 h-3" />底径
            </div>
            <div class="text-sm font-bold text-[#5D4E2B]">
              {{ formatEstimated(currentScheme.bottomDiameter) }}
              <span class="text-xs font-normal text-gray-500">{{ currentScheme.unit }}</span>
            </div>
            <div class="text-[10px] text-gray-400 mt-0.5">
              范围: {{ formatRange(currentScheme.bottomDiameter) }}
            </div>
          </div>
          <div class="p-2.5 bg-white rounded-lg border border-[#E8DFC9]">
            <div class="text-[10px] text-gray-500 mb-0.5 flex items-center gap-1">
              <Ruler class="w-3 h-3" />高度
            </div>
            <div class="text-sm font-bold text-[#5D4E2B]">
              {{ formatEstimated(currentScheme.height) }}
              <span class="text-xs font-normal text-gray-500">{{ currentScheme.unit }}</span>
            </div>
            <div class="text-[10px] text-gray-400 mt-0.5">
              范围: {{ formatRange(currentScheme.height) }}
            </div>
          </div>
        </div>
      </div>

      <div class="p-3 rounded-lg bg-gradient-to-br from-[#5D8A66]/10 to-[#8B6914]/10 border border-[#5D8A66]/30">
        <div class="text-xs text-gray-600 mb-1 flex items-center gap-1">
          <FlaskConical class="w-4 h-4" />容量估算
        </div>
        <div class="text-xl font-bold text-[#5D4E2B]">
          {{ formatEstimated(currentScheme.volume) }}
          <span class="text-sm font-normal text-gray-500 ml-1">mL</span>
        </div>
        <div v-if="currentScheme.volume" class="text-[10px] text-gray-500 mt-0.5">
          范围: {{ formatRange(currentScheme.volume) }} mL
        </div>
      </div>

      <div class="mt-2 space-y-1.5">
        <div class="text-xs font-semibold text-gray-600">数据完整性校验</div>
        <div class="flex items-center gap-2 text-xs">
          <CheckCircle2 class="w-4 h-4 text-green-600" />
          <span class="text-gray-700">
            已生成 {{ schemes.length }} 个复原方案
          </span>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <CheckCircle2 class="w-4 h-4 text-green-600" />
          <span class="text-gray-700">
            已补全 {{ restoredPointCount }} 个缺失控制点
          </span>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <CheckCircle2 class="w-4 h-4 text-green-600" />
          <span class="text-gray-700">
            平均可信度 {{ (schemes.reduce((a, b) => a + b.confidence, 0) / schemes.length * 100).toFixed(0) }}%
          </span>
        </div>
      </div>

      <button
        class="mt-auto w-full py-2.5 rounded-lg bg-[#5D8A66] text-white text-sm font-medium hover:bg-[#4a6f52] transition-colors flex items-center justify-center gap-2"
        @click="handleExport"
      >
        <Download class="w-4 h-4" />
        导出复原分析数据
      </button>
    </template>
  </div>
</template>
