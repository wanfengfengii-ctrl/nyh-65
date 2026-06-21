<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { AlertTriangle, AlertCircle, AlertOctagon, Download, RefreshCw } from 'lucide-vue-next'
import { api } from '@/lib/api'
import type { RiskWarningResult } from '@/types'

const props = defineProps<{
  culvertId: number | undefined
}>()

const result = ref<RiskWarningResult | null>(null)
const loading = ref(false)
const generatingReport = ref(false)
const filterLevel = ref<string>('all')

async function loadWarnings() {
  if (!props.culvertId) return
  loading.value = true
  try {
    result.value = await api.analysis.riskWarnings(props.culvertId)
  } catch (e) {
    console.error('加载风险预警失败', e)
  } finally {
    loading.value = false
  }
}

async function generateReport() {
  if (!props.culvertId) return
  generatingReport.value = true
  try {
    const result = await api.reports.generate(props.culvertId, 'risk')
    window.open(`http://localhost:8001${result.file_url}`, '_blank')
  } catch (e) {
    console.error('生成报告失败', e)
  } finally {
    generatingReport.value = false
  }
}

function getRiskIcon(level: string) {
  switch (level) {
    case '高': return AlertOctagon
    case '中': return AlertTriangle
    case '低': return AlertCircle
    default: return AlertCircle
  }
}

function getRiskColor(level: string) {
  switch (level) {
    case '高': return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-600', icon: 'text-red-500' }
    case '中': return { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-600', icon: 'text-orange-500' }
    case '低': return { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-600', icon: 'text-yellow-500' }
    default: return { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-600', icon: 'text-gray-500' }
  }
}

watch(() => props.culvertId, (id) => {
  if (id) {
    loadWarnings()
  }
}, { immediate: true })

onMounted(() => {
  loadWarnings()
})

const filteredSections = () => {
  if (!result.value) return []
  if (filterLevel.value === 'all') return result.value.risk_sections
  return result.value.risk_sections.filter(s => s.risk_level === filterLevel.value)
}
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-bold text-[#5D4E2B] flex items-center gap-2">
        <span class="inline-block w-1 h-5 bg-red-500 rounded"></span>
        高风险区段预警
      </h2>
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-600">筛选：</span>
          <select v-model="filterLevel" class="px-3 py-1.5 border rounded-lg text-sm">
            <option value="all">全部</option>
            <option value="高">高风险</option>
            <option value="中">中风险</option>
            <option value="低">低风险</option>
          </select>
        </div>
        <button
          class="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-1.5"
          @click="loadWarnings"
        >
          <RefreshCw class="w-4 h-4" />
          刷新
        </button>
        <button
          :disabled="generatingReport || !result"
          class="px-4 py-1.5 bg-[#5D8A66] text-white text-sm rounded-lg hover:bg-[#4a6f52] transition-colors flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="generateReport"
        >
          <Download class="w-4 h-4" />
          导出报告
        </button>
      </div>
    </div>

    <div class="flex-1 bg-white rounded-xl border border-[#E8DFC9] overflow-hidden flex flex-col">
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="text-gray-500">加载中...</div>
      </div>
      <div v-else-if="!result || result.total_risk_sections === 0" class="flex-1 flex items-center justify-center">
        <div class="text-gray-500 text-center">
          <AlertCircle class="w-12 h-12 text-green-400 mx-auto mb-2" />
          <div class="text-green-600 font-medium">暂无高风险区段</div>
          <div class="text-sm text-gray-400 mt-1">排水系统状态良好</div>
        </div>
      </div>
      <div v-else class="flex flex-col h-full">
        <div class="grid grid-cols-4 gap-4 p-4 bg-gradient-to-r from-gray-50 to-white border-b">
          <div class="p-3 bg-white rounded-lg border border-gray-200">
            <div class="text-xs text-gray-500 mb-1">风险区段总数</div>
            <div class="text-2xl font-bold text-gray-800">{{ result.total_risk_sections }}</div>
          </div>
          <div class="p-3 bg-red-50 rounded-lg border border-red-200">
            <div class="text-xs text-red-600 mb-1">高风险</div>
            <div class="text-2xl font-bold text-red-600">{{ result.high_risk_count }}</div>
          </div>
          <div class="p-3 bg-orange-50 rounded-lg border border-orange-200">
            <div class="text-xs text-orange-600 mb-1">中风险</div>
            <div class="text-2xl font-bold text-orange-600">{{ result.medium_risk_count }}</div>
          </div>
          <div class="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div class="text-xs text-yellow-600 mb-1">低风险</div>
            <div class="text-2xl font-bold text-yellow-600">{{ result.low_risk_count }}</div>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-4">
          <div class="space-y-3">
            <div
              v-for="(section, index) in filteredSections()"
              :key="index"
              class="p-4 rounded-xl border transition-all hover:shadow-md"
              :class="[
                getRiskColor(section.risk_level).bg,
                getRiskColor(section.risk_level).border
              ]"
            >
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-3">
                  <div
                    :class="[
                      'w-10 h-10 rounded-full flex items-center justify-center',
                      section.risk_level === '高' ? 'bg-red-100' :
                      section.risk_level === '中' ? 'bg-orange-100' : 'bg-yellow-100'
                    ]"
                  >
                    <component
                      :is="getRiskIcon(section.risk_level)"
                      :class="['w-5 h-5', getRiskColor(section.risk_level).icon]"
                    />
                  </div>
                  <div>
                    <div class="font-semibold text-[#5D4E2B]">
                      桩号 {{ section.start_station }} - {{ section.end_station }} 米
                    </div>
                    <div class="text-sm text-gray-600">{{ section.description }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <div class="text-right">
                    <div class="text-xs text-gray-500">风险评分</div>
                    <div :class="['text-lg font-bold', getRiskColor(section.risk_level).text]">
                      {{ section.risk_score.toFixed(1) }}
                    </div>
                  </div>
                  <span
                    :class="[
                      'text-xs px-2 py-1 rounded font-medium',
                      section.risk_level === '高' ? 'bg-red-100 text-red-700' :
                      section.risk_level === '中' ? 'bg-orange-100 text-orange-700' :
                      'bg-yellow-100 text-yellow-700'
                    ]"
                  >
                    {{ section.risk_level }}风险
                  </span>
                </div>
              </div>
              <div
                :class="[
                  'p-3 rounded-lg',
                  section.risk_level === '高' ? 'bg-red-100/50' :
                  section.risk_level === '中' ? 'bg-orange-100/50' : 'bg-yellow-100/50'
                ]"
              >
                <div class="text-xs font-medium text-gray-600 mb-1">处置建议</div>
                <div :class="['text-sm', getRiskColor(section.risk_level).text]">
                  {{ section.suggestion }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
