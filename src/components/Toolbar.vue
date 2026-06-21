<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Plus,
  Trash2,
  RotateCcw,
  Save,
  Copy,
  List,
  Wrench,
  Download,
  X,
  Pencil,
  Check,
} from 'lucide-vue-next'
import { useProfileStore } from '@/stores/profile'
import { calculateDimensions, generateDefaultPoints } from '@/utils/geometry'
import { useRouter } from 'vue-router'

const store = useProfileStore()
const router = useRouter()

const showSchemePanel = ref(false)
const renamingId = ref<string | null>(null)
const renameText = ref('')

const selectedIndex = computed(() => {
  if (store.selectedPointId === null) return -1
  return store.controlPoints.findIndex(p => p.id === store.selectedPointId)
})

function handleSaveScheme() {
  const name = prompt('方案名称：', store.currentScheme?.name || '新方案')
  if (name) {
    if (store.currentScheme) {
      store.renameScheme(store.currentScheme.id, name)
    } else {
      store.createNewScheme(name)
    }
  }
}

function handleAddPoint() {
  const pts = store.controlPoints
  const base = pts.length > 0 ? pts[Math.floor(pts.length / 2)] : { x: 50, y: 100 }
  store.addPoint(base.x + 10, base.y + 20)
}

function handleDeletePoint() {
  if (store.selectedPointId !== null) {
    store.deletePoint(store.selectedPointId)
  }
}

function startRename(id: string, name: string) {
  renamingId.value = id
  renameText.value = name
}

function confirmRename(id: string) {
  if (renameText.value.trim()) {
    store.renameScheme(id, renameText.value.trim())
  }
  renamingId.value = null
}

function toggleRepair() {
  if (selectedIndex.value >= 0) {
    store.toggleRepairMark(selectedIndex.value)
  }
}

