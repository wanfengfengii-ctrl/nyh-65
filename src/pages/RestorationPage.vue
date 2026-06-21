<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Home, RotateCcw, Trash2, Download, ArrowLeft } from 'lucide-vue-next'
import { useProfileStore } from '@/stores/profile'
import RestorationCanvas from '@/components/restoration/RestorationCanvas.vue'
import RestorationPanel from '@/components/restoration/RestorationPanel.vue'
import ProfileCanvas from '@/components/ProfileCanvas.vue'

const router = useRouter()
const store = useProfileStore()

const canvasRef = ref<InstanceType<typeof RestorationCanvas> | null>(null)
const panelRef = ref<InstanceType<typeof RestorationPanel> | null>(null)

const showOriginal = ref(true)
const showRestored = ref(true)
const showSpeculation = ref(true)

const showFragmentInput = ref(false)
const fragmentPoints = ref<{ x: number; y: number }[]>([])

onMounted(() => {
  store.loadFromStorage()
  if (store.controlPoints.length < 3) {
    showFragmentInput.value = true
  }
})

function handleGenerate() {
  const result = store.generateRestorations()
  if (!result.isValid) {
    showFragmentInput.value = true
  }
}

function handleClear() {
  store.clearRestorations()
}

function handleExport() {
  if (!store.currentScheme) return
  const data = store.exportRestoration()
  const blob = new Blob([data], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${store.currentScheme.name}_复原分析_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function handleDeletePoint(id: number) {
  store.deletePoint(id)
}

function loadSampleFragment() {
  store.createNewScheme('残损陶器示例')
  store.controlPoints.forEach((p, idx) => {
    if (idx < store.controlPoints.length - 1) {
      store.deletePoint(store.controlPoints[store.controlPoints.length - 1].id)
    }
  })
  const samplePoints = [
    { x: 60, y: 80 },
    { x: 75, y: 120 },
    { x: 80, y: 160 },
    { x: 70, y: 200 },
  ]
  samplePoints.forEach(p => {
    store.addPoint(p.x, p.y)
  })
  showFragmentInput.value = false
}
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
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#E65100] to-[#8B6914] flex items-center justify-center text-white text-sm font-bold shadow-sm">
          复
        </div>
        <div>
          <h1 class="text-[15px] font-bold text-[#5D4E2B] leading-tight">
            器物残损复原模块
          </h1>
          <p class="text-[10px] text-gray-500 leading-tight mt-0.5">
            Ceramic Profile Restoration Module
          </p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button
          class="px-3 py-1.5 bg-white text-[#5D4E2B] text-xs rounded-lg border border-[#E8DFC9] hover:bg-[#FAF6ED] transition-colors flex items-center gap-1.5"
          @click="router.push('/')"
        >
          <Home class="w-4 h-4" />
          返回主页
        </button>
        <div
          v-if="store.currentScheme"
          class="px-3 py-1 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9] text-xs text-[#5D4E2B]"
        >
          当前方案：
          <span class="font-semibold text-[#E65100]">{{ store.currentScheme.name }}</span>
          <span class="text-gray-400 ml-1">（{{ store.controlPoints.length }} 残损点）</span>
        </div>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <aside class="w-14 h-full flex flex-col items-center py-4 gap-2 bg-[#FAF6ED] border-r border-[#E8DFC9] flex-shrink-0">
        <button
          class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all w-full"
          title="重置当前方案"
          @click="store.resetPoints()"
        >
          <RotateCcw class="w-5 h-5 text-[#8B6914] group-hover:scale-110 transition-transform" />
          <span class="text-[10px] text-gray-600">重置</span>
        </button>
        <button
          :disabled="!store.hasRestoration"
          class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all w-full disabled:opacity-40 disabled:cursor-not-allowed"
          title="清空复原方案"
          @click="handleClear"
        >
          <Trash2 class="w-5 h-5 text-red-500 group-hover:scale-110 transition-transform" />
          <span class="text-[10px] text-gray-600">清空</span>
        </button>
        <button
          :disabled="!store.hasRestoration"
          class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all w-full disabled:opacity-40 disabled:cursor-not-allowed"
          title="导出复原数据"
          @click="handleExport"
        >
          <Download class="w-5 h-5 text-[#5D8A66] group-hover:scale-110 transition-transform" />
          <span class="text-[10px] text-gray-600">导出</span>
        </button>
        <div class="w-10 h-px bg-[#E8DFC9] my-1" />
        <div class="mt-auto w-full px-2">
          <div class="text-center text-[10px] text-gray-400 leading-relaxed">
            复原方案:
            <span v-if="store.hasRestoration" class="text-[#E65100] font-semibold">
              {{ store.restorationSchemes.length }} 个
            </span>
            <span v-else class="text-gray-400">无</span>
          </div>
        </div>
      </aside>

      <main class="flex-1 flex flex-col overflow-hidden p-3 gap-3">
        <div v-if="showFragmentInput" class="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
          <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <h3 class="text-lg font-bold text-[#5D4E2B] mb-3">输入残损剖面片段</h3>
            <p class="text-sm text-gray-600 mb-4">
              请在画布上双击添加现存剖面片段的控制点，或加载示例数据开始复原。
            </p>
            <div class="flex gap-3">
              <button
                class="flex-1 py-2.5 rounded-lg bg-[#5D8A66] text-white text-sm font-medium hover:bg-[#4a6f52] transition-colors"
                @click="showFragmentInput = false"
              >
                手动输入
              </button>
              <button
                class="flex-1 py-2.5 rounded-lg bg-[#8B6914] text-white text-sm font-medium hover:bg-[#6d5210] transition-colors"
                @click="loadSampleFragment"
              >
                加载示例数据
              </button>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 flex-1 min-h-0">
          <div class="lg:col-span-2 flex flex-col min-h-0">
            <div class="flex items-center justify-between mb-2 flex-shrink-0">
              <h2 class="text-sm font-bold text-[#5D4E2B] flex items-center gap-2">
                <span class="inline-block w-1 h-4 bg-[#E65100] rounded"></span>
                剖面曲线复原对比
              </h2>
              <div class="text-xs text-gray-500">
                <span class="text-[#5D8A66]">绿色实线</span> = 原始残损剖面 ·
                <span class="text-[#E65100]">橙色虚线</span> = 复原补全段
              </div>
            </div>
            <div class="flex-1 min-h-0">
              <RestorationCanvas
                v-if="store.hasRestoration"
                ref="canvasRef"
                :showOriginal="showOriginal"
                :showRestored="showRestored"
                :showSpeculation="showSpeculation"
              />
              <ProfileCanvas
                v-else
                @delete-point="handleDeletePoint"
              />
            </div>
          </div>

          <div class="flex flex-col min-h-0">
            <div class="flex items-center justify-between mb-2 flex-shrink-0">
              <h2 class="text-sm font-bold text-[#5D4E2B] flex items-center gap-2">
                <span class="inline-block w-1 h-4 bg-[#8B6914] rounded"></span>
                复原方案与参数
              </h2>
            </div>
            <div class="flex-1 min-h-0">
              <RestorationPanel
                ref="panelRef"
                :showOriginal="showOriginal"
                :showRestored="showRestored"
                :showSpeculation="showSpeculation"
                @generate="handleGenerate"
                @clear="handleClear"
                @export="handleExport"
                @update:showOriginal="showOriginal = $event"
                @update:showRestored="showRestored = $event"
                @update:showSpeculation="showSpeculation = $event"
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
