<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { BarChart3, CloudRain, CheckCircle, XCircle, Download, ArrowUpRight } from 'lucide-vue-next'
import { api } from '@/lib/api'
import type { DrainageCapacityResult, RainScenario } from '@/types'

const props = defineProps<{
  culvertId: number | undefined
}>()

const scenarios = ref<RainScenario[]>([])
const selectedScenarios = ref<number[]>([])
const results = ref<DrainageCapacityResult[]>([])
const loading = ref(false)
const generatingReport = ref(false)

async function loadScenarios() {
  try {
    scenarios.value = await api.scenarios.list()
    if (scenarios.value.length > 0) {
      selectedScenarios.value = scenarios.value.slice(0, 3).map(s => s.id)
    }
  } catch (e) {
    console.error('加载降雨情景失败', e)
  }
}

async function analyze() {
  if (!props.culvertId || selectedScenarios.value.length === 0) return
  loading.value = true
  try {
    results.value = await api.analysis.drainageCapacity(props.culvertId, selectedScenarios.value)
  } catch (e) {
    console.error('分析失败', e)
  } finally {
    loading.value = false
  }
}

async function generateReport() {
  if (!props.culvertId) return
  generatingReport.value = true
  try {
    const result = await api.reports.generate(props.culvertId, 'drainage')
    window.open(`http://localhost:8001${result.file_url}`, '_blank')
  } catch (e) {
    console.error('生成报告失败', e)
  } finally {
    generatingReport.value = false
  }
}

function toggleScenario(id: number) {
  const idx = selectedScenarios.value.indexOf(id)
  if (idx >= 0) {
    selectedScenarios.value.splice(idx, 1)
  } else {
    selectedScenarios.value.push(id)
  }
}

watch(() => props.culvertId, (id) => {
  if (id && selectedScenarios.value.length > 0) {
    analyze()
  }
}, { immediate: true })

onMounted(() => {
  loadScenarios()
})

const maxCapacity = ref(10)
const maxFlow = ref(10)

function getBarWidth(value: number, max: number) {
  return `${Math.min(100, (value / max) * 100)}%`
}

