<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { TrendingUp, AlertTriangle, Download, Calendar, BarChart2 } from 'lucide-vue-next'
import { api } from '@/lib/api'
import type { SedimentTrendResult } from '@/types'

const props = defineProps<{
  culvertId: number | undefined
}>()

const months = ref(12)
const result = ref<SedimentTrendResult | null>(null)
const loading = ref(false)
const generatingReport = ref(false)

async function analyze() {
  if (!props.culvertId) return
  loading.value = true
  try {
    result.value = await api.analysis.sedimentTrend(props.culvertId, months.value)
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
    const result = await api.reports.generate(props.culvertId, 'risk')
    window.open(`http://localhost:8001${result.file_url}`, '_blank')
  } catch (e) {
    console.error('生成报告失败', e)
  } finally {
    generatingReport.value = false
  }
}

watch(() => props.culvertId, (id) => {
  if (id) {
    analyze()
  }
}, { immediate: true })

const maxThickness = computed(() => {
  if (!result.value?.trend_points.length) return 1
  return Math.max(...result.value.trend_points.map(p => p.avg_thickness)) * 1.2
})

const riskLevelColor = computed(() => {
  switch (result.value?.risk_level) {
    case '高': return 'text-red-600 bg-red-100'
    case '中': return 'text-orange-600 bg-orange-100'
    case '低': return 'text-green-600 bg-green-100'
    default: return 'text-gray-600 bg-gray-100'
  }
})
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-bold text-[#5D4E2B] flex items-center gap-2">
        <span class="inline-block w-1 h-5 bg-[#F59E0B] rounded"></span>
        淤积趋势分析
      </h2>
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <Calendar class="w-4 h-4 text-gray-500" />
          <span class="text-sm text-gray-600">分析时长：</span>
          <select v-model="months" class="px-3 py-1.5 border rounded-lg text-sm" @change="analyze">
            <option :value="6">近6个月</option>
            <option :value="12">近12个月</option>
            <option :value="24">近24个月</option>
          </select>
        </div>
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

    <div class="flex-1 bg-white rounded-xl border border-[#E8DFC9] p-6 overflow-y-auto">
      <div v-if="loading" class="w-full h-full flex items-center justify-center">
        <div class="text-gray-500">分析中...</div>
      </div>
      <div v-else-if="!result || result.trend_points.length === 0" class="w-full h-full flex items-center justify-center">
        <div class="text-gray-500 text-center">
          <TrendingUp class="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <div>暂无淤积记录数据</div>
        </div>
      </div>
      <div v-else class="space-y-6">
        <div class="grid grid-cols-5 gap-4">
          <div class="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200">
            <div class="text-xs text-blue-600 mb-1">暗渠名称</div>
            <div class="text-lg font-bold text-blue-700 truncate">{{ result.culvert_name }}</div>
          </div>
          <div class="p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl border border-orange-200">
            <div class="text-xs text-orange-600 mb-1">平均淤积速率</div>
            <div class="text-lg font-bold text-orange-700">{{ (result.avg_sediment_rate * 1000).toFixed(1) }} mm/月</div>
          </div>
          <div class="p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-xl border border-red-200">
            <div class="text-xs text-red-600 mb-1">最大淤积厚度</div>
            <div class="text-lg font-bold text-red-700">{{ (result.max_thickness * 100).toFixed(1) }} cm</div>
          </div>
          <div class="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border border-purple-200">
            <div class="text-xs text-purple-600 mb-1">预测6个月后</div>
            <div class="text-lg font-bold text-purple-700">{{ (result.predicted_thickness_6m * 100).toFixed(1) }} cm</div>
          </div>
          <div class="p-4 rounded-xl border" :class="riskLevelColor">
            <div class="text-xs mb-1">风险等级</div>
            <div class="text-lg font-bold flex items-center gap-1">
              <AlertTriangle class="w-4 h-4" />
              {{ result.risk_level }}风险
            </div>
          </div>
        </div>

        <div class="p-4 bg-[#FAF6ED] rounded-xl border border-[#E8DFC9]">
          <h4 class="text-sm font-semibold text-[#5D4E2B] mb-4 flex items-center gap-2">
            <BarChart2 class="w-4 h-4" />
            淤积厚度趋势图
          </h4>
          <div class="flex items-end gap-2 h-48 px-4">
            <div
              v-for="(point, index) in result.trend_points"
              :key="index"
              class="flex-1 flex flex-col items-center gap-2"
            >
              <div class="text-xs font-medium text-gray-700">{{ (point.avg_thickness * 100).toFixed(0) }}cm</div>
              <div
                class="w-full rounded-t-lg transition-all duration-500"
                :class="[
                  point.avg_thickness >= 0.8 ? 'bg-red-500' :
                  point.avg_thickness >= 0.5 ? 'bg-orange-500' :
                  'bg-green-500'
                ]"
                :style="{ height: `${(point.avg_thickness / maxThickness) * 100}%`, minHeight: '4px' }"
              ></div>
              <div class="text-xs text-gray-500">{{ point.date }}</div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="p-4 bg-white rounded-xl border border-gray-200">
            <h4 class="text-sm font-semibold text-[#5D4E2B] mb-3">预测分析</h4>
            <div class="space-y-3">
              <div class="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <span class="text-sm text-gray-600">6个月后预测淤积厚度</span>
                <span :class="[
                  'text-base font-bold',
                  result.predicted_thickness_6m >= 0.8 ? 'text-red-600' :
                  result.predicted_thickness_6m >= 0.5 ? 'text-orange-600' :
                  'text-green-600'
                ]">{{ (result.predicted_thickness_6m * 100).toFixed(1) }} cm</span>
              </div>
              <div class="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <span class="text-sm text-gray-600">12个月后预测淤积厚度</span>
                <span :class="[
                  'text-base font-bold',
                  result.predicted_thickness_12m >= 0.8 ? 'text-red-600' :
                  result.predicted_thickness_12m >= 0.5 ? 'text-orange-600' :
                  'text-green-600'
                ]">{{ (result.predicted_thickness_12m * 100).toFixed(1) }} cm</span>
              </div>
            </div>
          </div>

          <div class="p-4 bg-white rounded-xl border border-gray-200">
            <h4 class="text-sm font-semibold text-[#5D4E2B] mb-3">建议措施</h4>
            <div class="space-y-2">
              <div
                v-for="(suggestion, index) in [
                  result.risk_level === '高' ? '立即安排清淤作业，清除严重淤积' : null,
                  result.risk_level !== '低' ? '建立季度监测机制，跟踪淤积变化' : null,
                  '制定年度清淤计划，保持排水能力',
                  '考虑在高风险区域增设沉沙设施',
                ].filter(Boolean)"
                :key="index"
                class="flex items-start gap-2 text-sm text-gray-700"
              >
                <span class="text-[#5D8A66] font-bold mt-0.5">•</span>
                <span>{{ suggestion }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="p-4 bg-white rounded-xl border border-gray-200">
          <h4 class="text-sm font-semibold text-[#5D4E2B] mb-3">历史淤积数据</h4>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">月份</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">平均淤积厚度</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">累计淤积量</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">状态</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="(point, index) in result.trend_points" :key="index" class="hover:bg-gray-50">
                  <td class="px-4 py-2">{{ point.date }}</td>
                  <td class="px-4 py-2">
                    <span :class="[
                      'font-medium',
                      point.avg_thickness >= 0.8 ? 'text-red-600' :
                      point.avg_thickness >= 0.5 ? 'text-orange-600' :
                      'text-green-600'
                    ]">{{ (point.avg_thickness * 100).toFixed(1) }} cm</span>
                  </td>
                  <td class="px-4 py-2">{{ point.accumulated_volume.toFixed(1) }} m³</td>
                  <td class="px-4 py-2">
                    <span :class="[
                      'text-xs px-2 py-0.5 rounded',
                      point.avg_thickness >= 0.8 ? 'bg-red-100 text-red-700' :
                      point.avg_thickness >= 0.5 ? 'bg-orange-100 text-orange-700' :
                      'bg-green-100 text-green-700'
                    ]">
                      {{ point.avg_thickness >= 0.8 ? '严重淤积' :
                         point.avg_thickness >= 0.5 ? '中度淤积' : '正常' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
