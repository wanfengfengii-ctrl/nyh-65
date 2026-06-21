<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  Droplets, MapPin, TrendingUp, AlertTriangle, BarChart3, FileText, ChevronDown, ChevronRight } from 'lucide-vue-next'
import { api } from '@/lib/api'
import type { Culvert } from '@/types'
import CulvertList from '@/components/drainage/CulvertList.vue'
import DrainageAnalysis from '@/components/drainage/DrainageAnalysis.vue'
import SedimentAnalysis from '@/components/drainage/SedimentAnalysis.vue'
import RiskWarning from '@/components/drainage/RiskWarning.vue'
import SchemeSimulation from '@/components/drainage/SchemeSimulation.vue'
import ProfileView from '@/components/drainage/ProfileView.vue'

const activeTab = ref('list')
const culverts = ref<Culvert[]>([])
const selectedCulvert = ref<Culvert | null>(null)
const loading = ref(false)

const tabs = [
  { id: 'list', name: '暗渠管理', icon: Droplets },
  { id: 'drainage', name: '排水能力分析', icon: BarChart3 },
  { id: 'sediment', name: '淤积趋势分析', icon: TrendingUp },
  { id: 'risk', name: '风险预警', icon: AlertTriangle },
  { id: 'simulation', name: '方案模拟', icon: FileText },
  { id: 'profile', name: '纵断面图', icon: MapPin },
]

const selectedCulvertName = computed(() => selectedCulvert.value?.name || '请选择暗渠')

async function loadCulverts() {
  loading.value = true
  try {
    culverts.value = await api.culverts.list()
    if (culverts.value.length > 0) {
      selectedCulvert.value = culverts.value[0]
    }
  } catch (e) {
    console.error('加载暗渠列表失败', e)
  } finally {
    loading.value = false
  }
}

function selectCulvert(culvert: Culvert) {
  selectedCulvert.value = culvert
}

onMounted(() => {
  loadCulverts()
})
</script>

<template>
  <div class="w-screen h-screen flex flex-col overflow-hidden bg-[#F5F0E8]">
    <header class="h-14 flex items-center justify-between px-5 bg-white border-b border-[#E8DFC9] flex-shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#2563EB] to-[#1E40AF] flex items-center justify-center text-white text-sm font-bold shadow-sm">
          排
        </div>
        <div>
          <h1 class="text-[15px] font-bold text-[#5D4E2B] leading-tight">
            古城地下排水暗渠管理与风险分析系统
          </h1>
          <p class="text-[10px] text-gray-500 leading-tight mt-0.5">
            Ancient City Drainage Management & Risk Analysis
          </p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <div class="px-3 py-1.5 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9] text-xs text-[#5D4E2B]">
          当前暗渠：
          <span class="font-semibold text-[#2563EB]">{{ selectedCulvertName }}</span>
        </div>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <aside class="w-56 bg-white border-r border-[#E8DFC9] flex flex-col flex-shrink-0">
        <div class="p-3 border-b border-[#E8DFC9]">
          <div class="text-xs font-semibold text-gray-500 mb-2">暗渠列表</div>
          <div class="space-y-1 max-h-[300px] overflow-y-auto">
            <div
              v-for="culvert in culverts"
              :key="culvert.id"
              :class="[
                'px-3 py-2 rounded-lg cursor-pointer transition-all text-sm flex items-center justify-between',
                selectedCulvert?.id === culvert.id
                  ? 'bg-[#2563EB]/10 text-[#2563EB] font-medium'
                  : 'text-gray-700 hover:bg-gray-50'
              ]"
              @click="selectCulvert(culvert)"
            >
              <span class="flex items-center gap-2">
                <Droplets class="w-4 h-4" />
                <span class="truncate">{{ culvert.name }}</span>
              </span>
              <ChevronRight v-if="selectedCulvert?.id === culvert.id" class="w-4 h-4" />
            </div>
          </div>
        </div>

        <nav class="flex-1 p-3 space-y-1">
          <div
            v-for="tab in tabs"
            :key="tab.id"
            :class="[
              'w-full px-3 py-2.5 rounded-lg cursor-pointer transition-all flex items-center gap-3 text-sm',
              activeTab === tab.id
                ? 'bg-[#2563EB] text-white shadow-sm'
                : 'text-gray-700 hover:bg-gray-100'
            ]"
            @click="activeTab = tab.id"
          >
            <component :is="tab.icon" class="w-4 h-4" />
            <span>{{ tab.name }}</span>
          </div>
        </nav>

        <div class="p-3 border-t border-[#E8DFC9]">
          <button
            class="w-full py-2 px-3 bg-[#5D8A66] text-white text-sm rounded-lg hover:bg-[#4a6f52] transition-colors flex items-center justify-center gap-2"
            @click="loadCulverts"
          >
            刷新数据
          </button>
        </div>
      </aside>

      <main class="flex-1 overflow-hidden p-4">
        <div v-if="loading" class="w-full h-full flex items-center justify-center">
          <div class="text-gray-500">加载中...</div>
        </div>
        <div v-else class="w-full h-full overflow-auto">
          <CulvertList
            v-if="activeTab === 'list'"
            :culverts="culverts"
            :selected-culvert="selectedCulvert"
            @select="selectCulvert"
            @refresh="loadCulverts"
          />
          <DrainageAnalysis
            v-else-if="activeTab === 'drainage'"
            :culvert-id="selectedCulvert?.id"
          />
          <SedimentAnalysis
            v-else-if="activeTab === 'sediment'"
            :culvert-id="selectedCulvert?.id"
          />
          <RiskWarning
            v-else-if="activeTab === 'risk'"
            :culvert-id="selectedCulvert?.id"
          />
          <SchemeSimulation
            v-else-if="activeTab === 'simulation'"
            :culvert-id="selectedCulvert?.id"
          />
          <ProfileView
            v-else-if="activeTab === 'profile'"
            :culvert-id="selectedCulvert?.id"
          />
        </div>
      </main>
    </div>
  </div>
</template>
