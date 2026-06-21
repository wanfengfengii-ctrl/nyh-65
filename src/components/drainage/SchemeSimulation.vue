<script setup lang="ts">
import { ref, watch } from 'vue'
import { Settings, TrendingUp, DollarSign, Clock, CheckCircle2, Play } from 'lucide-vue-next'
import { api } from '@/lib/api'
import type { SimulationResult } from '@/types'

const props = defineProps<{
  culvertId: number | undefined
}>()

const planType = ref('cleaning')
const parameters = ref<any>({
  cleaning_ratio: 1.0,
  expansion_ratio: 0.2,
  new_slope: 0.005,
})
const result = ref<SimulationResult | null>(null)
const loading = ref(false)
const history = ref<SimulationResult[]>([])

const planTypes = [
  { id: 'cleaning', name: '清淤方案', description: '通过清除淤积恢复排水能力', icon: '🧹' },
  { id: 'expansion', name: '断面扩建', description: '扩大断面尺寸提升排水能力', icon: '📐' },
  { id: 'slope', name: '坡度调整', description: '调整管道坡度改善排水条件', icon: '📈' },
]

async function runSimulation() {
  if (!props.culvertId) return
  loading.value = true
  try {
    let params: Record<string, any> = {}
    if (planType.value === 'cleaning') {
      params = { cleaning_ratio: parameters.value.cleaning_ratio }
    } else if (planType.value === 'expansion') {
      params = { expansion_ratio: parameters.value.expansion_ratio }
    } else if (planType.value === 'slope') {
      params = { new_slope: parameters.value.new_slope }
    }

    result.value = await api.analysis.simulate(props.culvertId, planType.value, params)
    if (result.value) {
      history.value.unshift({ ...result.value })
      if (history.value.length > 5) {
        history.value.pop()
      }
    }
  } catch (e) {
    console.error('模拟失败', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.culvertId, () => {
  result.value = null
  history.value = []
})

function formatCurrency(value: number) {
  if (value >= 10000) {
    return `${(value / 10000).toFixed(1)}万`
  }
  return `${value.toFixed(0)}元`
}
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-bold text-[#5D4E2B] flex items-center gap-2">
        <span class="inline-block w-1 h-5 bg-[#8B5CF6] rounded"></span>
        治理方案模拟
      </h2>
    </div>

    <div class="flex-1 flex gap-4 overflow-hidden">
      <div class="w-80 bg-white rounded-xl border border-[#E8DFC9] p-4 flex-shrink-0 flex flex-col">
        <h3 class="text-sm font-semibold text-[#5D4E2B] mb-3 flex items-center gap-2">
          <Settings class="w-4 h-4 text-[#8B5CF6]" />
          选择方案类型
        </h3>
        <div class="space-y-2 mb-4">
          <div
            v-for="plan in planTypes"
            :key="plan.id"
            :class="[
              'p-3 rounded-lg border cursor-pointer transition-all',
              planType === plan.id
                ? 'border-[#8B5CF6] bg-[#8B5CF6]/5'
                : 'border-gray-200 hover:border-gray-300'
            ]"
            @click="planType = plan.id as any"
          >
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xl">{{ plan.icon }}</span>
              <span class="font-medium text-[#5D4E2B]">{{ plan.name }}</span>
            </div>
            <div class="text-xs text-gray-500">{{ plan.description }}</div>
          </div>
        </div>

        <div class="flex-1">
          <h4 class="text-sm font-semibold text-[#5D4E2B] mb-3">参数设置</h4>
          <div v-if="planType === 'cleaning'" class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">
                清淤比例: {{ (parameters.cleaning_ratio * 100).toFixed(0) }}%
              </label>
              <input
                v-model.number="parameters.cleaning_ratio"
                type="range"
                min="0"
                max="1"
                step="0.1"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#8B5CF6]"
              />
              <div class="flex justify-between text-xs text-gray-400 mt-1">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>
            <div class="p-3 bg-purple-50 rounded-lg text-xs text-purple-700">
              清淤比例越高，排水能力恢复越好，但成本也相应增加
            </div>
          </div>

          <div v-else-if="planType === 'expansion'" class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">
                扩建比例: {{ (parameters.expansion_ratio * 100).toFixed(0) }}%
              </label>
              <input
                v-model.number="parameters.expansion_ratio"
                type="range"
                min="0.1"
                max="0.5"
                step="0.05"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#8B5CF6]"
              />
              <div class="flex justify-between text-xs text-gray-400 mt-1">
                <span>10%</span>
                <span>30%</span>
                <span>50%</span>
              </div>
            </div>
            <div class="p-3 bg-purple-50 rounded-lg text-xs text-purple-700">
              扩建比例越大，排水能力提升越明显，但工程量和成本也越高
            </div>
          </div>

          <div v-else-if="planType === 'slope'" class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">
                调整后坡度: {{ (parameters.new_slope * 1000).toFixed(1) }}‰
              </label>
              <input
                v-model.number="parameters.new_slope"
                type="range"
                min="0.001"
                max="0.01"
                step="0.0005"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#8B5CF6]"
              />
              <div class="flex justify-between text-xs text-gray-400 mt-1">
                <span>1‰</span>
                <span>5‰</span>
                <span>10‰</span>
              </div>
            </div>
            <div class="p-3 bg-purple-50 rounded-lg text-xs text-purple-700">
              坡度越大，排水流速越快，但需要考虑地形条件限制
            </div>
          </div>
        </div>

        <button
          :disabled="loading || !culvertId"
          class="w-full py-2.5 bg-[#8B5CF6] text-white text-sm font-medium rounded-lg hover:bg-[#7C3AED] transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="runSimulation"
        >
          <Play class="w-4 h-4" />
          {{ loading ? '模拟中...' : '运行模拟' }}
        </button>
      </div>

      <div class="flex-1 bg-white rounded-xl border border-[#E8DFC9] p-4 overflow-y-auto">
        <div v-if="!result" class="w-full h-full flex items-center justify-center">
          <div class="text-gray-500 text-center">
            <Settings class="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <div>选择方案类型并设置参数，点击运行模拟</div>
          </div>
        </div>

        <div v-else class="space-y-6">
          <div class="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-200">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-lg font-bold text-purple-700">{{ result.plan_type }}</h3>
              <span class="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">模拟完成</span>
            </div>

            <div class="grid grid-cols-2 gap-4 mb-4">
              <div class="p-3 bg-white rounded-lg">
                <div class="flex items-center gap-2 text-xs text-gray-500 mb-1">
                  <TrendingUp class="w-3.5 h-3.5" />
                  原排水能力
                </div>
                <div class="text-2xl font-bold text-gray-800">{{ result.original_capacity.toFixed(2) }} <span class="text-sm font-normal text-gray-500">m³/s</span></div>
              </div>
              <div class="p-3 bg-white rounded-lg">
                <div class="flex items-center gap-2 text-xs text-green-600 mb-1">
                  <TrendingUp class="w-3.5 h-3.5" />
                  模拟后排水能力
                </div>
                <div class="text-2xl font-bold text-green-600">{{ result.simulated_capacity.toFixed(2) }} <span class="text-sm font-normal text-gray-500">m³/s</span></div>
              </div>
            </div>

            <div class="p-3 bg-green-50 rounded-lg border border-green-200 mb-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <CheckCircle2 class="w-5 h-5 text-green-500" />
                  <span class="font-medium text-green-700">能力提升</span>
                </div>
                <span class="text-2xl font-bold text-green-600">+{{ (result.capacity_improvement * 100 / result.original_capacity).toFixed(1) }}%</span>
              </div>
              <div class="text-sm text-green-600 mt-1">
                排水能力提升 {{ result.capacity_improvement.toFixed(2) }} m³/s
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="p-3 bg-white rounded-lg">
                <div class="flex items-center gap-2 text-xs text-gray-500 mb-1">
                  <DollarSign class="w-3.5 h-3.5" />
                  预估费用
                </div>
                <div class="text-xl font-bold text-orange-600">¥{{ formatCurrency(result.cost_estimate) }}</div>
              </div>
              <div class="p-3 bg-white rounded-lg">
                <div class="flex items-center gap-2 text-xs text-gray-500 mb-1">
                  <Clock class="w-3.5 h-3.5" />
                  施工周期
                </div>
                <div class="text-xl font-bold text-blue-600">{{ result.construction_period }}</div>
              </div>
            </div>
          </div>

          <div class="p-4 bg-[#FAF6ED] rounded-xl border border-[#E8DFC9]">
            <h4 class="text-sm font-semibold text-[#5D4E2B] mb-2">方案说明</h4>
            <p class="text-sm text-gray-600">{{ result.suggestion }}</p>
          </div>

          <div v-if="history.length > 1" class="p-4 bg-white rounded-xl border border-gray-200">
            <h4 class="text-sm font-semibold text-[#5D4E2B] mb-3">模拟历史</h4>
            <div class="space-y-2">
              <div
                v-for="(h, index) in history.slice(1)"
                :key="index"
                class="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm"
              >
                <div class="flex items-center gap-3">
                  <span class="text-gray-400">#{{ history.length - index }}</span>
                  <span class="font-medium text-gray-700">{{ h.plan_type }}</span>
                </div>
                <div class="flex items-center gap-4">
                  <span class="text-green-600">+{{ (h.capacity_improvement * 100 / h.original_capacity).toFixed(1) }}%</span>
                  <span class="text-orange-600">¥{{ formatCurrency(h.cost_estimate) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
