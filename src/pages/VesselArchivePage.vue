<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Search, Plus, Edit, Trash2, Eye, ArrowLeft, History, ShieldCheck, Sparkles, Filter, X, Save } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { api } from '@/lib/api'
import { useProfileStore } from '@/stores/profile'
import type { VesselProfile, ControlPoint, VesselVersion, RestorationAssessment, KeyPart } from '@/types'

const router = useRouter()
const store = useProfileStore()

const profiles = ref<VesselProfile[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const filterCondition = ref('')
const filterType = ref('')
const filterDynasty = ref('')
const selectedProfile = ref<VesselProfile | null>(null)
const showDetailModal = ref(false)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showVersionsModal = ref(false)
const showAssessmentModal = ref(false)
const versions = ref<VesselVersion[]>([])
const assessments = ref<RestorationAssessment[]>([])
const creatingProfile = ref({
  name: '',
  code: '',
  vessel_type: '',
  dynasty: '',
  condition_status: '完整器' as '完整器' | '残损器' | '复原器' | '采集残片',
  description: '',
  material: '',
  origin_site: '',
  museum_no: '',
  condition_detail: '',
})
const versionLabel = ref('')
const versionSummary = ref('')
const savingVersion = ref(false)
const creatingAssessment = ref(false)

const conditionBadge = (s?: string) => {
  const map: Record<string, [string, string]> = {
    '完整器': ['bg-green-100 text-green-700', '✅'],
    '残损器': ['bg-red-100 text-red-700', '⚠️'],
    '复原器': ['bg-orange-100 text-orange-700', '🔄'],
    '采集残片': ['bg-gray-200 text-gray-600', '🧩'],
  }
  return map[s || ''] || ['bg-gray-100 text-gray-500', '']
}

const vesselTypeOptions = ['罐', '瓶', '盘', '碗', '杯', '壶', '盆', '炉', '鬲', '尊', '鼎', '其他']
const conditionOptions = ['完整器', '残损器', '复原器', '采集残片']
const dynastyOptions = ['唐', '宋', '元', '明', '清', '龙山文化', '新石器', '商', '周', '现代仿制', '未知']

const filteredProfiles = computed(() => {
  return profiles.value.filter(p => {
    if (filterCondition.value && p.condition_status !== filterCondition.value) return false
    if (filterType.value && p.vessel_type !== filterType.value) return false
    if (filterDynasty.value && p.dynasty !== filterDynasty.value) return false
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      return (
        p.name.toLowerCase().includes(kw) ||
        (p.code && p.code.toLowerCase().includes(kw)) ||
        (p.description && p.description.toLowerCase().includes(kw)) ||
        (p.museum_no && p.museum_no.toLowerCase().includes(kw))
      )
    }
    return true
  })
})

const statCount = computed(() => ({
  total: profiles.value.length,
  intact: profiles.value.filter(p => p.condition_status === '完整器').length,
  damaged: profiles.value.filter(p => p.condition_status === '残损器').length,
  restored: profiles.value.filter(p => p.condition_status === '复原器').length,
}))

