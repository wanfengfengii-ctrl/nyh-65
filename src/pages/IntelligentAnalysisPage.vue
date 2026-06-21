<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ArrowLeft, Scaling, Activity, FileText, Layers, Target, Sparkles, Flame, Download, X, ChevronDown, Eye } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { api } from '@/lib/api'
import { useProfileStore } from '@/stores/profile'
import type { ControlPoint, VesselProfile, CeramicVesselTemplate, HeatmapPoint, KeyDifference, DifferenceAnalysisResult, ReportGenerationResult, ResearchReport, KeyPart, ParametricEditResult } from '@/types'

const router = useRouter()
const store = useProfileStore()

const activeTab = ref<'parametric' | 'differences' | 'reports'>('parametric')
const previewControlPoints = ref<ControlPoint[]>([])
const profileBeforeEdit = ref<ControlPoint[]>([])

function syncPreview() {
  previewControlPoints.value = (store.controlPoints as ControlPoint[])?.map(p => ({ ...p })) || []
  profileBeforeEdit.value = JSON.parse(JSON.stringify(previewControlPoints.value))
}
onMounted(syncPreview)

const dimOptions = [
  { key: 'height', label: '通高', unit: 'mm', desc: '整体高度等比缩放' },
  { key: 'mouth_diameter', label: '口径', unit: 'mm', desc: '口沿区域加权缩放（保持颈部自然过渡）' },
  { key: 'belly_diameter', label: '腹径', unit: 'mm', desc: '腹部区域高斯衰减加权缩放' },
  { key: 'bottom_diameter', label: '底径', unit: 'mm', desc: '底部区域加权缩放（保持圈足过渡）' },
  { key: 'volume', label: '容量', unit: 'ml', desc: '按立方根体积整体缩放' },
]
const selectedDim = ref('height')
const targetValue = ref<number>(0)
const preserveProportions = ref(true)
const currentOriginal = computed(() => {
  const dims = (store as any).lastCalculatedDimensions || {}
  const labelMap: Record<string, string> = { height: 'height', mouth_diameter: 'mouth_diameter', belly_diameter: 'belly_diameter', bottom_diameter: 'bottom_diameter', volume: 'volume' }
  return dims[labelMap[selectedDim.value]] || 0
})
const parametricResult = ref<ParametricEditResult | null>(null)
const parametricLoading = ref(false)

const profileListA = ref<VesselProfile[]>([])
const profileListB = ref<VesselProfile[]>([])
const templateList = ref<CeramicVesselTemplate[]>([])
const selA = ref<'workspace' | number>('workspace')
const selB = ref<'workspace' | number>('workspace')
const selAUseTemplate = ref(false)
const selBUseTemplate = ref(false)
const selATemplate = ref<number | null>(null)
const selBTemplate = ref<number | null>(null)
const sampleCount = ref(200)
const diffResult = ref<DifferenceAnalysisResult | null>(null)
const diffLoading = ref(false)

const reports = ref<ResearchReport[]>([])
const selectedProfileForReport = ref<number | null>(null)
const reportProfileList = ref<VesselProfile[]>([])
const reportType = ref<'standard' | 'conservation' | 'comparative' | 'typology'>('standard')
const reportAuthor = ref('')
const reportCustomTitle = ref('')
const reportKeywords = ref('')
const includeSections = ref<string[]>(['basic', 'profile', 'dimensions', 'key_parts', 'volume', 'restoration', 'template_match', 'conclusion'])
const sectionOptions = [
  { key: 'basic', label: '基本信息' },
  { key: 'profile', label: '剖面描述' },
  { key: 'dimensions', label: '尺寸分析' },
  { key: 'key_parts', label: '关键部位分析' },
  { key: 'volume', label: '容量估算' },
  { key: 'restoration', label: '复原评估' },
  { key: 'template_match', label: '模板对比' },
  { key: 'conclusion', label: '研究结论' },
]
const generatingReport = ref(false)
const lastGenerated = ref<ReportGenerationResult | null>(null)
const showReportDetail = ref(false)
const reportDetail = ref<any>(null)

async function doParametricEdit() {
  if (!previewControlPoints.value.length || !targetValue.value) return
  parametricLoading.value = true
  parametricResult.value = null
  try {
    const result = await api.vesselProfiles.parametricEdit({
      control_points: profileBeforeEdit.value,
      dimension_type: selectedDim.value,
      target_value: targetValue.value,
      preserve_proportions: preserveProportions.value,
    })
    parametricResult.value = result
    previewControlPoints.value = result.control_points
  } catch (e: any) {
    alert('参数化编辑失败：' + (e?.message || '未知错误'))
  } finally {
    parametricLoading.value = false
  }
}

function applyEditToWorkspace() {
  if (!parametricResult.value) return
  store.replacePoints(parametricResult.value.control_points)
  alert('已应用到工作台')
}

function resetParametric() {
  previewControlPoints.value = JSON.parse(JSON.stringify(profileBeforeEdit.value))
  parametricResult.value = null
  targetValue.value = currentOriginal.value > 0 ? currentOriginal.value : 0
}

watch(selectedDim, () => {
  targetValue.value = currentOriginal.value > 0 ? currentOriginal.value : 0
})

async function loadProfileLists() {
  try {
    profileListA.value = await api.vesselProfiles.list()
    profileListB.value = profileListA.value
    templateList.value = await api.templates.list()
    reportProfileList.value = profileListA.value
    reports.value = await api.ceramicAnalysis.reports.list()
  } catch (e) { console.error(e) }
}
onMounted(loadProfileLists)

