<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Plus, Download, Trash2, Eye, BookOpen, ArrowLeft, Filter, ChevronDown, X } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { api } from '@/lib/api'
import { useProfileStore } from '@/stores/profile'
import type { CeramicVesselTemplate, ControlPoint } from '@/types'

const router = useRouter()
const store = useProfileStore()

const templates = ref<CeramicVesselTemplate[]>([])
const loading = ref(false)
const categories = ref<Record<string, string[]>>({})
const searchKeyword = ref('')
const filterCategory = ref('')
const filterDynasty = ref('')
const categoryExpanded = ref(true)
const showCreateModal = ref(false)
const selectedTemplate = ref<CeramicVesselTemplate | null>(null)
const showDetailModal = ref(false)
const applyScale = ref(1.0)
const applyTargetDim = ref<'height' | 'belly'>('height')
const applyTargetValue = ref<number>(0)

const allCategories = computed(() => Object.keys(categories.value || {}))
const allDynasties = computed(() => {
  const set = new Set<string>()
  Object.values(categories.value || {}).forEach(arr => arr.forEach(d => d && set.add(d)))
  templates.value.forEach(t => t.dynasty && set.add(t.dynasty))
  return Array.from(set)
})

const filteredTemplates = computed(() => {
  return templates.value.filter(t => {
    if (filterCategory.value && t.category !== filterCategory.value) return false
    if (filterDynasty.value && t.dynasty !== filterDynasty.value) return false
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      return (
        t.name.toLowerCase().includes(kw) ||
        t.code.toLowerCase().includes(kw) ||
        (t.description && t.description.toLowerCase().includes(kw))
      )
    }
    return true
  })
})

async function loadData() {
  loading.value = true
  try {
    templates.value = await api.templates.list()
    try {
      const catData = await api.templates.categories()
      categories.value = catData.categories || {}
    } catch (e) {
      const catMap: Record<string, string[]> = {}
      templates.value.forEach(t => {
        if (!catMap[t.category]) catMap[t.category] = []
        if (t.dynasty && !catMap[t.category].includes(t.dynasty)) {
          catMap[t.category].push(t.dynasty)
        }
      })
      categories.value = catMap
    }
  } catch (e) {
    console.error('加载模板失败', e)
  } finally {
    loading.value = false
  }
}

function countByCategory(cat: string) {
  return templates.value.filter(t => t.category === cat).length
}

function openDetail(tpl: CeramicVesselTemplate) {
  selectedTemplate.value = tpl
  showDetailModal.value = true
  if (tpl.typical_height) applyTargetValue.value = tpl.typical_height
}

function closeDetail() {
  showDetailModal.value = false
  selectedTemplate.value = null
}

function miniVesselPath(controlPoints: ControlPoint[] | undefined | null) {
  if (!controlPoints || controlPoints.length < 2) return ''
  const pts = controlPoints
  const maxX = Math.max(...pts.map(p => p.x), 1)
  const maxY = Math.max(...pts.map(p => p.y), 1)
  const sorted = [...pts].sort((a, b) => a.y - b.y)
  return sorted.map((p, i) => {
    const x = 18 + (p.x / maxX) * 16
    const y = 44 - (p.y / maxY) * 40
    return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
  }).join(' ') + ' L18,' + (44 - (sorted[0].y / maxY) * 40).toFixed(1) + ' Z'
}

async function applyTemplateToWorkspace() {
  if (!selectedTemplate.value) return
  try {
    const params: any = {}
    if (applyTargetDim.value === 'height' && applyTargetValue.value > 0) {
      params.target_height = applyTargetValue.value
    } else if (applyTargetDim.value === 'belly' && applyTargetValue.value > 0) {
      params.target_belly_diameter = applyTargetValue.value
    } else if (applyScale.value !== 1.0) {
      params.scale_factor = applyScale.value
    }
    let cps: ControlPoint[]
    if (Object.keys(params).length > 0) {
      const result = await api.templates.apply(selectedTemplate.value.id, params)
      cps = result.control_points
    } else {
      cps = selectedTemplate.value.control_points as ControlPoint[]
    }
    store.createNewScheme(`${selectedTemplate.value.name} - 应用`)
    store.replacePoints(cps.map(p => ({ x: p.x, y: p.y })))
    closeDetail()
    router.push('/')
  } catch (e: any) {
    alert('应用模板失败：' + (e?.message || '未知错误'))
  }
}

