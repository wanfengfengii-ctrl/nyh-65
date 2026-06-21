<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ArrowLeft, Download, Trash2, Copy, Plus, Check } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { calculateDimensions, catmullRomToBezier, validateProfile } from '@/utils/geometry'
import type { ProfileScheme } from '@/types'

const router = useRouter()
const store = useProfileStore()

const selectedIds = ref<Set<string>>(new Set())
const compareCanvasRef = ref<HTMLCanvasElement | null>(null)
const dpr = window.devicePixelRatio || 1
const canvasSize = ref({ w: 800, h: 500 })

const schemeColors = [
  '#5D8A66',
  '#8B6914',
  '#1565C0',
  '#E53935',
  '#8E24AA',
  '#FB8C00',
  '#00897B',
  '#3949AB',
]

const selectedSchemes = computed(() => {
  return store.schemes.filter(s => selectedIds.value.has(s.id))
})

const comparisonResults = computed(() => {
  return selectedSchemes.value.map(s => ({
    scheme: s,
    result: calculateDimensions(s.controlPoints, s.unit),
    validation: validateProfile(s.controlPoints),
  }))
})

function toggleSelect(id: string) {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    if (selectedIds.value.size < 6) {
      selectedIds.value.add(id)
    }
  }
  selectedIds.value = new Set(selectedIds.value)
  drawComparison()
}