async function loadProfiles() {
  loading.value = true
  try {
    profiles.value = await api.vesselProfiles.list()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadVersions() {
  if (!selectedProfile.value) return
  try {
    versions.value = await api.vesselProfiles.versions.list(selectedProfile.value.id)
  } catch (e) {
    versions.value = []
  }
}

async function loadAssessments() {
  if (!selectedProfile.value) return
  try {
    assessments.value = await api.vesselProfiles.assessments.list(selectedProfile.value.id)
  } catch (e) {
    assessments.value = []
  }
}

function openDetail(p: VesselProfile) {
  selectedProfile.value = p
  showDetailModal.value = true
}

async function createProfile() {
  try {
    const cps = (store.controlPoints as ControlPoint[])?.length ? store.controlPoints : null
    const payload = {
      ...creatingProfile.value,
      control_points: cps,
      profile_data: cps ? { control_points: cps } : null,
    }
    const created = await api.vesselProfiles.create(payload)
    profiles.value.unshift(created)
    showCreateModal.value = false
    creatingProfile.value = { name: '', code: '', vessel_type: '', dynasty: '', condition_status: '完整器', description: '', material: '', origin_site: '', museum_no: '', condition_detail: '' }
    openDetail(created)
  } catch (e: any) {
    alert('创建失败：' + (e?.message || '未知错误'))
  }
}

async function saveCurrentToProfile() {
  if (!selectedProfile.value) return
  try {
    const cps = store.controlPoints as ControlPoint[]
    const payload: any = { control_points: cps }
    const updated = await api.vesselProfiles.update(selectedProfile.value.id, payload)
    selectedProfile.value = updated
    profiles.value = profiles.value.map(p => p.id === updated.id ? updated : p)
    alert('已将当前工作台剖面保存到档案')
  } catch (e: any) {
    alert('保存失败：' + (e?.message || '未知错误'))
  }
}

function loadProfileToWorkspace() {
  if (!selectedProfile.value) return
  const cps = (selectedProfile.value as any).control_points || (selectedProfile.value as any).profile_data?.control_points || []
  if (!cps?.length) {
    alert('此档案暂无控制点数据')
    return
  }
  store.createNewScheme(selectedProfile.value.name)
  store.replacePoints(cps)
  router.push('/')
}

async function deleteProfile(p: VesselProfile) {
  if (!confirm(`确定删除档案 "${p.name}"？此操作不可恢复。`)) return
  try {
    await api.vesselProfiles.delete(p.id)
    profiles.value = profiles.value.filter(x => x.id !== p.id)
    if (selectedProfile.value?.id === p.id) {
      showDetailModal.value = false
      selectedProfile.value = null
    }
  } catch (e: any) {
    alert('删除失败：' + (e?.message || '未知错误'))
  }
}

async function saveVersion() {
  if (!selectedProfile.value || savingVersion.value) return
  savingVersion.value = true
  try {
    const cps = store.controlPoints as ControlPoint[]
    const created = await api.vesselProfiles.versions.create(selectedProfile.value.id, {
      version_label: versionLabel.value || undefined,
      change_summary: versionSummary.value || undefined,
      control_points: cps,
      profile_snapshot: {
        control_points: cps,
        dimensions: (store as any).lastCalculatedDimensions || null,
      },
    })
    await loadVersions()
    versionLabel.value = ''
    versionSummary.value = ''
    alert('版本已保存：v' + created.version_number)
  } catch (e: any) {
    alert('保存版本失败：' + (e?.message || '未知错误'))
  } finally {
    savingVersion.value = false
  }
}

async function restoreVersion(v: VesselVersion) {
  if (!selectedProfile.value) return
  if (!confirm(`确定回退到版本 v${v.version_number} (${v.version_label || '未命名'})？`)) return
  try {
    const updated = await api.vesselProfiles.versions.restore(selectedProfile.value.id, v.id)
    selectedProfile.value = updated
    profiles.value = profiles.value.map(p => p.id === updated.id ? updated : p)
    alert('已恢复到此版本')
  } catch (e: any) {
    alert('恢复失败：' + (e?.message || '未知错误'))
  }
}

async function doAssessRestoration() {
  if (!selectedProfile.value || creatingAssessment.value) return
  creatingAssessment.value = true
  try {
    const cps = (selectedProfile.value as any).control_points || (selectedProfile.value as any).profile_data?.control_points || store.controlPoints
    const assessed = await api.vesselProfiles.assessments.create(selectedProfile.value.id, { control_points: cps })
    assessments.value.unshift(assessed)
    alert('可信度评估完成：总分 ' + (assessed.overall_confidence * 100).toFixed(1) + '%')
  } catch (e: any) {
    alert('评估失败：' + (e?.message || '未知错误'))
  } finally {
    creatingAssessment.value = false
  }
}

function miniVesselPath(obj: any) {
  const cps: ControlPoint[] = obj?.control_points || obj?.profile_data?.control_points || []
  if (cps.length < 2) return ''
  const maxX = Math.max(...cps.map(p => p.x), 1)
  const maxY = Math.max(...cps.map(p => p.y), 1)
  const sorted = [...cps].sort((a, b) => a.y - b.y)
  return sorted.map((p, i) => {
    const x = 18 + (p.x / maxX) * 16
    const y = 44 - (p.y / maxY) * 40
    return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
  }).join(' ') + ' L18,' + (44 - (sorted[0].y / maxY) * 40).toFixed(1) + ' Z'
}

function confidenceColor(c: number) {
  if (c >= 0.85) return 'text-green-600 bg-green-100'
  if (c >= 0.65) return 'text-yellow-600 bg-yellow-100'
  if (c >= 0.4) return 'text-orange-600 bg-orange-100'
  return 'text-red-600 bg-red-100'
}

function profileDimensions(p: any) {
  return p?.dimensions || (p as any).profile_data?.dimensions || {}
}

watch(showVersionsModal, v => { if (v) loadVersions() })
watch(showAssessmentModal, v => { if (v) loadAssessments() })

onMounted(loadProfiles)
</script>

<template>
  <div class="w-screen h-screen flex flex-col overflow-hidden bg-[#F5F0E8]">
    <header class="h-14 flex items-center justify-between px-5 bg-white border-b border-[#E8DFC9] flex-shrink-0">
      <div class="flex items-center gap-3">
        <button class="p-1.5 rounded-lg hover:bg-[#F5F0E8]" @click="router.push('/')">
          <ArrowLeft class="w-5 h-5 text-[#5D4E2B]" />
        </button>
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#8B6914] to-[#6d5210] flex items-center justify-center text-white text-sm font-bold shadow-sm">档</div>
        <div>
          <h1 class="text-[15px] font-bold text-[#5D4E2B] leading-tight">器型档案管理</h1>
          <p class="text-[10px] text-gray-500 leading-tight mt-0.5">Ceramic Vessel Archive</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <Search class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input v-model="searchKeyword" type="text" placeholder="搜索档案..." class="pl-9 pr-4 py-1.5 text-xs border border-[#E8DFC9] rounded-lg w-56 focus:outline-none focus:border-[#8B6914]" />
        </div>
        <button class="flex items-center gap-1.5 px-3 py-1.5 bg-[#8B6914] text-white text-xs rounded-lg hover:bg-[#6d5210]" @click="showCreateModal = true">
          <Plus class="w-4 h-4" />
          新建档案
        </button>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <aside class="w-56 flex-shrink-0 bg-white border-r border-[#E8DFC9] overflow-y-auto">
        <div class="p-3 border-b border-[#E8DFC9] bg-[#FAF6ED]">
          <h3 class="text-sm font-bold text-[#5D4E2B] flex items-center gap-2"><Filter class="w-4 h-4" />统计 · 筛选</h3>
        </div>
        <div class="p-3">
          <div class="grid grid-cols-2 gap-2 mb-4">
            <div class="p-2 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
              <div class="text-[10px] text-gray-500">总档案</div>
              <div class="text-lg font-bold text-[#5D4E2B]">{{ statCount.total }}</div>
            </div>
            <div class="p-2 bg-green-50 rounded-lg border border-green-100">
              <div class="text-[10px] text-green-600">完整器</div>
              <div class="text-lg font-bold text-green-700">{{ statCount.intact }}</div>
            </div>
            <div class="p-2 bg-red-50 rounded-lg border border-red-100">
              <div class="text-[10px] text-red-600">残损器</div>
              <div class="text-lg font-bold text-red-700">{{ statCount.damaged }}</div>
            </div>
            <div class="p-2 bg-orange-50 rounded-lg border border-orange-100">
              <div class="text-[10px] text-orange-600">复原器</div>
              <div class="text-lg font-bold text-orange-700">{{ statCount.restored }}</div>
            </div>
          </div>
          <div class="space-y-3">
            <div>
              <label class="text-[11px] text-gray-500 mb-1 block">保存状态</label>
              <select v-model="filterCondition" class="w-full px-2 py-1.5 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]">
                <option value="">全部状态</option>
                <option v-for="c in conditionOptions" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div>
              <label class="text-[11px] text-gray-500 mb-1 block">器型类别</label>
              <select v-model="filterType" class="w-full px-2 py-1.5 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]">
                <option value="">全部类别</option>
                <option v-for="t in vesselTypeOptions" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div>
              <label class="text-[11px] text-gray-500 mb-1 block">所属朝代</label>
              <select v-model="filterDynasty" class="w-full px-2 py-1.5 text-xs border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]">
                <option value="">全部朝代</option>
                <option v-for="d in dynastyOptions" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
          </div>
        </div>
      </aside>

      <main class="flex-1 overflow-y-auto p-4">
        <div v-if="loading" class="flex items-center justify-center h-64 text-gray-400 text-sm">加载中...</div>
        <div v-else-if="filteredProfiles.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-400">
          <Sparkles class="w-16 h-16 mb-3 opacity-30" />
          <p class="text-sm">暂无匹配的档案</p>
          <button class="mt-3 text-xs text-[#8B6914] hover:underline" @click="searchKeyword='';filterCondition='';filterType='';filterDynasty=''">清除筛选条件</button>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="p in filteredProfiles" :key="p.id" class="bg-white rounded-xl border border-[#E8DFC9] overflow-hidden hover:shadow-lg hover:border-[#8B6914]/40 transition-all cursor-pointer group" @click="openDetail(p)">
            <div class="h-32 bg-gradient-to-b from-[#FAF6ED] to-[#F5F0E8] flex items-center justify-center relative border-b border-[#E8DFC9]">
              <svg width="96" height="112" viewBox="0 0 36 50" class="transition-transform group-hover:scale-105">
                <path :d="miniVesselPath(p)" fill="#8B6914" fill-opacity="0.25" stroke="#8B6914" stroke-width="0.8" />
              </svg>
              <div class="absolute top-2 left-2 flex gap-1">
                <span :class="['px-1.5 py-0.5 rounded text-[10px] flex items-center gap-1', conditionBadge(p.condition_status)[0]]">
                  <span>{{ conditionBadge(p.condition_status)[1] }}</span>{{ p.condition_status }}
                </span>
              </div>
              <div v-if="p.restoration_confidence != null" class="absolute top-2 right-2 px-1.5 py-0.5 bg-white/90 rounded text-[10px] flex items-center gap-1" :class="confidenceColor(p.restoration_confidence)">
                <ShieldCheck class="w-3 h-3" />{{ (p.restoration_confidence * 100).toFixed(0) }}%
              </div>
            </div>
            <div class="p-3">
              <div class="flex items-start justify-between mb-1">
                <div class="flex-1 min-w-0">
                  <h3 class="text-sm font-semibold text-[#5D4E2B] truncate">{{ p.name }}</h3>
                  <p class="text-[10px] text-gray-400 truncate">{{ p.code || '未编号' }} {{ p.dynasty ? '· ' + p.dynasty : '' }}</p>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[10px] text-gray-500 mt-2">
                <div v-if="profileDimensions(p).height">通高: <span class="text-[#5D4E2B]">{{ profileDimensions(p).height?.toFixed(0) }}mm</span></div>
                <div v-if="profileDimensions(p).belly_diameter">腹径: <span class="text-[#5D4E2B]">{{ profileDimensions(p).belly_diameter?.toFixed(0) }}mm</span></div>
                <div v-if="profileDimensions(p).mouth_diameter">口径: <span class="text-[#5D4E2B]">{{ profileDimensions(p).mouth_diameter?.toFixed(0) }}mm</span></div>
                <div v-if="profileDimensions(p).volume">容量: <span class="text-[#8B6914]">{{ (profileDimensions(p).volume/1000).toFixed(1) }}L</span></div>
              </div>
              <div class="mt-2 flex items-center gap-1 text-[10px] text-gray-400">
                <History class="w-3 h-3" />
                <span>v{{ p.version_count || 0 }} 版本</span>
                <span>·</span>
                <span>{{ new Date(p.updated_at || p.created_at || '').toLocaleDateString('zh-CN') }}</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <div v-if="showDetailModal && selectedProfile" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showDetailModal = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <div class="px-5 py-4 border-b border-[#E8DFC9] flex items-center justify-between bg-[#FAF6ED]">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-[#8B6914] to-[#6d5210] flex items-center justify-center text-white font-bold">档</div>
            <div>
              <div class="flex items-center gap-2">
                <h2 class="text-lg font-bold text-[#5D4E2B]">{{ selectedProfile.name }}</h2>
                <span :class="['px-2 py-0.5 rounded text-[10px]', conditionBadge(selectedProfile.condition_status)[0]]">{{ conditionBadge(selectedProfile.condition_status)[1] }} {{ selectedProfile.condition_status }}</span>
              </div>
              <p class="text-xs text-gray-500">{{ selectedProfile.code || '未编号' }} · {{ selectedProfile.vessel_type || '未知器型' }} · {{ selectedProfile.dynasty || '朝代未知' }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button class="px-3 py-1.5 bg-white text-[#5D4E2B] text-xs rounded-lg hover:bg-[#F5F0E8] border border-[#E8DFC9] flex items-center gap-1" @click="showVersionsModal = true">
              <History class="w-4 h-4" />版本历史
            </button>
            <button class="px-3 py-1.5 bg-[#1565C0] text-white text-xs rounded-lg hover:bg-[#0D47A1] flex items-center gap-1" @click="loadProfileToWorkspace">
              <Edit class="w-4 h-4" />在工作台编辑
            </button>
            <button class="p-2 rounded-lg hover:bg-white/60" @click="showDetailModal = false"><X class="w-5 h-5 text-gray-400" /></button>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto p-5">
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <div class="lg:col-span-1 bg-gradient-to-b from-[#FAF6ED] to-[#F5F0E8] rounded-xl border border-[#E8DFC9] p-4 flex flex-col items-center">
              <svg width="220" height="280" viewBox="0 0 72 100" class="mb-3">
                <path d="M36,98 L36,40 M72,40 L0,40" stroke="#8B6914" stroke-width="0.3" stroke-dasharray="1,1" fill="none" />
                <path
                  :d="(() => {
                    const cps: any = (selectedProfile as any).control_points || (selectedProfile as any).profile_data?.control_points || []
                    if (cps.length < 2) return ''
                    const maxX = Math.max(...cps.map((p: any) => p.x), 1)
                    const maxY = Math.max(...cps.map((p: any) => p.y), 1)
                    const sorted = [...cps].sort((a: any, b: any) => a.y - b.y)
                    return sorted.map((p: any, i: number) => {
                      const x = 36 + (p.x / maxX) * 32
                      const y = 90 - (p.y / maxY) * 85
                      return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
                    }).join(' ') + ' L36,' + (90 - (sorted[0].y / maxY) * 85).toFixed(1) + ' Z'
                  })()"
                  fill="#8B6914" fill-opacity="0.2" stroke="#8B6914" stroke-width="1.5"
                />
              </svg>
              <button class="w-full py-2 bg-[#8B6914] text-white text-xs rounded-lg hover:bg-[#6d5210] flex items-center justify-center gap-1" @click="saveCurrentToProfile">
                <Save class="w-4 h-4" />将当前工作台剖面保存到此档案
              </button>
            </div>
            <div class="lg:col-span-2 space-y-4">
              <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
                  <div class="text-[10px] text-gray-500">通高</div>
                  <div class="text-base font-bold text-[#5D4E2B]">{{ profileDimensions(selectedProfile).height?.toFixed(1) || '--' }}<span class="text-[10px] font-normal ml-1 text-gray-400">mm</span></div>
                </div>
                <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
                  <div class="text-[10px] text-gray-500">口径</div>
                  <div class="text-base font-bold text-[#5D4E2B]">{{ profileDimensions(selectedProfile).mouth_diameter?.toFixed(1) || '--' }}<span class="text-[10px] font-normal ml-1 text-gray-400">mm</span></div>
                </div>
                <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
                  <div class="text-[10px] text-gray-500">腹径</div>
                  <div class="text-base font-bold text-[#5D4E2B]">{{ profileDimensions(selectedProfile).belly_diameter?.toFixed(1) || '--' }}<span class="text-[10px] font-normal ml-1 text-gray-400">mm</span></div>
                </div>
                <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
                  <div class="text-[10px] text-gray-500">容量</div>
                  <div class="text-base font-bold text-[#8B6914]">
                    {{ profileDimensions(selectedProfile).volume != null ? (profileDimensions(selectedProfile).volume < 1000 ? profileDimensions(selectedProfile).volume.toFixed(0) + 'ml' : (profileDimensions(selectedProfile).volume/1000).toFixed(2) + 'L') : '--' }}
                  </div>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <h4 class="text-xs font-bold text-[#5D4E2B] mb-2 flex items-center gap-1"><span class="w-1 h-3 bg-[#8B6914] rounded"></span>基本信息</h4>
                  <div class="space-y-1 text-xs">
                    <div class="flex"><span class="w-16 text-gray-400">材质</span><span class="text-[#5D4E2B]">{{ selectedProfile.material || '--' }}</span></div>
                    <div class="flex"><span class="w-16 text-gray-400">出土地</span><span class="text-[#5D4E2B]">{{ selectedProfile.origin_site || '--' }}</span></div>
                    <div class="flex"><span class="w-16 text-gray-400">博物馆号</span><span class="text-[#5D4E2B]">{{ selectedProfile.museum_no || '--' }}</span></div>
                    <div class="flex"><span class="w-16 text-gray-400">版本号</span><span class="text-[#5D4E2B]">v{{ selectedProfile.version_count || 1 }}</span></div>
                  </div>
                </div>
                <div>
                  <h4 class="text-xs font-bold text-[#5D4E2B] mb-2 flex items-center gap-1"><span class="w-1 h-3 bg-[#E65100] rounded"></span>复原评估</h4>
                  <div v-if="selectedProfile.restoration_confidence != null" class="p-3 bg-[#E65100]/5 rounded-lg border border-[#E65100]/20">
                    <div class="flex items-center justify-between mb-2">
                      <span class="text-xs text-gray-500">综合可信度</span>
                      <span class="text-xs font-bold px-2 py-0.5 rounded" :class="confidenceColor(selectedProfile.restoration_confidence)">{{ (selectedProfile.restoration_confidence * 100).toFixed(1) }}%</span>
                    </div>
                    <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div class="h-full rounded-full transition-all" :class="selectedProfile.restoration_confidence >= 0.65 ? 'bg-green-500' : selectedProfile.restoration_confidence >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'" :style="{ width: (selectedProfile.restoration_confidence * 100) + '%' }"></div>
                    </div>
                    <button class="mt-3 w-full py-1.5 bg-[#E65100] text-white text-xs rounded-lg hover:bg-[#BF360C]" @click="showAssessmentModal = true">查看/重新评估</button>
                  </div>
                  <div v-else class="p-3 bg-gray-50 rounded-lg border border-dashed border-gray-200 text-center">
                    <p class="text-xs text-gray-500 mb-2">尚未进行复原可信度评估</p>
                    <button class="py-1.5 px-3 bg-[#E65100] text-white text-xs rounded-lg hover:bg-[#BF360C]" @click="doAssessRestoration"><ShieldCheck class="w-3 h-3 inline mr-1" />立即评估</button>
                  </div>
                </div>
              </div>
              <div v-if="selectedProfile.description">
                <h4 class="text-xs font-bold text-[#5D4E2B] mb-2 flex items-center gap-1"><span class="w-1 h-3 bg-[#1565C0] rounded"></span>档案描述</h4>
                <p class="text-xs text-gray-600 leading-relaxed bg-[#FAF6ED] p-3 rounded-lg border border-[#E8DFC9]">{{ selectedProfile.description }}</p>
              </div>
              <div class="flex gap-2 pt-2">
                <button class="flex-1 py-2.5 bg-[#1565C0] text-white text-sm rounded-lg hover:bg-[#0D47A1] font-medium" @click="loadProfileToWorkspace">打开工作台编辑此器型</button>
                <button class="px-4 py-2.5 bg-red-50 text-red-600 text-sm rounded-lg hover:bg-red-100 border border-red-100" @click="deleteProfile(selectedProfile)"><Trash2 class="w-4 h-4" /></button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showCreateModal = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div class="px-5 py-4 border-b border-[#E8DFC9] flex items-center justify-between bg-[#FAF6ED]">
          <h2 class="text-lg font-bold text-[#5D4E2B]">新建器型档案</h2>
          <button class="p-2 rounded-lg hover:bg-white/60" @click="showCreateModal = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="flex-1 overflow-y-auto p-5 space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="col-span-2">
              <label class="text-xs text-gray-600 mb-1 block">档案名称 <span class="text-red-400">*</span></label>
              <input v-model="creatingProfile.name" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]" placeholder="如：唐陶彩绘陶罐" />
            </div>
            <div>
              <label class="text-xs text-gray-600 mb-1 block">档案编号</label>
              <input v-model="creatingProfile.code" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]" placeholder="如：TJ-001" />
            </div>
            <div>
              <label class="text-xs text-gray-600 mb-1 block">博物馆编号</label>
              <input v-model="creatingProfile.museum_no" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]" />
            </div>
            <div>
              <label class="text-xs text-gray-600 mb-1 block">器型类别</label>
              <select v-model="creatingProfile.vessel_type" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]">
                <option value="">请选择</option>
                <option v-for="t in vesselTypeOptions" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-gray-600 mb-1 block">所属朝代</label>
              <select v-model="creatingProfile.dynasty" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]">
                <option value="">请选择</option>
                <option v-for="d in dynastyOptions" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-gray-600 mb-1 block">保存状态</label>
              <select v-model="creatingProfile.condition_status" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]">
                <option v-for="c in conditionOptions" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div>
              <label class="text-xs text-gray-600 mb-1 block">材质</label>
              <input v-model="creatingProfile.material" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]" placeholder="如：青瓷、白瓷、陶" />
            </div>
            <div class="col-span-2">
              <label class="text-xs text-gray-600 mb-1 block">出土地点</label>
              <input v-model="creatingProfile.origin_site" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]" />
            </div>
            <div class="col-span-2">
              <label class="text-xs text-gray-600 mb-1 block">档案描述</label>
              <textarea v-model="creatingProfile.description" rows="3" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914] resize-none" placeholder="描述器型特征、纹饰、历史背景等"></textarea>
            </div>
          </div>
          <div class="p-3 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-700">
            💡 新建档案将自动关联<strong>当前工作台的剖面控制点</strong>（如果已绘制）。您也可以稍后再添加控制点数据。
          </div>
        </div>
        <div class="px-5 py-4 border-t border-[#E8DFC9] flex justify-end gap-2 bg-gray-50">
          <button class="px-4 py-2 bg-white text-gray-600 text-sm rounded-lg hover:bg-gray-100 border border-gray-200" @click="showCreateModal = false">取消</button>
          <button :disabled="!creatingProfile.name" class="px-5 py-2 bg-[#8B6914] text-white text-sm rounded-lg hover:bg-[#6d5210] disabled:opacity-40 disabled:cursor-not-allowed" @click="createProfile">创建档案</button>
        </div>
      </div>
    </div>

    <div v-if="showVersionsModal && selectedProfile" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showVersionsModal = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <div class="px-5 py-4 border-b border-[#E8DFC9] flex items-center justify-between bg-[#FAF6ED]">
          <h2 class="text-lg font-bold text-[#5D4E2B] flex items-center gap-2"><History class="w-5 h-5" />版本历史 - {{ selectedProfile.name }}</h2>
          <button class="p-2 rounded-lg hover:bg-white/60" @click="showVersionsModal = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="p-5 border-b border-[#E8DFC9] bg-gray-50">
          <h4 class="text-sm font-bold text-[#5D4E2B] mb-3">保存新版本（基于当前工作台剖面）</h4>
          <div class="grid grid-cols-2 gap-3 mb-3">
            <input v-model="versionLabel" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]" placeholder="版本标签（如：初版）" />
            <input v-model="versionSummary" type="text" class="w-full px-3 py-2 text-sm border border-[#E8DFC9] rounded-lg focus:outline-none focus:border-[#8B6914]" placeholder="变更说明" />
          </div>
          <button :disabled="savingVersion" class="w-full py-2 bg-[#1565C0] text-white text-sm rounded-lg hover:bg-[#0D47A1] disabled:opacity-50" @click="saveVersion">
            {{ savingVersion ? '保存中...' : '保存当前剖面为新版本' }}
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-5">
          <div v-if="versions.length === 0" class="text-center text-gray-400 text-sm py-8">暂无历史版本，请从上方保存第一个版本</div>
          <div v-else class="space-y-2">
            <div v-for="v in versions" :key="v.id" class="p-4 bg-white border border-[#E8DFC9] rounded-xl hover:shadow-sm transition">
              <div class="flex items-start justify-between mb-2">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 bg-[#1565C0] text-white text-xs font-bold rounded">v{{ v.version_number }}</span>
                    <span v-if="v.version_label" class="text-sm font-semibold text-[#5D4E2B]">{{ v.version_label }}</span>
                  </div>
                  <p class="text-xs text-gray-500 mt-1">{{ v.created_at ? new Date(v.created_at).toLocaleString('zh-CN') : '' }}</p>
                </div>
                <button class="px-3 py-1.5 bg-orange-50 text-orange-600 text-xs rounded-lg hover:bg-orange-100 border border-orange-100" @click="restoreVersion(v)">恢复此版本</button>
              </div>
              <div v-if="v.change_summary" class="text-xs text-gray-600 bg-[#FAF6ED] rounded-lg px-3 py-2 border border-[#E8DFC9]">{{ v.change_summary }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAssessmentModal && selectedProfile" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showAssessmentModal = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <div class="px-5 py-4 border-b border-[#E8DFC9] flex items-center justify-between bg-[#FAF6ED]">
          <h2 class="text-lg font-bold text-[#5D4E2B] flex items-center gap-2"><ShieldCheck class="w-5 h-5" />复原可信度评估</h2>
          <button class="p-2 rounded-lg hover:bg-white/60" @click="showAssessmentModal = false"><X class="w-5 h-5 text-gray-400" /></button>
        </div>
        <div class="flex-1 overflow-y-auto p-5 space-y-4">
          <div class="flex justify-center">
            <button :disabled="creatingAssessment" class="px-5 py-2 bg-[#E65100] text-white text-sm rounded-lg hover:bg-[#BF360C] disabled:opacity-50">
              {{ creatingAssessment ? '评估中...' : '+ 执行新评估' }}
            </button>
          </div>
          <div v-if="assessments.length === 0" class="text-center text-gray-400 text-sm py-8">暂无评估记录，请点击上方按钮执行评估</div>
          <div v-else class="space-y-3">
            <div v-for="a in assessments" :key="a.id" class="p-4 bg-[#FAF6ED] border border-[#E8DFC9] rounded-xl">
              <div class="flex items-center justify-between mb-3">
                <div>
                  <span class="text-xs text-gray-500">{{ new Date(a.created_at || '').toLocaleString('zh-CN') }}</span>
                </div>
                <span class="text-sm font-bold px-3 py-1 rounded-full" :class="confidenceColor(a.overall_confidence)">{{ (a.overall_confidence * 100).toFixed(1) }}%</span>
              </div>
              <div class="w-full h-2.5 bg-gray-200 rounded-full mb-4 overflow-hidden">
                <div class="h-full rounded-full transition-all" :class="a.overall_confidence >= 0.85 ? 'bg-green-500' : a.overall_confidence >= 0.65 ? 'bg-yellow-500' : a.overall_confidence >= 0.4 ? 'bg-orange-500' : 'bg-red-500'" :style="{ width: (a.overall_confidence * 100) + '%' }"></div>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-2 mb-3">
                <div class="p-2 bg-white rounded-lg">
                  <div class="text-[10px] text-gray-500">残片覆盖率</div>
                  <div class="text-sm font-bold text-[#5D4E2B]">{{ (a.fragment_coverage * 100).toFixed(0) }}%</div>
                </div>
                <div class="p-2 bg-white rounded-lg">
                  <div class="text-[10px] text-gray-500">缺失区段数</div>
                  <div class="text-sm font-bold text-[#5D4E2B]">{{ a.gap_count }}</div>
                </div>
                <div class="p-2 bg-white rounded-lg">
                  <div class="text-[10px] text-gray-500">支持证据项</div>
                  <div class="text-sm font-bold text-[#5D4E2B]">{{ (a.supporting_evidence as any[])?.length || 0 }}</div>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-2 mb-3">
                <div v-for="(k, label) in { part_confs_mouth: '口沿', part_confs_neck: '颈部', part_confs_shoulder: '肩部', part_confs_belly: '腹部', part_confs_foot: '圈足', part_confs_bottom: '底部' }" :key="k" class="flex items-center gap-2">
                  <span class="w-10 text-[10px] text-gray-500">{{ label }}</span>
                  <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div class="h-full rounded-full bg-[#8B6914]" :style="{ width: (((a as any)[k] || 0) * 100) + '%' }"></div>
                  </div>
                  <span class="w-10 text-right text-[10px] text-gray-600">{{ (((a as any)[k] || 0) * 100).toFixed(0) }}%</span>
                </div>
              </div>
              <div v-if="(a.recommendations as any[])?.length" class="pt-2 border-t border-[#E8DFC9]">
                <div class="text-[11px] font-semibold text-[#E65100] mb-1">💡 建议</div>
                <ul class="space-y-0.5">
                  <li v-for="(r, i) in (a.recommendations as any[])" :key="i" class="text-xs text-gray-600 list-disc list-inside">{{ r }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