function exportCurrent() {
  if (!store.currentScheme) return
  const data = store.exportScheme(store.currentScheme.id)
  const blob = new Blob([data], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${store.currentScheme.name}_剖面数据.json`
  a.click()
  URL.revokeObjectURL(url)
}

function getMiniPreview(schemeId: string) {
  const s = store.schemes.find(x => x.id === schemeId)
  if (!s) return { w: 60, h: 80 }
  const r = calculateDimensions(s.controlPoints, s.unit)
  return {
    w: 60,
    h: 80,
    ratio: r.height > 0 ? r.bellyDiameter / r.height : 0.5,
  }
}
</script>

<template>
  <div class="relative h-full flex flex-col items-center py-4 gap-2 bg-[#FAF6ED] border-r border-[#E8DFC9] w-16 flex-shrink-0">
    <div class="flex flex-col gap-1 w-full px-2">
      <button
        class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all"
        title="添加控制点"
        @click="handleAddPoint"
      >
        <Plus class="w-5 h-5 text-[#5D8A66] group-hover:scale-110 transition-transform" />
        <span class="text-[10px] text-gray-600">添加</span>
      </button>
      <button
        :disabled="store.selectedPointId === null || store.controlPoints.length <= 3"
        class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        title="删除选中控制点（至少保留3个）"
        @click="handleDeletePoint"
      >
        <Trash2 class="w-5 h-5 text-red-500 group-hover:scale-110 transition-transform" />
        <span class="text-[10px] text-gray-600">删除</span>
      </button>
      <button
        class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all"
        title="重置为默认曲线"
        @click="store.resetPoints()"
      >
        <RotateCcw class="w-5 h-5 text-[#8B6914] group-hover:scale-110 transition-transform" />
        <span class="text-[10px] text-gray-600">重置</span>
      </button>
    </div>

    <div class="w-10 h-px bg-[#E8DFC9] my-1" />

    <div class="flex flex-col gap-1 w-full px-2">
      <button
        :disabled="selectedIndex < 0"
        class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        :title="selectedIndex >= 0 ? '标记/取消修坯位置' : '请先选择控制点'"
        @click="toggleRepair"
      >
        <Wrench class="w-5 h-5 text-orange-500 group-hover:scale-110 transition-transform" />
        <span class="text-[10px] text-gray-600">修坯</span>
      </button>
      <button
        class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all"
        title="保存当前方案"
        @click="handleSaveScheme"
      >
        <Save class="w-5 h-5 text-[#1565C0] group-hover:scale-110 transition-transform" />
        <span class="text-[10px] text-gray-600">保存</span>
      </button>
      <button
        class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all"
        title="导出数据"
        @click="exportCurrent"
      >
        <Download class="w-5 h-5 text-[#5D8A66] group-hover:scale-110 transition-transform" />
        <span class="text-[10px] text-gray-600">导出</span>
      </button>
    </div>

    <div class="w-10 h-px bg-[#E8DFC9] my-1" />

    <div class="flex flex-col gap-1 w-full px-2">
      <button
        :class="[
          'group flex flex-col items-center justify-center gap-1 py-3 rounded-lg border transition-all',
          showSchemePanel ? 'bg-[#5D8A66] text-white border-[#5D8A66]' : 'hover:bg-white border-transparent hover:border-[#E8DFC9]'
        ]"
        title="方案管理"
        @click="showSchemePanel = !showSchemePanel"
      >
        <List class="w-5 h-5 group-hover:scale-110 transition-transform" />
        <span class="text-[10px]">方案</span>
      </button>
      <button
        class="group flex flex-col items-center justify-center gap-1 py-3 rounded-lg hover:bg-white border border-transparent hover:border-[#E8DFC9] transition-all"
        title="方案对比"
        @click="router.push('/compare')"
      >
        <Copy class="w-5 h-5 text-[#8B6914] group-hover:scale-110 transition-transform" />
        <span class="text-[10px] text-gray-600">对比</span>
      </button>
    </div>

    <div
      v-if="showSchemePanel"
      class="absolute left-full top-0 ml-2 w-72 max-h-[80vh] bg-white rounded-lg shadow-xl border border-[#E8DFC9] z-50 overflow-hidden flex flex-col"
    >
      <div class="flex items-center justify-between p-3 border-b border-[#E8DFC9] bg-[#FAF6ED]">
        <h4 class="text-sm font-bold text-[#5D4E2B]">方案管理</h4>
        <button
          class="p-1 rounded hover:bg-white"
          @click="showSchemePanel = false"
        >
          <X class="w-4 h-4 text-gray-500" />
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-2 space-y-2">
        <div
          v-for="s in store.schemes"
          :key="s.id"
          :class="[
            'p-2.5 rounded-lg border cursor-pointer transition-all flex items-start gap-2',
            s.id === store.currentSchemeId
              ? 'bg-[#5D8A66]/10 border-[#5D8A66]'
              : 'bg-white border-[#E8DFC9] hover:bg-[#FAF6ED]'
          ]"
          @click="store.selectScheme(s.id)"
        >
          <div
            class="w-10 h-14 rounded border border-[#E8DFC9] flex-shrink-0 bg-[#F5F0E8] flex items-center justify-center overflow-hidden"
          >
            <svg :width="40" :height="56" viewBox="0 0 40 56">
              <path
                v-if="s.controlPoints.length >= 2"
                :d="(() => {
                  const pts = s.controlPoints
                  const maxX = Math.max(...pts.map(p => p.x), 1)
                  const maxY = Math.max(...pts.map(p => p.y), 1)
                  return pts.map((p, i) => {
                    const x = 20 + (p.x / maxX) * 18
                    const y = 50 - (p.y / maxY) * 46
                    return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
                  }).join(' ') + ' L20,' + (50 - (pts[0].y / maxY) * 46).toFixed(1) + ' Z'
                })()"
                fill="#5D8A66"
                fill-opacity="0.3"
                stroke="#5D8A66"
                stroke-width="1"
              />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div v-if="renamingId !== s.id" class="flex items-center justify-between gap-1">
              <span class="text-sm font-medium text-[#5D4E2B] truncate">{{ s.name }}</span>
              <button
                class="p-0.5 rounded hover:bg-white flex-shrink-0"
                @click.stop="startRename(s.id, s.name)"
              >
                <Pencil class="w-3 h-3 text-gray-400" />
              </button>
            </div>
            <div v-else class="flex items-center gap-1">
              <input
                v-model="renameText"
                class="flex-1 min-w-0 px-1.5 py-0.5 text-sm border border-[#5D8A66] rounded outline-none"
                @keyup.enter="confirmRename(s.id)"
              />
              <button
                class="p-0.5 rounded hover:bg-[#5D8A66]/10"
                @click.stop="confirmRename(s.id)"
              >
                <Check class="w-3 h-3 text-[#5D8A66]" />
              </button>
            </div>
            <div class="text-[10px] text-gray-500 mt-0.5">
              {{ s.controlPoints.length }} 控制点 · {{ s.unit }}
            </div>
            <div class="flex gap-1 mt-1.5">
              <button
                class="px-2 py-0.5 text-[10px] rounded bg-[#F5F0E8] text-gray-600 hover:bg-[#E8DFC9]"
                @click.stop="store.duplicateScheme(s.id)"
              >复制</button>
              <button
                v-if="store.schemes.length > 1"
                class="px-2 py-0.5 text-[10px] rounded bg-red-50 text-red-600 hover:bg-red-100"
                @click.stop="store.deleteScheme(s.id)"
              >删除</button>
            </div>
          </div>
        </div>
      </div>
      <div class="p-2 border-t border-[#E8DFC9] bg-[#FAF6ED]">
        <button
          class="w-full py-1.5 rounded bg-[#5D8A66] text-white text-xs hover:bg-[#4a6f52] transition-colors flex items-center justify-center gap-1"
          @click="store.createNewScheme()"
        >
          <Plus class="w-3.5 h-3.5" /> 新建方案
        </button>
      </div>
    </div>

    <div class="mt-auto w-full px-2">
      <div class="text-center text-[10px] text-gray-400 leading-relaxed">
        选中:
        <span v-if="store.selectedPointId !== null" class="text-[#5D8A66] font-semibold">
          {{ selectedIndex + 1 }}号
        </span>
        <span v-else class="text-gray-400">无</span>
      </div>
    </div>
  </div>
</template>