function getCPsOf(which: 'A' | 'B'): ControlPoint[] {
  if (which === 'A') {
    if (selAUseTemplate.value && selATemplate.value) {
      const tpl = templateList.value.find(t => t.id === selATemplate.value)
      return (tpl?.control_points as ControlPoint[]) || []
    }
    if (selA.value === 'workspace') return (store.controlPoints as ControlPoint[]) || []
    const p = profileListA.value.find(x => x.id === selA.value)
    return (p as any)?.control_points || (p as any)?.profile_data?.control_points || []
  } else {
    if (selBUseTemplate.value && selBTemplate.value) {
      const tpl = templateList.value.find(t => t.id === selBTemplate.value)
      return (tpl?.control_points as ControlPoint[]) || []
    }
    if (selB.value === 'workspace') return (store.controlPoints as ControlPoint[]) || []
    const p = profileListB.value.find(x => x.id === selB.value)
    return (p as any)?.control_points || (p as any)?.profile_data?.control_points || []
  }
}

function getNameOf(which: 'A' | 'B'): string {
  if (which === 'A') {
    if (selAUseTemplate.value && selATemplate.value) {
      return templateList.value.find(t => t.id === selATemplate.value)?.name || '模板A'
    }
    if (selA.value === 'workspace') return '当前工作台剖面'
    return profileListA.value.find(x => x.id === selA.value)?.name || '档案A'
  } else {
    if (selBUseTemplate.value && selBTemplate.value) {
      return templateList.value.find(t => t.id === selBTemplate.value)?.name || '模板B'
    }
    if (selB.value === 'workspace') return '当前工作台剖面'
    return profileListB.value.find(x => x.id === selB.value)?.name || '档案B'
  }
}

async function doDifferenceAnalysis() {
  const a = getCPsOf('A')
  const b = getCPsOf('B')
  if (a.length < 2 || b.length < 2) {
    alert('请先准备两个器型的控制点数据')
    return
  }
  diffLoading.value = true
  diffResult.value = null
  try {
    diffResult.value = await api.ceramicAnalysis.differenceAnalysis({
      profile_a_control_points: a,
      profile_b_control_points: b,
      profile_a_name: getNameOf('A'),
      profile_b_name: getNameOf('B'),
      sample_count: sampleCount.value,
    })
  } catch (e: any) {
    alert('差异分析失败：' + (e?.message || '未知错误'))
  } finally {
    diffLoading.value = false
  }
}

function heatColor(val: number, max: number) {
  const t = Math.min(1, Math.abs(val) / Math.max(max, 0.01))
  if (val >= 0) {
    const r = Math.floor(255 * Math.min(1, t * 1.5))
    const g = Math.floor(200 * (1 - t))
    const b = Math.floor(100 * (1 - t))
    return `rgb(${r},${g},${b})`
  } else {
    const r = Math.floor(100 * (1 - t))
    const g = Math.floor(180 * (1 - t * 0.5))
    const b = Math.floor(255 * Math.min(1, t * 1.5))
    return `rgb(${r},${g},${b})`
  }
}

const maxDiff = computed(() => {
  if (!diffResult.value) return 0
  return Math.max(...diffResult.value.heatmap_data.map(p => Math.abs(p.diameter_diff)), 0.001)
})

function similarityLabel(s: number) {
  if (s >= 0.9) return { text: '极高', cls: 'text-green-600 bg-green-100' }
  if (s >= 0.75) return { text: '较高', cls: 'text-emerald-600 bg-emerald-100' }
  if (s >= 0.55) return { text: '中等', cls: 'text-yellow-600 bg-yellow-100' }
  if (s >= 0.3) return { text: '较低', cls: 'text-orange-600 bg-orange-100' }
  return { text: '极低', cls: 'text-red-600 bg-red-100' }
}

async function doGenerateReport() {
  if (!selectedProfileForReport.value) { alert('请选择目标器型档案'); return }
  generatingReport.value = true
  lastGenerated.value = null
  try {
    const kw = reportKeywords.value.split(/[,，\s]+/).filter(Boolean)
    const result = await api.ceramicAnalysis.generateReport({
      profile_id: selectedProfileForReport.value,
      report_type: reportType.value,
      include_sections: includeSections.value,
      author: reportAuthor.value || undefined,
      keywords: kw.length ? kw : undefined,
      custom_title: reportCustomTitle.value || undefined,
    })
    lastGenerated.value = result
    await loadReportList()
  } catch (e: any) {
    alert('报告生成失败：' + (e?.message || '未知错误'))
  } finally {
    generatingReport.value = false
  }
}

async function loadReportList() {
  reports.value = await api.ceramicAnalysis.reports.list(selectedProfileForReport.value ? { profile_id: selectedProfileForReport.value } : undefined)
}
watch(selectedProfileForReport, () => loadReportList())

async function viewReport(r: ResearchReport) {
  try {
    reportDetail.value = await api.ceramicAnalysis.reports.get(r.id)
    showReportDetail.value = true
  } catch (e: any) { alert('加载报告失败：' + (e?.message || '未知错误')) }
}

function downloadReport(r: ResearchReport, format: 'json' | 'csv' = 'json') {
  const url = api.ceramicAnalysis.reports.export(r.id, format)
  const a = document.createElement('a')
  a.href = url
  a.download = `报告_${r.report_code || r.id}_${Date.now()}.${format}`
  a.target = '_blank'
  a.click()
}

function miniProfilePath(cps: ControlPoint[], w = 36, h = 50, offsetX = 18) {
  if (!cps?.length) return ''
  const maxX = Math.max(...cps.map(p => p.x), 1)
  const maxY = Math.max(...cps.map(p => p.y), 1)
  const sorted = [...cps].sort((a, b) => a.y - b.y)
  return sorted.map((p, i) => {
    const x = offsetX + (p.x / maxX) * (w / 2 - 2)
    const y = h - 3 - (p.y / maxY) * (h - 6)
    return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
  }).join(' ') + ' L' + offsetX + ',' + (h - 3 - (sorted[0].y / maxY) * (h - 6)).toFixed(1) + ' Z'
}