async function deleteTemplate(id: number) {
  if (!confirm('确定删除此模板？此操作不可恢复。')) return
  try {
    await api.templates.delete(id)
    templates.value = templates.value.filter(t => t.id !== id)
    if (selectedTemplate.value?.id === id) closeDetail()
  } catch (e: any) {
    alert('删除失败：' + (e?.message || '未知错误'))
  }
}

function exportTemplate(tpl: CeramicVesselTemplate) {
  const data = JSON.stringify({
    exportType: 'vessel_template',
    exportedAt: new Date().toISOString(),
    template: {
      name: tpl.name,
      code: tpl.code,
      category: tpl.category,
      dynasty: tpl.dynasty,
      region: tpl.region,
      material: tpl.material,
      control_points: tpl.control_points,
      description: tpl.description,
      references: tpl.references,
    }
  }, null, 2)
  const blob = new Blob([data], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `模板_${tpl.code}_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(loadData)
</script>

<template>
  <div class="w-screen h-screen flex flex-col overflow-hidden bg-[#F5F0E8]">
    <header class="h-14 flex items-center justify-between px-5 bg-white border-b border-[#E8DFC9] flex-shrink-0">
      <div class="flex items-center gap-3">
        <button
          class="p-1.5 rounded-lg hover:bg-[#F5F0E8] transition-colors"
          @click="router.push('/')"
        >
          <ArrowLeft class="w-5 h-5 text-[#5D4E2B]" />
        </button>
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#5D8A66] to-[#2E7D32] flex items-center justify-center text-white text-sm font-bold shadow-sm">
          模
        </div>
        <div>
          <h1 class="text-[15px] font-bold text-[#5D4E2B] leading-tight">
            标准器型模板库
          </h1>
          <p class="text-[10px] text-gray-500 leading-tight mt-0.5">
            Standard Vessel Type Template Library
          </p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <Search class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索名称/编号/描述..."
            class="pl-9 pr-4 py-1.5 text-xs border border-[#E8DFC9] rounded-lg w-64 focus:outline-none focus:border-[#5D8A66]"
          />
        </div>
        <button
          class="flex items-center gap-1.5 px-3 py-1.5 bg-[#5D8A66] text-white text-xs rounded-lg hover:bg-[#4a6f52] transition-colors"
          @click="showCreateModal = true"
        >
          <Plus class="w-4 h-4" />
          新建模板
        </button>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <aside class="w-60 flex-shrink-0 bg-white border-r border-[#E8DFC9] overflow-y-auto">
        <div class="p-3 border-b border-[#E8DFC9] bg-[#FAF6ED]">
          <h3 class="text-sm font-bold text-[#5D4E2B] flex items-center gap-2">
            <Filter class="w-4 h-4" />
            分类筛选
          </h3>
        </div>
        <div class="p-2">
          <div class="mb-3">
            <select
              v-model="filterCategory"
              class="w-full px-2 py-1.5 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#5D8A66]"
            >
              <option value="">全部分类</option>
              <option v-for="c in allCategories" :key="c" :value="c">
                {{ c }} ({{ countByCategory(c) }})
              </option>
            </select>
          </div>
          <div class="mb-3">
            <select
              v-model="filterDynasty"
              class="w-full px-2 py-1.5 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#5D8A66]"
            >
              <option value="">全部朝代</option>
              <option v-for="d in allDynasties" :key="d" :value="d">{{ d }}</option>
            </select>
          </div>
          <div class="pt-3 border-t border-[#E8DFC9]">
            <div
              class="flex items-center justify-between px-1 py-1 cursor-pointer hover:bg-[#FAF6ED] rounded"
              @click="categoryExpanded = !categoryExpanded"
            >
              <span class="text-xs font-semibold text-[#5D4E2B]">按分类浏览</span>
              <ChevronDown
                class="w-4 h-4 text-gray-400 transition-transform"
                :class="{ 'rotate-180': !categoryExpanded }"
              />
            </div>
            <div v-show="categoryExpanded" class="mt-1 space-y-1">
              <div
                v-for="c in allCategories"
                :key="c"
                class="flex items-center justify-between px-2 py-1 text-xs rounded cursor-pointer hover:bg-[#FAF6ED]"
                :class="{ 'bg-[#5D8A66]/10 text-[#5D8A66]': filterCategory === c }"
                @click="filterCategory = filterCategory === c ? '' : c"
              >
                <span class="truncate">{{ c }}</span>
                <span
                  class="px-1.5 py-0.5 rounded-full text-[10px]"
                  :class="filterCategory === c ? 'bg-[#5D8A66] text-white' : 'bg-gray-100 text-gray-500'"
                >{{ countByCategory(c) }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <main class="flex-1 overflow-y-auto p-4">
        <div v-if="loading" class="flex items-center justify-center h-64 text-gray-400 text-sm">
          加载中...
        </div>
        <div v-else-if="filteredTemplates.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-400">
          <BookOpen class="w-16 h-16 mb-3 opacity-30" />
          <p class="text-sm">暂无匹配的模板</p>
          <button
            class="mt-3 text-xs text-[#5D8A66] hover:underline"
            @click="searchKeyword = ''; filterCategory = ''; filterDynasty = ''"
          >清除筛选条件</button>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="tpl in filteredTemplates"
            :key="tpl.id"
            class="bg-white rounded-xl border border-[#E8DFC9] overflow-hidden hover:shadow-lg hover:border-[#5D8A66]/40 transition-all cursor-pointer group"
            @click="openDetail(tpl)"
          >
            <div class="h-36 bg-gradient-to-b from-[#FAF6ED] to-[#F5F0E8] flex items-center justify-center relative border-b border-[#E8DFC9]">
              <svg width="100" height="130" viewBox="0 0 36 50" class="transition-transform group-hover:scale-105">
                <path
                  :d="miniVesselPath(tpl.control_points as ControlPoint[])"
                  fill="#5D8A66"
                  fill-opacity="0.25"
                  stroke="#5D8A66"
                  stroke-width="0.8"
                />
              </svg>
              <div class="absolute top-2 left-2 px-2 py-0.5 bg-white/90 backdrop-blur rounded text-[10px] text-[#5D4E2B] border border-[#E8DFC9]">
                {{ tpl.category }}
              </div>
              <div v-if="tpl.dynasty" class="absolute top-2 right-2 px-2 py-0.5 bg-[#8B6914]/10 rounded text-[10px] text-[#8B6914]">
                {{ tpl.dynasty }}
              </div>
              <div class="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  class="p-1 bg-white rounded shadow-sm hover:bg-[#5D8A66] hover:text-white text-gray-500"
                  title="查看详情"
                  @click.stop="openDetail(tpl)"
                >
                  <Eye class="w-3.5 h-3.5" />
                </button>
                <button
                  class="p-1 bg-white rounded shadow-sm hover:bg-[#8B6914] hover:text-white text-gray-500"
                  title="导出"
                  @click.stop="exportTemplate(tpl)"
                >
                  <Download class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
            <div class="p-3">
              <h3 class="text-sm font-semibold text-[#5D4E2B] truncate mb-1">{{ tpl.name }}</h3>
              <p class="text-[10px] text-gray-400 mb-2">{{ tpl.code }}</p>
              <div class="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-gray-500">
                <div v-if="tpl.typical_height">
                  <span class="text-gray-400">通高</span>
                  <span class="text-[#5D4E2B] ml-1">{{ tpl.typical_height?.toFixed(0) }}mm</span>
                </div>
                <div v-if="tpl.typical_belly_diameter">
                  <span class="text-gray-400">腹径</span>
                  <span class="text-[#5D4E2B] ml-1">{{ tpl.typical_belly_diameter?.toFixed(0) }}mm</span>
                </div>
                <div v-if="tpl.typical_volume">
                  <span class="text-gray-400">容量</span>
                  <span class="text-[#5D8A66] ml-1">{{ (tpl.typical_volume / 1000).toFixed(1) }}L</span>
                </div>
                <div v-if="tpl.typical_mouth_diameter">
                  <span class="text-gray-400">口径</span>
                  <span class="text-[#5D4E2B] ml-1">{{ tpl.typical_mouth_diameter?.toFixed(0) }}mm</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <div
      v-if="showDetailModal && selectedTemplate"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      @click.self="closeDetail"
    >
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <div class="px-5 py-4 border-b border-[#E8DFC9] flex items-center justify-between bg-[#FAF6ED]">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-[#5D8A66] to-[#2E7D32] flex items-center justify-center text-white font-bold">
              模
            </div>
            <div>
              <h2 class="text-lg font-bold text-[#5D4E2B]">{{ selectedTemplate.name }}</h2>
              <p class="text-xs text-gray-500">{{ selectedTemplate.code }} · {{ selectedTemplate.category }} · {{ selectedTemplate.dynasty || '朝代未知' }}</p>
            </div>
          </div>
          <button class="p-2 rounded-lg hover:bg-white/60" @click="closeDetail">
            <X class="w-5 h-5 text-gray-400" />
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-5">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div class="bg-gradient-to-b from-[#FAF6ED] to-[#F5F0E8] rounded-xl border border-[#E8DFC9] p-4 flex flex-col items-center justify-center">
              <svg width="200" height="260" viewBox="0 0 72 100" class="mb-3">
                <path
                  d="M36,98 L36,40 M72,40 L0,40"
                  stroke="#8B6914"
                  stroke-width="0.3"
                  stroke-dasharray="1,1"
                  fill="none"
                />
                <path
                  :d="(() => {
                    const pts = (selectedTemplate.control_points as ControlPoint[]) || []
                    if (pts.length < 2) return ''
                    const maxX = Math.max(...pts.map(p => p.x), 1)
                    const maxY = Math.max(...pts.map(p => p.y), 1)
                    const sorted = [...pts].sort((a, b) => a.y - b.y)
                    return sorted.map((p, i) => {
                      const x = 36 + (p.x / maxX) * 32
                      const y = 90 - (p.y / maxY) * 85
                      return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
                    }).join(' ') + ' L36,' + (90 - (sorted[0].y / maxY) * 85).toFixed(1) + ' Z'
                  })()"
                  fill="#5D8A66"
                  fill-opacity="0.2"
                  stroke="#5D8A66"
                  stroke-width="1.5"
                />
              </svg>
              <div class="w-full space-y-2 text-xs">
                <div class="flex justify-between px-3">
                  <span class="text-gray-500">控制点数量</span>
                  <span class="font-semibold text-[#5D4E2B]">{{ (selectedTemplate.control_points as any[])?.length || 0 }}</span>
                </div>
              </div>
            </div>
            <div class="space-y-4">
              <div>
                <h4 class="text-sm font-bold text-[#5D4E2B] mb-2 flex items-center gap-2">
                  <span class="inline-block w-1 h-4 bg-[#5D8A66] rounded"></span>
                  典型尺寸
                </h4>
                <div class="grid grid-cols-2 gap-2">
                  <div class="p-2.5 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
                    <div class="text-[10px] text-gray-500 mb-0.5">通高</div>
                    <div class="text-base font-bold text-[#5D4E2B]">{{ selectedTemplate.typical_height?.toFixed(1) || '--' }}<span class="text-xs font-normal text-gray-400 ml-1">mm</span></div>
                  </div>
                  <div class="p-2.5 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
                    <div class="text-[10px] text-gray-500 mb-0.5">口径</div>
                    <div class="text-base font-bold text-[#5D4E2B]">{{ selectedTemplate.typical_mouth_diameter?.toFixed(1) || '--' }}<span class="text-xs font-normal text-gray-400 ml-1">mm</span></div>
                  </div>
                  <div class="p-2.5 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
                    <div class="text-[10px] text-gray-500 mb-0.5">腹径</div>
                    <div class="text-base font-bold text-[#5D4E2B]">{{ selectedTemplate.typical_belly_diameter?.toFixed(1) || '--' }}<span class="text-xs font-normal text-gray-400 ml-1">mm</span></div>
                  </div>
                  <div class="p-2.5 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
                    <div class="text-[10px] text-gray-500 mb-0.5">容量</div>
                    <div class="text-base font-bold text-[#5D8A66]">
                      {{ selectedTemplate.typical_volume != null ? (selectedTemplate.typical_volume < 1000 ? selectedTemplate.typical_volume.toFixed(0) + 'ml' : (selectedTemplate.typical_volume/1000).toFixed(2) + 'L') : '--' }}
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="selectedTemplate.description">
                <h4 class="text-sm font-bold text-[#5D4E2B] mb-2 flex items-center gap-2">
                  <span class="inline-block w-1 h-4 bg-[#8B6914] rounded"></span>
                  器型描述
                </h4>
                <p class="text-xs text-gray-600 leading-relaxed bg-[#FAF6ED] p-3 rounded-lg border border-[#E8DFC9]">{{ selectedTemplate.description }}</p>
              </div>
              <div v-if="selectedTemplate.references">
                <h4 class="text-sm font-bold text-[#5D4E2B] mb-2 flex items-center gap-2">
                  <span class="inline-block w-1 h-4 bg-[#1565C0] rounded"></span>
                  参考文献
                </h4>
                <p class="text-xs text-gray-500 italic">{{ selectedTemplate.references }}</p>
              </div>
              <div class="pt-2">
                <h4 class="text-sm font-bold text-[#5D4E2B] mb-2 flex items-center gap-2">
                  <span class="inline-block w-1 h-4 bg-[#E65100] rounded"></span>
                  应用到工作台
                </h4>
                <div class="p-3 bg-[#E65100]/5 rounded-lg border border-[#E65100]/20 space-y-2">
                  <div class="flex items-center gap-2 text-xs">
                    <label class="flex items-center gap-1">
                      <input type="radio" v-model="applyTargetDim" value="height" class="accent-[#E65100]" />
                      按目标高度
                    </label>
                    <label class="flex items-center gap-1">
                      <input type="radio" v-model="applyTargetDim" value="belly" class="accent-[#E65100]" />
                      按目标腹径
                    </label>
                  </div>
                  <div class="flex gap-2 items-center">
                    <input
                      v-model.number="applyTargetValue"
                      type="number"
                      step="1"
                      class="flex-1 px-3 py-1.5 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#E65100]"
                      :placeholder="applyTargetDim === 'height' ? '目标高度 (mm)' : '目标腹径 (mm)'"
                    />
                    <span class="text-[10px] text-gray-400">或缩放</span>
                    <input
                      v-model.number="applyScale"
                      type="number"
                      step="0.05"
                      min="0.1"
                      max="5"
                      class="w-20 px-3 py-1.5 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#E65100]"
                      placeholder="倍数"
                    />
                  </div>
                  <div class="flex gap-2 pt-1">
                    <button
                      class="flex-1 py-2 bg-[#E65100] text-white text-sm rounded-lg hover:bg-[#BF360C] transition-colors font-medium"
                      @click="applyTemplateToWorkspace"
                    >应用并打开工作台</button>
                    <button
                      class="px-3 py-2 bg-white text-[#5D4E2B] text-sm rounded-lg hover:bg-[#FAF6ED] transition-colors border border-[#E8DFC9]"
                      @click="exportTemplate(selectedTemplate)"
                    >
                      <Download class="w-4 h-4" />
                    </button>
                    <button
                      v-if="!selectedTemplate.created_by || selectedTemplate.created_by !== 'system'"
                      class="px-3 py-2 bg-red-50 text-red-500 text-sm rounded-lg hover:bg-red-100 transition-colors border border-red-100"
                      @click="deleteTemplate(selectedTemplate.id)"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
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