watch(results, (newResults) => {
  if (newResults.length > 0) {
    maxCapacity.value = Math.max(...newResults.map(r => r.actual_capacity)) * 1.2
    maxFlow.value = Math.max(...newResults.map(r => r.design_flow)) * 1.2
  }
})
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-bold text-[#5D4E2B] flex items-center gap-2">
        <span class="inline-block w-1 h-5 bg-[#2563EB] rounded"></span>
        排水能力对比分析
      </h2>
      <div class="flex gap-2">
        <button
          :disabled="loading || selectedScenarios.length === 0"
          class="px-4 py-1.5 bg-[#2563EB] text-white text-sm rounded-lg hover:bg-[#1E40AF] transition-colors flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="analyze"
        >
          <BarChart3 class="w-4 h-4" />
          开始分析
        </button>
        <button
          :disabled="generatingReport || results.length === 0"
          class="px-4 py-1.5 bg-[#5D8A66] text-white text-sm rounded-lg hover:bg-[#4a6f52] transition-colors flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="generateReport"
        >
          <Download class="w-4 h-4" />
          导出报告
        </button>
      </div>
    </div>

    <div class="flex-1 flex gap-4 overflow-hidden">
      <div class="w-64 bg-white rounded-xl border border-[#E8DFC9] p-4 flex-shrink-0 overflow-y-auto">
        <h3 class="text-sm font-semibold text-[#5D4E2B] mb-3 flex items-center gap-2">
          <CloudRain class="w-4 h-4 text-[#2563EB]" />
          选择降雨情景
        </h3>
        <div class="space-y-2">
          <div
            v-for="scenario in scenarios"
            :key="scenario.id"
            :class="[
              'p-3 rounded-lg border cursor-pointer transition-all',
              selectedScenarios.includes(scenario.id)
                ? 'border-[#2563EB] bg-[#2563EB]/5'
                : 'border-gray-200 hover:border-gray-300'
            ]"
            @click="toggleScenario(scenario.id)"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-medium text-[#5D4E2B]">{{ scenario.name }}</span>
              <div
                :class="[
                  'w-4 h-4 rounded border-2 flex items-center justify-center',
                  selectedScenarios.includes(scenario.id)
                    ? 'border-[#2563EB] bg-[#2563EB]'
                    : 'border-gray-300'
                ]"
              >
                <CheckCircle v-if="selectedScenarios.includes(scenario.id)" class="w-3 h-3 text-white" />
              </div>
            </div>
            <div class="text-xs text-gray-500 space-y-0.5">
              <div>重现期：{{ scenario.return_period }}年一遇</div>
              <div>降雨量：{{ scenario.total_rainfall }}mm</div>
              <div>降雨时长：{{ scenario.rainfall_duration }}h</div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex-1 bg-white rounded-xl border border-[#E8DFC9] p-4 overflow-y-auto">
        <div v-if="loading" class="w-full h-full flex items-center justify-center">
          <div class="text-gray-500">分析中...</div>
        </div>
        <div v-else-if="results.length === 0" class="w-full h-full flex items-center justify-center">
          <div class="text-gray-500 text-center">
            <CloudRain class="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <div>请选择降雨情景并点击分析按钮</div>
          </div>
        </div>
        <div v-else class="space-y-6">
          <div class="grid grid-cols-3 gap-4">
            <div class="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200">
              <div class="text-xs text-blue-600 mb-1">分析情景数</div>
              <div class="text-2xl font-bold text-blue-700">{{ results.length }}</div>
            </div>
            <div class="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200">
              <div class="text-xs text-green-600 mb-1">达标情景</div>
              <div class="text-2xl font-bold text-green-700">{{ results.filter(r => r.is_sufficient).length }}</div>
            </div>
            <div class="p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-xl border border-red-200">
              <div class="text-xs text-red-600 mb-1">不达标情景</div>
              <div class="text-2xl font-bold text-red-700">{{ results.filter(r => !r.is_sufficient).length }}</div>
            </div>
          </div>

          <div class="space-y-4">
            <h4 class="text-sm font-semibold text-[#5D4E2B]">排水能力对比</h4>
            <div class="space-y-4">
              <div
                v-for="result in results"
                :key="result.scenario_id"
                class="p-4 rounded-xl border"
                :class="result.is_sufficient ? 'border-green-200 bg-green-50/50' : 'border-red-200 bg-red-50/50'"
              >
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center gap-2">
                    <component
                      :is="result.is_sufficient ? CheckCircle : XCircle"
                      :class="result.is_sufficient ? 'text-green-500' : 'text-red-500'"
                      class="w-5 h-5"
                    />
                    <span class="font-semibold text-[#5D4E2B]">{{ result.scenario_name }}</span>
                    <span class="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">{{ result.return_period }}年一遇</span>
                  </div>
                  <span
                    :class="[
                      'text-sm font-medium px-2 py-0.5 rounded',
                      result.is_sufficient ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    ]"
                  >
                    {{ result.is_sufficient ? '排水能力充足' : '排水能力不足' }}
                  </span>
                </div>

                <div class="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <div class="text-xs text-gray-500 mb-1">设计流量 (m³/s)</div>
                    <div class="flex items-center gap-2">
                      <div class="h-6 bg-gray-200 rounded-full flex-1 overflow-hidden">
                        <div
                          class="h-full bg-orange-400 rounded-full transition-all"
                          :style="{ width: getBarWidth(result.design_flow, maxFlow) }"
                        ></div>
                      </div>
                      <span class="text-sm font-semibold text-orange-600 w-16 text-right">{{ result.design_flow.toFixed(2) }}</span>
                    </div>
                  </div>
                  <div>
                    <div class="text-xs text-gray-500 mb-1">实际排水能力 (m³/s)</div>
                    <div class="flex items-center gap-2">
                      <div class="h-6 bg-gray-200 rounded-full flex-1 overflow-hidden">
                        <div
                          class="h-full bg-blue-500 rounded-full transition-all"
                          :style="{ width: getBarWidth(result.actual_capacity, maxCapacity) }"
                        ></div>
                      </div>
                      <span class="text-sm font-semibold text-blue-600 w-16 text-right">{{ result.actual_capacity.toFixed(2) }}</span>
                    </div>
                  </div>
                </div>

                <div class="grid grid-cols-3 gap-3 pt-3 border-t border-gray-200">
                  <div class="text-center">
                    <div class="text-xs text-gray-500">溢流量</div>
                    <div :class="['text-base font-bold', result.overflow > 0 ? 'text-red-600' : 'text-green-600']">
                      {{ result.overflow.toFixed(2) }} m³/s
                    </div>
                  </div>
                  <div class="text-center">
                    <div class="text-xs text-gray-500">溢流比例</div>
                    <div :class="['text-base font-bold', result.overflow_ratio > 0 ? 'text-red-600' : 'text-green-600']">
                      {{ (result.overflow_ratio * 100).toFixed(1) }}%
                    </div>
                  </div>
                  <div class="text-center">
                    <div class="text-xs text-gray-500">总降雨量</div>
                    <div class="text-base font-bold text-[#5D4E2B]">
                      {{ result.total_rainfall }} mm
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