function exportAllComparison() {
  const data = {
    exportTime: new Date().toISOString(),
    schemes: selectedSchemes.value.map(s => {
      const r = calculateDimensions(s.controlPoints, s.unit)
      return {
        name: s.name,
        unit: s.unit,
        dimensions: {
          height: r.height,
          mouthDiameter: r.mouthDiameter,
          bellyDiameter: r.bellyDiameter,
          bottomDiameter: r.bottomDiameter,
          volumeMl: r.volume,
        },
        controlPoints: s.controlPoints.map((p, i) => ({
          index: i,
          x: p.x,
          y: p.y,
          isRepairMark: s.repairMarks.some(rm => rm.pointIndex === i),
        })),
      }
    }),
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `器型对比数据_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function drawComparison() {
  const canvas = compareCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const container = canvas.parentElement
  if (container) {
    canvasSize.value = { w: container.clientWidth, h: container.clientHeight }
    canvas.width = canvasSize.value.w * dpr
    canvas.height = canvasSize.value.h * dpr
    canvas.style.width = canvasSize.value.w + 'px'
    canvas.style.height = canvasSize.value.h + 'px'
  }

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, canvasSize.value.w, canvasSize.value.h)

  const padding = 60
  const availW = canvasSize.value.w - 2 * padding
  const availH = canvasSize.value.h - 2 * padding

  let maxX = 0
  let maxY = 0
  for (const s of selectedSchemes.value) {
    for (const p of s.controlPoints) {
      if (p.x > maxX) maxX = p.x
      if (p.y > maxY) maxY = p.y
    }
  }
  if (maxX === 0) maxX = 100
  if (maxY === 0) maxY = 200
  maxX *= 1.15
  maxY *= 1.1

  const scale = Math.min(availW / (2 * maxX), availH / maxY)
  const offsetX = canvasSize.value.w / 2
  const offsetY = canvasSize.value.h - padding

  const toScreen = (wx: number, wy: number) => ({
    x: offsetX + wx * scale,
    y: offsetY - wy * scale,
  })

  ctx.save()
  ctx.strokeStyle = 'rgba(139, 105, 20, 0.1)'
  ctx.lineWidth = 1
  for (let x = 0; x <= maxX; x += 50) {
    const sp = toScreen(x, 0)
    ctx.beginPath()
    ctx.moveTo(sp.x, padding)
    ctx.lineTo(sp.x, offsetY)
    ctx.stroke()
    const sp2 = toScreen(-x, 0)
    ctx.beginPath()
    ctx.moveTo(sp2.x, padding)
    ctx.lineTo(sp2.x, offsetY)
    ctx.stroke()
  }
  for (let y = 0; y <= maxY; y += 50) {
    const sp = toScreen(0, y)
    ctx.beginPath()
    ctx.moveTo(toScreen(-maxX, y).x, sp.y)
    ctx.lineTo(toScreen(maxX, y).x, sp.y)
    ctx.stroke()
  }
  ctx.restore()

  ctx.save()
  ctx.strokeStyle = '#8B6914'
  ctx.lineWidth = 1.5
  const axisO = toScreen(0, 0)
  ctx.beginPath()
  ctx.moveTo(axisO.x, padding - 10)
  ctx.lineTo(axisO.x, offsetY + 10)
  ctx.stroke()
  ctx.fillStyle = '#8B6914'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'right'
  for (let y = 0; y <= maxY; y += 50) {
    const sp = toScreen(0, y)
    if (sp.y > padding && sp.y < offsetY) {
      ctx.fillText(y + '', sp.x - 8, sp.y + 4)
    }
  }
  ctx.restore()

  selectedSchemes.value.forEach((s, idx) => {
    const color = schemeColors[idx % schemeColors.length]
    const pts = s.controlPoints
    if (pts.length < 2) return

    const drawSide = (mirror: number) => {
      ctx.save()
      ctx.strokeStyle = color
      ctx.lineWidth = 2.5
      ctx.globalAlpha = 0.9
      ctx.beginPath()

      const extended = [pts[0], ...pts, pts[pts.length - 1]]
      const first = toScreen(mirror * pts[0].x, pts[0].y)
      ctx.moveTo(first.x, first.y)

      for (let i = 0; i < extended.length - 3; i++) {
        const p0 = { x: mirror * extended[i].x, y: extended[i].y }
        const p1 = { x: mirror * extended[i + 1].x, y: extended[i + 1].y }
        const p2 = { x: mirror * extended[i + 2].x, y: extended[i + 2].y }
        const p3 = { x: mirror * extended[i + 3].x, y: extended[i + 3].y }
        const { cp1x, cp1y, cp2x, cp2y } = catmullRomToBezier(p0 as any, p1 as any, p2 as any, p3 as any)
        const s1 = toScreen(cp1x, cp1y)
        const s2 = toScreen(cp2x, cp2y)
        const ep = toScreen(p2.x, p2.y)
        ctx.bezierCurveTo(s1.x, s1.y, s2.x, s2.y, ep.x, ep.y)
      }
      ctx.stroke()
      ctx.restore()
    }

    drawSide(1)
    drawSide(-1)

    ctx.save()
    ctx.fillStyle = color
    ctx.globalAlpha = 0.08
    ctx.beginPath()
    const start = toScreen(-pts[0].x, pts[0].y)
    ctx.moveTo(start.x, start.y)
    const extR = [pts[0], ...pts, pts[pts.length - 1]]
    for (let i = 0; i < extR.length - 3; i++) {
      const p0 = { x: extR[i].x, y: extR[i].y }
      const p1 = { x: extR[i + 1].x, y: extR[i + 1].y }
      const p2 = { x: extR[i + 2].x, y: extR[i + 2].y }
      const p3 = { x: extR[i + 3].x, y: extR[i + 3].y }
      const { cp1x, cp1y, cp2x, cp2y } = catmullRomToBezier(p0 as any, p1 as any, p2 as any, p3 as any)
      const s1 = toScreen(cp1x, cp1y)
      const s2 = toScreen(cp2x, cp2y)
      const ep = toScreen(p2.x, p2.y)
      ctx.bezierCurveTo(s1.x, s1.y, s2.x, s2.y, ep.x, ep.y)
    }
    const extL = [pts[0], ...pts, pts[pts.length - 1]].reverse()
    for (let i = 0; i < extL.length - 3; i++) {
      const p0 = { x: -extL[i].x, y: extL[i].y }
      const p1 = { x: -extL[i + 1].x, y: extL[i + 1].y }
      const p2 = { x: -extL[i + 2].x, y: extL[i + 2].y }
      const p3 = { x: -extL[i + 3].x, y: extL[i + 3].y }
      const { cp1x, cp1y, cp2x, cp2y } = catmullRomToBezier(p0 as any, p1 as any, p2 as any, p3 as any)
      const s1 = toScreen(cp1x, cp1y)
      const s2 = toScreen(cp2x, cp2y)
      const ep = toScreen(p2.x, p2.y)
      ctx.bezierCurveTo(s1.x, s1.y, s2.x, s2.y, ep.x, ep.y)
    }
    ctx.closePath()
    ctx.fill()
    ctx.restore()
  })
}

function openScheme(s: ProfileScheme) {
  store.selectScheme(s.id)
  router.push('/')
}

onMounted(() => {
  store.loadFromStorage()
  if (store.schemes.length >= 1) {
    selectedIds.value.add(store.schemes[0].id)
  }
  if (store.schemes.length >= 2) {
    selectedIds.value.add(store.schemes[1].id)
  }
  selectedIds.value = new Set(selectedIds.value)
  setTimeout(drawComparison, 50)
  window.addEventListener('resize', drawComparison)
})
</script>

<template>
  <div class="w-screen h-screen flex flex-col overflow-hidden bg-[#F5F0E8]">
    <header class="h-14 flex items-center justify-between px-5 bg-white border-b border-[#E8DFC9] flex-shrink-0">
      <div class="flex items-center gap-3">
        <button
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-[#FAF6ED] border border-[#E8DFC9] text-sm text-[#5D4E2B] transition-colors"
          @click="router.push('/')"
        >
          <ArrowLeft class="w-4 h-4" />
          返回工作台
        </button>
        <div class="h-5 w-px bg-[#E8DFC9]" />
        <h1 class="text-[15px] font-bold text-[#5D4E2B]">
          器型方案对比
        </h1>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-500">
          已选 {{ selectedSchemes.length }} 个方案（最多6个）
        </span>
        <button
          :disabled="selectedSchemes.length < 2"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#5D8A66] text-white text-sm hover:bg-[#4a6f52] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          @click="exportAllComparison"
        >
          <Download class="w-4 h-4" />
          导出对比数据
        </button>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <aside class="w-72 flex-shrink-0 bg-white border-r border-[#E8DFC9] overflow-y-auto">
        <div class="p-3 border-b border-[#E8DFC9] bg-[#FAF6ED]">
          <h3 class="text-sm font-bold text-[#5D4E2B] mb-2">方案列表（点击选择对比）</h3>
          <p class="text-[11px] text-gray-500">最多同时对比 6 个方案</p>
        </div>
        <div class="p-2 space-y-2">
          <div
            v-for="(s, idx) in store.schemes"
            :key="s.id"
            :class="[
              'relative p-2.5 rounded-lg border cursor-pointer transition-all',
              selectedIds.has(s.id)
                ? 'bg-[#5D8A66]/5 border-[#5D8A66] shadow-sm'
                : 'bg-white border-[#E8DFC9] hover:bg-[#FAF6ED]'
            ]"
            @click="toggleSelect(s.id)"
          >
            <div
              v-if="selectedIds.has(s.id)"
              class="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center"
              :style="{ background: schemeColors[selectedSchemes.findIndex(x => x.id === s.id) % schemeColors.length] }"
            >
              <Check class="w-3 h-3 text-white" />
            </div>
            <div class="flex items-start gap-2 pr-6">
              <svg width="36" height="50" viewBox="0 0 36 50" class="flex-shrink-0 rounded border border-[#E8DFC9] bg-[#F5F0E8]">
                <path
                  v-if="s.controlPoints.length >= 2"
                  :d="(() => {
                    const pts = s.controlPoints
                    const maxX = Math.max(...pts.map(p => p.x), 1)
                    const maxY = Math.max(...pts.map(p => p.y), 1)
                    return pts.map((p, i) => {
                      const x = 18 + (p.x / maxX) * 16
                      const y = 44 - (p.y / maxY) * 40
                      return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
                    }).join(' ') + ' L18,' + (44 - (pts[0].y / maxY) * 40).toFixed(1) + ' Z'
                  })()"
                  :fill="schemeColors[store.schemes.indexOf(s) % schemeColors.length]"
                  fill-opacity="0.3"
                  :stroke="schemeColors[store.schemes.indexOf(s) % schemeColors.length]"
                  stroke-width="1"
                />
              </svg>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-[#5D4E2B] truncate">{{ s.name }}</div>
                <div class="text-[10px] text-gray-500 mt-0.5">
                  {{ s.controlPoints.length }}点 · {{ s.unit }} · {{ s.repairMarks.length }}修坯
                </div>
                <div class="flex gap-1 mt-1.5">
                  <button
                    class="px-1.5 py-0.5 text-[10px] rounded bg-[#F5F0E8] text-gray-600 hover:bg-[#E8DFC9]"
                    @click.stop="openScheme(s)"
                  >编辑</button>
                  <button
                    class="px-1.5 py-0.5 text-[10px] rounded bg-[#F5F0E8] text-gray-600 hover:bg-[#E8DFC9]"
                    @click.stop="store.duplicateScheme(s.id)"
                  >
                    <Copy class="w-2.5 h-2.5 inline" />
                  </button>
                  <button
                    v-if="store.schemes.length > 1"
                    class="px-1.5 py-0.5 text-[10px] rounded bg-red-50 text-red-600 hover:bg-red-100"
                    @click.stop="store.deleteScheme(s.id)"
                  >
                    <Trash2 class="w-2.5 h-2.5 inline" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <button
            class="w-full py-2.5 rounded-lg border-2 border-dashed border-[#E8DFC9] text-gray-400 text-xs hover:border-[#5D8A66] hover:text-[#5D8A66] hover:bg-[#5D8A66]/5 transition-colors flex items-center justify-center gap-1"
            @click="store.createNewScheme()"
          >
            <Plus class="w-3.5 h-3.5" /> 新建方案
          </button>
        </div>
      </aside>

      <main class="flex-1 flex flex-col overflow-hidden p-4 gap-4">
        <div class="flex-1 min-h-0 bg-white rounded-lg border border-[#E8DFC9] overflow-hidden">
          <div class="h-full w-full p-4">
            <canvas ref="compareCanvasRef" class="block" />
          </div>
        </div>

        <div v-if="comparisonResults.length > 0" class="bg-white rounded-lg border border-[#E8DFC9] overflow-hidden">
          <div class="px-4 py-2.5 border-b border-[#E8DFC9] bg-[#FAF6ED]">
            <h3 class="text-sm font-bold text-[#5D4E2B]">尺寸对比表</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-[#F5F0E8] text-xs">
                <tr>
                  <th class="text-left px-4 py-2 text-gray-600 font-semibold">方案</th>
                  <th class="text-right px-4 py-2 text-gray-600 font-semibold">高度</th>
                  <th class="text-right px-4 py-2 text-gray-600 font-semibold">口径</th>
                  <th class="text-right px-4 py-2 text-gray-600 font-semibold">腹径</th>
                  <th class="text-right px-4 py-2 text-gray-600 font-semibold">底径</th>
                  <th class="text-right px-4 py-2 text-gray-600 font-semibold">容量(ml)</th>
                  <th class="text-center px-4 py-2 text-gray-600 font-semibold">单位</th>
                  <th class="text-center px-4 py-2 text-gray-600 font-semibold">状态</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(item, idx) in comparisonResults"
                  :key="item.scheme.id"
                  class="border-t border-[#E8DFC9] hover:bg-[#FAF6ED]"
                >
                  <td class="px-4 py-2.5">
                    <div class="flex items-center gap-2">
                      <span
                        class="w-3 h-3 rounded-full flex-shrink-0"
                        :style="{ background: schemeColors[idx % schemeColors.length] }"
                      />
                      <span class="font-medium text-[#5D4E2B]">{{ item.scheme.name }}</span>
                    </div>
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono text-[#5D4E2B]">
                    {{ item.result.isValid ? item.result.height.toFixed(1) : '--' }}
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono text-[#5D4E2B]">
                    {{ item.result.isValid ? item.result.mouthDiameter.toFixed(1) : '--' }}
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono text-[#5D4E2B]">
                    {{ item.result.isValid ? item.result.bellyDiameter.toFixed(1) : '--' }}
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono text-[#5D4E2B]">
                    {{ item.result.isValid ? item.result.bottomDiameter.toFixed(1) : '--' }}
                  </td>
                  <td class="px-4 py-2.5 text-right font-mono text-[#5D8A66] font-semibold">
                    {{ item.result.volume !== null && item.result.isValid ? item.result.volume.toFixed(1) : '--' }}
                  </td>
                  <td class="px-4 py-2.5 text-center text-gray-500">{{ item.scheme.unit }}</td>
                  <td class="px-4 py-2.5 text-center">
                    <span
                      v-if="item.validation.isValid"
                      class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 text-green-700 text-[10px]"
                    >
                      <Check class="w-3 h-3" /> 有效
                    </span>
                    <span v-else class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-50 text-red-700 text-[10px]">
                      无效
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