function parametricPreviewPath(cps: ControlPoint[], w = 160, h = 220, offsetX = 80) {
  if (!cps?.length) return ''
  const maxX = Math.max(...cps.map(p => p.x), 1)
  const maxY = Math.max(...cps.map(p => p.y), 1)
  const sorted = [...cps].sort((a, b) => a.y - b.y)
  return sorted.map((p, i) => {
    const x = offsetX + (p.x / maxX) * (w / 2 - 8)
    const y = h - 10 - (p.y / maxY) * (h - 20)
    return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
  }).join(' ')
}
</script>

<template>
  <div class="w-screen h-screen flex flex-col overflow-hidden bg-[#F5F0E8]">
    <header class="h-14 flex items-center justify-between px-5 bg-white border-b border-[#E8DFC9] flex-shrink-0">
      <div class="flex items-center gap-3">
        <button class="p-1.5 rounded-lg hover:bg-[#F5F0E8]" @click="router.push('/')">
          <ArrowLeft class="w-5 h-5 text-[#5D4E2B]" />
        </button>
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#7B1FA2] to-[#4A148C] flex items-center justify-center text-white text-sm font-bold shadow-sm">智</div>
        <div>
          <h1 class="text-[15px] font-bold text-[#5D4E2B] leading-tight">器型智能分析中心</h1>
          <p class="text-[10px] text-gray-500 leading-tight mt-0.5">Intelligent Ceramic Vessel Analysis Suite</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-for="t in [{ k: 'parametric', label: '参数化联动', icon: Scaling, cls: 'from-[#5D8A66] to-[#2E7D32]' },
            { k: 'differences', label: '差异热区', icon: Flame, cls: 'from-[#E65100] to-[#BF360C]' },
            { k: 'reports', label: '研究报告', icon: FileText, cls: 'from-[#1565C0] to-[#0D47A1]' }]" :key="t.k"
          :class="['flex items-center gap-1.5 px-3.5 py-1.5 text-xs rounded-lg transition-all font-medium', activeTab === t.k ? `bg-gradient-to-r ${t.cls} text-white shadow-md` : 'bg-white text-[#5D4E2B] border border-[#E8DFC9] hover:bg-[#FAF6ED]']"
          @click="activeTab = t.k as any"
        >
          <component :is="t.icon" class="w-4 h-4" />{{ t.label }}
        </button>
      </div>
    </header>

    <main class="flex-1 overflow-y-auto p-4">
      <section v-show="activeTab === 'parametric'" class="grid grid-cols-1 lg:grid-cols-5 gap-4 h-full">
        <div class="lg:col-span-2 bg-white rounded-xl border border-[#E8DFC9] p-5 space-y-4">
          <div>
            <h2 class="text-base font-bold text-[#5D4E2B] flex items-center gap-2">
              <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-[#5D8A66] to-[#2E7D32] flex items-center justify-center text-white"><Scaling class="w-5 h-5" /></div>
              参数化尺寸联动编辑
            </h2>
            <p class="text-xs text-gray-500 mt-1 ml-11">调整单个尺寸参数，实现整体器型比例联动变化</p>
          </div>
          <div class="space-y-3 pt-2">
            <div>
              <label class="text-xs font-semibold text-gray-600 mb-1.5 block">目标尺寸参数</label>
              <div class="grid grid-cols-5 gap-1.5">
                <button v-for="d in dimOptions" :key="d.key"
                  :class="['py-2 text-[11px] rounded-lg border font-medium transition-all', selectedDim === d.key ? 'bg-[#5D8A66] text-white border-[#5D8A66] shadow-sm' : 'bg-white text-[#5D4E2B] border-[#E8DFC9] hover:border-[#5D8A66] hover:bg-[#5D8A66]/5']"
                  @click="selectedDim = d.key"
                >{{ d.label }}</button>
              </div>
              <p class="text-[10px] text-gray-400 mt-1">{{ dimOptions.find(d => d.key === selectedDim)?.desc }}</p>
            </div>
            <div>
              <label class="text-xs font-semibold text-gray-600 mb-1.5 block">目标值（{{ dimOptions.find(d => d.key === selectedDim)?.unit }}）</label>
              <div class="flex gap-2">
                <input v-model.number="targetValue" type="number" step="1" class="flex-1 px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#5D8A66]" />
                <button class="px-3 py-2 text-xs text-gray-500 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9] hover:bg-[#F5F0E8]" @click="resetParametric">
                  原值
                </button>
              </div>
              <p class="text-[10px] text-gray-400 mt-1">
                当前测量: <span class="text-[#5D8A66] font-semibold">{{ currentOriginal ? currentOriginal.toFixed(2) + ' ' + dimOptions.find(d => d.key === selectedDim)?.unit : '（在工作台测量）' }}</span>
                <span v-if="currentOriginal && targetValue">
                  · 变化率: <span :class="targetValue > currentOriginal ? 'text-red-500' : 'text-blue-500'">
                    {{ targetValue > currentOriginal ? '+' : '' }}{{ ((targetValue - currentOriginal) / currentOriginal * 100).toFixed(1) }}%
                  </span>
                </span>
              </p>
            </div>
            <div v-if="parametricResult" class="p-3 bg-green-50 border border-green-200 rounded-lg">
              <div class="text-xs font-semibold text-green-700 mb-1 flex items-center gap-1"><Sparkles class="w-4 h-4" />编辑成功</div>
              <div class="grid grid-cols-2 gap-2 text-[11px]">
                <div><span class="text-gray-500">缩放系数</span> <span class="font-semibold text-[#5D4E2B]">{{ (parametricResult.scale_applied ?? 1).toFixed(4) }}</span></div>
                <div><span class="text-gray-500">控制点</span> <span class="font-semibold text-[#5D4E2B]">{{ parametricResult.control_points.length }}</span></div>
                <div v-if="(parametricResult.new_dimensions || parametricResult.dimensions)?.height"><span class="text-gray-500">新高</span> <span class="font-semibold text-[#5D4E2B]">{{ ((parametricResult.new_dimensions || parametricResult.dimensions) as any)?.height?.toFixed(1) }}mm</span></div>
                <div v-if="(parametricResult.new_dimensions || parametricResult.dimensions)?.bellyDiameter"><span class="text-gray-500">新腹径</span> <span class="font-semibold text-[#5D4E2B]">{{ ((parametricResult.new_dimensions || parametricResult.dimensions) as any)?.bellyDiameter?.toFixed(1) }}mm</span></div>
                <div v-if="(parametricResult.new_dimensions || parametricResult.dimensions)?.volume" class="col-span-2"><span class="text-gray-500">新容量</span> <span class="font-semibold text-[#5D8A66]">{{ (((parametricResult.new_dimensions || parametricResult.dimensions) as any)?.volume < 1000 ? ((parametricResult.new_dimensions || parametricResult.dimensions) as any)?.volume.toFixed(0) + 'ml' : (((parametricResult.new_dimensions || parametricResult.dimensions) as any)?.volume/1000).toFixed(2) + 'L') }}</span></div>
              </div>
            </div>
            <div class="flex items-center gap-2 text-xs">
              <input type="checkbox" id="preserve" v-model="preserveProportions" class="accent-[#5D8A66]" />
              <label for="preserve" class="text-gray-600">保持非目标区域比例（推荐）</label>
            </div>
            <div class="flex gap-2 pt-2">
              <button :disabled="!targetValue || parametricLoading" class="flex-1 py-2.5 bg-[#5D8A66] text-white text-sm font-medium rounded-lg hover:bg-[#4a6f52] disabled:opacity-40 disabled:cursor-not-allowed" @click="doParametricEdit">
                {{ parametricLoading ? '计算中...' : '执行联动编辑' }}
              </button>
              <button :disabled="!parametricResult" class="px-4 py-2.5 bg-[#1565C0] text-white text-sm rounded-lg hover:bg-[#0D47A1] disabled:opacity-40" @click="applyEditToWorkspace">应用到工作台</button>
            </div>
          </div>
        </div>

        <div class="lg:col-span-3 bg-white rounded-xl border border-[#E8DFC9] p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-bold text-[#5D4E2B] flex items-center gap-2"><Eye class="w-4 h-4" />联动预览（编辑前后对比）</h3>
            <div class="flex items-center gap-3 text-[10px]">
              <span class="flex items-center gap-1"><span class="w-3 h-3 rounded" style="background: rgba(139,105,20,0.25); border:1.5px solid #8B6914;"></span>编辑前</span>
              <span class="flex items-center gap-1"><span class="w-3 h-3 rounded" style="background: rgba(93,138,102,0.25); border:1.5px solid #5D8A66;"></span>编辑后</span>
            </div>
          </div>
          <div class="h-[520px] bg-gradient-to-b from-[#FAF6ED] to-[#F5F0E8] rounded-lg border border-[#E8DFC9] flex items-center justify-center">
            <svg width="100%" height="100%" viewBox="0 0 340 540" style="max-width:340px;">
              <defs>
                <pattern id="grid2" width="20" height="20" patternUnits="userSpaceOnUse">
                  <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#E8DFC9" stroke-width="0.5" />
                </pattern>
              </defs>
              <rect width="340" height="540" fill="url(#grid2)" />
              <line x1="170" y1="20" x2="170" y2="520" stroke="#8B6914" stroke-width="0.5" stroke-dasharray="3,3" />
              <path :d="parametricPreviewPath(profileBeforeEdit, 340, 540, 85)" fill="rgba(139,105,20,0.12)" stroke="#8B6914" stroke-width="1.5" stroke-dasharray="4,2" />
              <path :d="parametricPreviewPath(previewControlPoints, 340, 540, 255)" fill="rgba(93,138,102,0.18)" stroke="#5D8A66" stroke-width="1.5" />
              <g font-size="9" fill="#8B6914" text-anchor="middle">
                <text x="85" y="536">原始</text>
                <text x="255" y="536">联动后</text>
              </g>
            </svg>
          </div>
        </div>
      </section>

      <section v-show="activeTab === 'differences'" class="space-y-4">
        <div class="bg-white rounded-xl border border-[#E8DFC9] p-5">
          <h2 class="text-base font-bold text-[#5D4E2B] flex items-center gap-2 mb-4">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-[#E65100] to-[#BF360C] flex items-center justify-center text-white"><Flame class="w-5 h-5" /></div>
            器型差异热区分析
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="p-4 bg-gradient-to-br from-[#1565C0]/5 to-[#1565C0]/10 rounded-xl border border-[#1565C0]/20">
              <h3 class="text-xs font-bold text-[#1565C0] mb-2 flex items-center gap-1"><Target class="w-4 h-4" />基准剖面 A</h3>
              <label class="flex items-center gap-1.5 text-[11px] text-gray-600 mb-2">
                <input type="checkbox" v-model="selAUseTemplate" class="accent-[#1565C0]" />使用标准器型模板
              </label>
              <select v-if="!selAUseTemplate" v-model="selA" class="w-full px-2.5 py-2 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#1565C0]">
                <option value="workspace">— 当前工作台剖面 —</option>
                <optgroup label="器型档案">
                  <option v-for="p in profileListA" :key="p.id" :value="p.id">{{ p.name }} ({{ p.code || p.id }})</option>
                </optgroup>
              </select>
              <select v-else v-model="selATemplate" class="w-full px-2.5 py-2 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#1565C0]">
                <option :value="null">— 请选择模板 —</option>
                <option v-for="t in templateList" :key="t.id" :value="t.id">{{ t.name }} ({{ t.code }})</option>
              </select>
              <div class="mt-3 h-24 bg-white rounded-lg border border-[#1565C0]/10 flex items-center justify-center">
                <svg width="80" height="90" viewBox="0 0 36 50">
                  <path :d="miniProfilePath(getCPsOf('A'))" fill="#1565C0" fill-opacity="0.2" stroke="#1565C0" stroke-width="0.8" />
                </svg>
              </div>
            </div>

            <div class="flex flex-col items-center justify-center">
              <div class="w-14 h-14 rounded-full bg-gradient-to-br from-[#E65100] to-[#BF360C] flex items-center justify-center text-white font-bold text-lg shadow-lg mb-2">VS</div>
              <button :disabled="diffLoading" class="px-4 py-2 bg-[#E65100] text-white text-xs font-medium rounded-lg hover:bg-[#BF360C] shadow-md disabled:opacity-50" @click="doDifferenceAnalysis">
                {{ diffLoading ? '分析中...' : '执行差异对比' }}
              </button>
              <div class="mt-3 w-full max-w-[200px]">
                <label class="text-[10px] text-gray-500 mb-1 block">采样精度：{{ sampleCount }} 点</label>
                <input v-model.number="sampleCount" type="range" min="50" max="500" step="10" class="w-full accent-[#E65100]" />
              </div>
            </div>

            <div class="p-4 bg-gradient-to-br from-[#7B1FA2]/5 to-[#7B1FA2]/10 rounded-xl border border-[#7B1FA2]/20">
              <h3 class="text-xs font-bold text-[#7B1FA2] mb-2 flex items-center gap-1"><Target class="w-4 h-4" />对比剖面 B</h3>
              <label class="flex items-center gap-1.5 text-[11px] text-gray-600 mb-2">
                <input type="checkbox" v-model="selBUseTemplate" class="accent-[#7B1FA2]" />使用标准器型模板
              </label>
              <select v-if="!selBUseTemplate" v-model="selB" class="w-full px-2.5 py-2 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#7B1FA2]">
                <option value="workspace">— 当前工作台剖面 —</option>
                <optgroup label="器型档案">
                  <option v-for="p in profileListB" :key="p.id" :value="p.id">{{ p.name }} ({{ p.code || p.id }})</option>
                </optgroup>
              </select>
              <select v-else v-model="selBTemplate" class="w-full px-2.5 py-2 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#7B1FA2]">
                <option :value="null">— 请选择模板 —</option>
                <option v-for="t in templateList" :key="t.id" :value="t.id">{{ t.name }} ({{ t.code }})</option>
              </select>
              <div class="mt-3 h-24 bg-white rounded-lg border border-[#7B1FA2]/10 flex items-center justify-center">
                <svg width="80" height="90" viewBox="0 0 36 50">
                  <path :d="miniProfilePath(getCPsOf('B'))" fill="#7B1FA2" fill-opacity="0.2" stroke="#7B1FA2" stroke-width="0.8" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div v-if="diffResult" class="grid grid-cols-1 xl:grid-cols-5 gap-4">
          <div class="xl:col-span-2 bg-white rounded-xl border border-[#E8DFC9] p-5">
            <h3 class="text-sm font-bold text-[#5D4E2B] mb-3 flex items-center gap-2"><Activity class="w-4 h-4" />总体相似度</h3>
            <div class="flex items-center gap-5 mb-4">
              <div class="relative w-32 h-32">
                <svg width="128" height="128" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="44" fill="none" stroke="#E8DFC9" stroke-width="8" />
                  <circle cx="50" cy="50" r="44" fill="none" :stroke="diffResult.overall_similarity >= 0.75 ? '#22c55e' : diffResult.overall_similarity >= 0.5 ? '#eab308' : '#ef4444'" stroke-width="8" stroke-linecap="round"
                    :stroke-dasharray="(2 * Math.PI * 44)" :stroke-dashoffset="(2 * Math.PI * 44) * (1 - diffResult.overall_similarity)" transform="rotate(-90 50 50)" />
                </svg>
                <div class="absolute inset-0 flex flex-col items-center justify-center">
                  <div class="text-3xl font-bold text-[#5D4E2B]">{{ (diffResult.overall_similarity * 100).toFixed(1) }}</div>
                  <div class="text-[10px] text-gray-500">%</div>
                </div>
              </div>
              <div class="flex-1 space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs text-gray-500">相似度评级</span>
                  <span :class="['px-2.5 py-0.5 text-xs font-bold rounded-full', similarityLabel(diffResult.overall_similarity).cls]">{{ similarityLabel(diffResult.overall_similarity).text }}</span>
                </div>
                <div class="text-xs text-gray-600"><span class="font-semibold text-[#1565C0]">{{ diffResult.profile_a_name || 'A' }}</span> vs <span class="font-semibold text-[#7B1FA2]">{{ diffResult.profile_b_name || 'B' }}</span></div>
                <div class="space-y-1 pt-2">
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] text-gray-500 w-24">平均直径差</span>
                    <span class="text-xs font-bold text-[#5D4E2B]">{{ diffResult.statistics?.mean_diameter_diff?.toFixed(2) || '--' }}mm</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] text-gray-500 w-24">最大直径差</span>
                    <span class="text-xs font-bold text-red-500">{{ diffResult.statistics?.max_diameter_diff?.toFixed(2) || '--' }}mm</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] text-gray-500 w-24">高度偏差</span>
                    <span class="text-xs font-bold text-[#5D4E2B]">{{ diffResult.statistics?.height_diff_pct?.toFixed(2) || '--' }}%</span>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <h4 class="text-xs font-bold text-[#5D4E2B] mb-2">🔍 关键差异区段（Top {{ Math.min(5, diffResult.key_differences.length) }}）</h4>
              <div class="space-y-1.5 max-h-[320px] overflow-y-auto">
                <div v-for="(kd, i) in diffResult.key_differences.slice(0, 8)" :key="i" class="p-2.5 rounded-lg border"
                  :class="kd.severity === 'high' ? 'bg-red-50 border-red-200' : kd.severity === 'medium' ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'"
                >
                  <div class="flex items-center justify-between mb-0.5">
                    <span class="text-xs font-semibold text-[#5D4E2B]">{{ kd.section_name }}</span>
                    <span :class="['text-[10px] font-bold px-1.5 py-0.5 rounded', kd.severity === 'high' ? 'bg-red-500 text-white' : kd.severity === 'medium' ? 'bg-yellow-500 text-white' : 'bg-gray-400 text-white']">
                      {{ kd.severity === 'high' ? '高' : kd.severity === 'medium' ? '中' : '低' }}
                    </span>
                  </div>
                  <div class="text-[10px] text-gray-500">
                    高度: {{ kd.height_start?.toFixed(1) }}–{{ kd.height_end?.toFixed(1) }}mm · 差 <strong :class="kd.avg_difference >= 0 ? 'text-red-600' : 'text-blue-600'">{{ kd.avg_difference >= 0 ? '+' : '' }}{{ kd.avg_difference?.toFixed(2) }}mm</strong>
                  </div>
                  <p class="text-[10px] text-gray-600 mt-0.5">{{ kd.description }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="xl:col-span-3 bg-white rounded-xl border border-[#E8DFC9] p-5">
            <h3 class="text-sm font-bold text-[#5D4E2B] mb-3 flex items-center justify-between">
              <span class="flex items-center gap-2"><Layers class="w-4 h-4" />差异热图（逐点对比）</span>
              <div class="flex items-center gap-4 text-[10px] font-normal">
                <span class="flex items-center gap-1"><span class="inline-block w-8 h-3 rounded" style="background: linear-gradient(to right, rgb(100,180,255), rgb(220,220,220), rgb(255,100,60));"></span> B偏粗 ← 无差异 → A偏粗</span>
              </div>
            </h3>
            <div class="bg-gradient-to-b from-[#FAF6ED] to-[#F5F0E8] rounded-lg border border-[#E8DFC9] p-4 overflow-x-auto">
              <svg width="100%" height="540" viewBox="0 0 700 540" style="min-width:700px;">
                <g>
                  <text x="90" y="25" font-size="11" font-weight="bold" fill="#1565C0">A 剖面（{{ diffResult.profile_a_name?.slice(0, 10) }}）</text>
                  <text x="360" y="25" font-size="11" font-weight="bold" fill="#E65100">差异热图</text>
                  <text x="610" y="25" font-size="11" font-weight="bold" fill="#7B1FA2">B 剖面（{{ diffResult.profile_b_name?.slice(0, 10) }}）</text>
                  <path
                    :d="(() => {
                      const a = diffResult.profile_a_sample || []
                      if (!a.length) return ''
                      const maxX = Math.max(...a.map(p => p.x), 1)
                      const maxY = Math.max(...a.map(p => p.y), 1)
                      return a.map((p, i) => {
                        const x = 90 + (p.x / maxX) * 50
                        const y = 520 - (p.y / maxY) * 470
                        return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
                      }).join(' ')
                    })()" fill="rgba(21,101,192,0.18)" stroke="#1565C0" stroke-width="1.2"
                  />
                  <path
                    :d="(() => {
                      const b = diffResult.profile_b_sample || []
                      if (!b.length) return ''
                      const maxX = Math.max(...b.map(p => p.x), 1)
                      const maxY = Math.max(...b.map(p => p.y), 1)
                      return b.map((p, i) => {
                        const x = 610 + (p.x / maxX) * 50
                        const y = 520 - (p.y / maxY) * 470
                        return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
                      }).join(' ')
                    })()" fill="rgba(123,31,162,0.18)" stroke="#7B1FA2" stroke-width="1.2"
                  />
                  <g>
                    <line x1="250" y1="50" x2="250" y2="520" stroke="#1565C0" stroke-width="0.5" stroke-dasharray="2,2" opacity="0.5" />
                    <line x1="350" y1="50" x2="350" y2="520" stroke="#1565C0" stroke-width="0.5" stroke-dasharray="2,2" opacity="0.5" />
                    <line x1="450" y1="50" x2="450" y2="520" stroke="#7B1FA2" stroke-width="0.5" stroke-dasharray="2,2" opacity="0.5" />
                    <rect v-for="(p, i) in diffResult.heatmap_data" :key="'bar'+i"
                      :x="350 - 50 * (1 + p.diameter_diff / (maxDiff * 2))"
                      :y="520 - (p.normalized_height * 470) - 2"
                      :width="50 * Math.abs(p.diameter_diff) / maxDiff"
                      height="2.5"
                      :fill="heatColor(p.diameter_diff, maxDiff)" opacity="0.85" />
                    <line x1="350" y1="50" x2="350" y2="520" stroke="#5D4E2B" stroke-width="1" />
                  </g>
                </g>
                <g font-size="9" fill="#5D4E2B" text-anchor="end">
                  <text v-for="y in [0, 0.25, 0.5, 0.75, 1]" :key="'tick'+y" :x="240" :y="522 - y * 470">{{ (y * 100).toFixed(0) }}%</text>
                </g>
              </svg>
            </div>
          </div>
        </div>
      </section>

      <section v-show="activeTab === 'reports'" class="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <div class="xl:col-span-2 bg-white rounded-xl border border-[#E8DFC9] p-5 space-y-4">
          <h2 class="text-base font-bold text-[#5D4E2B] flex items-center gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-[#1565C0] to-[#0D47A1] flex items-center justify-center text-white"><FileText class="w-5 h-5" /></div>
            研究报告生成器
          </h2>
          <div>
            <label class="text-xs font-semibold text-gray-600 mb-1.5 block">目标器型档案 <span class="text-red-400">*</span></label>
            <select v-model="selectedProfileForReport" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#1565C0]">
              <option :value="null">— 请选择器型档案 —</option>
              <option v-for="p in reportProfileList" :key="p.id" :value="p.id">{{ p.name }} · {{ p.condition_status }} · {{ p.dynasty || '朝代未知' }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-600 mb-1.5 block">报告类型</label>
            <div class="grid grid-cols-2 gap-1.5">
              <button v-for="t in [{ k: 'standard' as string, label: '标准研究报告' }, { k: 'conservation' as string, label: '保护修复报告' }, { k: 'comparative' as string, label: '对比研究报告' }, { k: 'typology' as string, label: '类型学报告' }]" :key="t.k"
                :class="['py-2 text-[11px] rounded-lg border font-medium transition', reportType === t.k ? 'bg-[#1565C0] text-white border-[#1565C0]' : 'bg-white text-[#5D4E2B] border-[#E8DFC9] hover:border-[#1565C0] hover:bg-[#1565C0]/5']"
                @click="reportType = t.k as any"
              >{{ t.label }}</button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-semibold text-gray-600 mb-1.5 block">报告自定义标题</label>
              <input v-model="reportCustomTitle" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#1565C0]" placeholder="可选" />
            </div>
            <div>
              <label class="text-xs font-semibold text-gray-600 mb-1.5 block">研究人员/作者</label>
              <input v-model="reportAuthor" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#1565C0]" placeholder="可选" />
            </div>
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-600 mb-1.5 block">关键词（逗号分隔）</label>
            <input v-model="reportKeywords" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#1565C0]" placeholder="如：唐代, 罐, 青瓷, 考古" />
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-600 mb-2 block">包含章节</label>
            <div class="grid grid-cols-2 gap-1.5">
              <label v-for="s in sectionOptions" :key="s.key" class="flex items-center gap-1.5 p-2 rounded-lg border border-[#E8DFC9] text-xs cursor-pointer hover:bg-[#FAF6ED]">
                <input type="checkbox" :value="s.key" v-model="includeSections" class="accent-[#1565C0]" />
                <span :class="includeSections.includes(s.key) ? 'text-[#1565C0] font-semibold' : 'text-gray-500'">{{ s.label }}</span>
              </label>
            </div>
          </div>
          <button :disabled="!selectedProfileForReport || generatingReport" class="w-full py-3 bg-gradient-to-r from-[#1565C0] to-[#0D47A1] text-white text-sm font-bold rounded-lg shadow-md hover:shadow-lg disabled:opacity-40" @click="doGenerateReport">
            {{ generatingReport ? '📝 正在生成报告...' : '🚀 生成研究报告' }}
          </button>
          <div v-if="lastGenerated" class="p-4 bg-green-50 border border-green-200 rounded-xl">
            <div class="text-sm font-bold text-green-700 mb-2 flex items-center gap-1"><Sparkles class="w-4 h-4" />生成成功！</div>
            <div class="text-xs text-gray-600 space-y-1">
              <div>报告编号：<span class="font-semibold">{{ lastGenerated.report_code }}</span></div>
              <div>类型：{{ lastGenerated.report_type }}</div>
              <div>章节：{{ lastGenerated.section_count }} 节</div>
              <div>摘要：{{ (lastGenerated as any).summary?.slice(0, 80) }}{{ (lastGenerated as any).summary?.length > 80 ? '...' : '' }}</div>
            </div>
          </div>
        </div>

        <div class="xl:col-span-3 bg-white rounded-xl border border-[#E8DFC9] p-5">
          <h3 class="text-sm font-bold text-[#5D4E2B] mb-3 flex items-center justify-between">
            <span class="flex items-center gap-2"><Layers class="w-4 h-4" />历史报告档案</span>
            <span class="text-[11px] font-normal text-gray-400">{{ reports.length }} 份</span>
          </h3>
          <div v-if="reports.length === 0" class="flex flex-col items-center justify-center h-[420px] text-gray-400">
            <FileText class="w-20 h-20 mb-3 opacity-20" />
            <p class="text-sm">暂无已生成报告</p>
            <p class="text-[11px] mt-1">请选择器型档案并生成第一份研究报告</p>
          </div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div v-for="r in reports" :key="r.id" class="p-4 rounded-xl border border-[#E8DFC9] bg-gradient-to-br from-white to-[#FAF6ED] hover:border-[#1565C0]/40 hover:shadow-md transition-all">
              <div class="flex items-start justify-between mb-2">
                <div class="flex items-center gap-2">
                  <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-[#1565C0] to-[#0D47A1] flex items-center justify-center text-white text-xs font-bold">报</div>
                  <div>
                    <h4 class="text-sm font-bold text-[#5D4E2B] leading-tight line-clamp-1">{{ r.custom_title || r.title || '未命名报告' }}</h4>
                    <p class="text-[10px] text-gray-400">{{ r.report_code }} · {{ r.report_type }}</p>
                  </div>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-1 text-[10px] text-gray-500 mb-3">
                <div>器型ID: <span class="text-[#5D4E2B]">{{ r.profile_id }}</span></div>
                <div>章节: <span class="text-[#5D4E2B]">{{ r.section_count || '-' }}</span></div>
                <div v-if="r.author">作者: <span class="text-[#5D4E2B]">{{ r.author }}</span></div>
                <div>{{ new Date(r.created_at || '').toLocaleDateString('zh-CN') }}</div>
              </div>
              <div v-if="(r.keywords as string[])?.length" class="flex flex-wrap gap-1 mb-3">
                <span v-for="k in (r.keywords as string[]).slice(0, 5)" :key="k" class="px-1.5 py-0.5 bg-[#1565C0]/10 text-[#1565C0] text-[10px] rounded">#{{ k }}</span>
              </div>
              <div class="flex gap-1.5">
                <button class="flex-1 py-1.5 bg-[#1565C0] text-white text-[11px] rounded-lg hover:bg-[#0D47A1] flex items-center justify-center gap-1" @click="viewReport(r)"><Eye class="w-3.5 h-3.5" />查看</button>
                <button class="py-1.5 px-2.5 bg-[#5D8A66] text-white text-[11px] rounded-lg hover:bg-[#4a6f52] flex items-center gap-1" @click="downloadReport(r, 'json')"><Download class="w-3.5 h-3.5" />JSON</button>
                <button class="py-1.5 px-2.5 bg-[#8B6914] text-white text-[11px] rounded-lg hover:bg-[#6d5210] flex items-center gap-1" @click="downloadReport(r, 'csv')"><Download class="w-3.5 h-3.5" />CSV</button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <div v-if="showReportDetail && reportDetail" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showReportDetail = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <div class="px-5 py-4 border-b border-[#E8DFC9] flex items-center justify-between bg-[#FAF6ED]">
          <div>
            <h2 class="text-lg font-bold text-[#5D4E2B]">{{ reportDetail.title || '研究报告' }}</h2>
            <p class="text-xs text-gray-500">{{ reportDetail.report_code }} · {{ reportDetail.author ? '作者：' + reportDetail.author : '' }} · {{ new Date(reportDetail.created_at || '').toLocaleDateString('zh-CN') }}</p>
          </div>
          <div class="flex items-center gap-2">
            <button class="px-3 py-1.5 bg-[#1565C0] text-white text-xs rounded-lg hover:bg-[#0D47A1] flex items-center gap-1" @click="downloadReport(reportDetail, 'json')"><Download class="w-4 h-4" />导出JSON</button>
            <button class="px-3 py-1.5 bg-[#8B6914] text-white text-xs rounded-lg hover:bg-[#6d5210] flex items-center gap-1" @click="downloadReport(reportDetail, 'csv')"><Download class="w-4 h-4" />导出CSV</button>
            <button class="p-2 rounded-lg hover:bg-white/60" @click="showReportDetail = false"><X class="w-5 h-5 text-gray-400" /></button>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto p-6 space-y-5">
          <template v-for="sec in (reportDetail.sections || [])" :key="sec.id || sec.section_id || JSON.stringify(sec).slice(0, 10)">
            <div class="p-4 bg-[#FAF6ED] rounded-xl border border-[#E8DFC9]">
              <h3 class="text-sm font-bold text-[#5D4E2B] mb-3 flex items-center gap-2 pb-2 border-b border-[#E8DFC9]">
                <span class="w-6 h-6 rounded-lg bg-[#1565C0] text-white flex items-center justify-center text-xs">{{ sec.order || sec.section_order || '•' }}</span>
                {{ sec.section_title || sec.title || '章节' }}
              </h3>
              <div v-if="sec.data" class="text-xs text-gray-700 leading-relaxed">
                <pre v-if="typeof sec.data === 'string'" class="whitespace-pre-wrap font-sans">{{ sec.data }}</pre>
                <div v-else-if="Array.isArray(sec.data)">
                  <div v-for="(item, i) in sec.data" :key="i" class="mb-1.5">• {{ typeof item === 'string' ? item : JSON.stringify(item, null, 0) }}</div>
                </div>
                <pre v-else class="whitespace-pre-wrap font-sans">{{ JSON.stringify(sec.data, null, 2) }}</pre>
              </div>
              <div v-if="sec.content" class="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap">{{ sec.content }}</div>
            </div>
          </template>
          <div v-if="reportDetail.conclusions" class="p-4 bg-gradient-to-br from-[#1565C0]/5 to-[#0D47A1]/5 rounded-xl border border-[#1565C0]/20">
            <h3 class="text-sm font-bold text-[#1565C0] mb-2">📌 研究结论</h3>
            <div v-if="Array.isArray(reportDetail.conclusions)" class="space-y-1.5 text-xs text-gray-700">
              <div v-for="(c, i) in reportDetail.conclusions" :key="i">• {{ c }}</div>
            </div>
            <pre v-else class="whitespace-pre-wrap font-sans text-xs text-gray-700">{{ JSON.stringify(reportDetail.conclusions, null, 2) }}</pre>
          </div>
          <div v-if="reportDetail.keywords?.length" class="flex flex-wrap gap-1.5">
            <span v-for="k in reportDetail.keywords" :key="k" class="px-2 py-0.5 bg-[#1565C0]/10 text-[#1565C0] text-[11px] rounded-full">#{{ k }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
