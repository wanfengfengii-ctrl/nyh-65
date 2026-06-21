<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import type { ControlPoint, KeyPart } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { catmullRomToBezier, sampleCurvePoints, checkSelfIntersection, validateProfile } from '@/utils/geometry'

const store = useProfileStore()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const dpr = window.devicePixelRatio || 1

const viewConfig = ref({
  padding: 50,
  scale: 2,
  offsetX: 0,
  offsetY: 0,
})

const dragging = ref<number | null>(null)
const hoverPoint = ref<number | null>(null)
const canvasSize = ref({ width: 600, height: 500 })

const validation = computed(() => validateProfile(store.controlPoints))
const hasSelfIntersection = computed(() => {
  if (store.controlPoints.length < 2) return false
  const sampled = sampleCurvePoints(store.controlPoints, 15)
  return checkSelfIntersection(sampled)
})

function worldToScreen(wx: number, wy: number): { x: number; y: number } {
  const { padding, scale, offsetX, offsetY } = viewConfig.value
  const h = canvasSize.value.height
  return {
    x: padding + offsetX + wx * scale,
    y: h - padding - offsetY - wy * scale,
  }
}

function screenToWorld(sx: number, sy: number): { x: number; y: number } {
  const { padding, scale, offsetX, offsetY } = viewConfig.value
  const h = canvasSize.value.height
  return {
    x: (sx - padding - offsetX) / scale,
    y: (h - padding - offsetY - sy) / scale,
  }
}

function findPointAt(sx: number, sy: number, tol: number = 12): ControlPoint | null {
  for (let i = store.controlPoints.length - 1; i >= 0; i--) {
    const p = store.controlPoints[i]
    const sp = worldToScreen(p.x, p.y)
    const dx = sx - sp.x
    const dy = sy - sp.y
    if (dx * dx + dy * dy <= tol * tol) {
      return p
    }
  }
  return null
}

function getCanvasLocal(e: MouseEvent): { x: number; y: number } {
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
  }
}

function onMouseDown(e: MouseEvent) {
  const { x, y } = getCanvasLocal(e)
  const p = findPointAt(x, y)
  if (p) {
    dragging.value = p.id
    store.selectPoint(p.id)
  }
}

function onMouseMove(e: MouseEvent) {
  const { x, y } = getCanvasLocal(e)
  if (dragging.value !== null) {
    const w = screenToWorld(x, y)
    store.updatePoint(dragging.value, w.x, w.y)
  } else {
    const p = findPointAt(x, y)
    hoverPoint.value = p ? p.id : null
  }
}

function onMouseUp() {
  dragging.value = null
}

function onDoubleClick(e: MouseEvent) {
  const { x, y } = getCanvasLocal(e)
  const w = screenToWorld(x, y)
  store.addPoint(w.x, w.y)
}

function resize() {
  if (!containerRef.value || !canvasRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  canvasSize.value = { width: rect.width, height: rect.height }
  const canvas = canvasRef.value
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  canvas.style.width = rect.width + 'px'
  canvas.style.height = rect.height + 'px'
  autoScale()
  draw()
}

function autoScale() {
  const pts = store.controlPoints
  if (pts.length === 0) return
  const maxX = Math.max(...pts.map(p => p.x), 100)
  const maxY = Math.max(...pts.map(p => p.y), 200)
  const availW = canvasSize.value.width - 2 * viewConfig.value.padding - 40
  const availH = canvasSize.value.height - 2 * viewConfig.value.padding - 40
  const s = Math.min(availW / (maxX * 1.3), availH / (maxY * 1.2))
  viewConfig.value.scale = Math.max(0.5, s)
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, canvasSize.value.width, canvasSize.value.height)

  drawGrid(ctx)
  drawAxis(ctx)
  drawMirroredProfile(ctx)
  drawKeyParts(ctx)
  drawProfileCurve(ctx)
  drawRepairMarks(ctx)
  drawControlPoints(ctx)
  drawDimensionLines(ctx)
}

function drawGrid(ctx: CanvasRenderingContext2D) {
  const { padding, scale } = viewConfig.value
  const { width, height } = canvasSize.value
  ctx.save()
  ctx.strokeStyle = 'rgba(139, 105, 20, 0.08)'
  ctx.lineWidth = 1

  const gridStep = 50
  const w = (width - 2 * padding) / scale
  const h = (height - 2 * padding) / scale

  for (let x = 0; x <= w; x += gridStep) {
    const sp = worldToScreen(x, 0)
    ctx.beginPath()
    ctx.moveTo(sp.x, padding)
    ctx.lineTo(sp.x, height - padding)
    ctx.stroke()
  }
  for (let y = 0; y <= h; y += gridStep) {
    const sp = worldToScreen(0, y)
    ctx.beginPath()
    ctx.moveTo(padding - 20, sp.y)
    ctx.lineTo(width - padding, sp.y)
    ctx.stroke()
  }
  ctx.restore()
}

function drawAxis(ctx: CanvasRenderingContext2D) {
  const { padding } = viewConfig.value
  const { width, height } = canvasSize.value
  ctx.save()

  ctx.strokeStyle = '#8B6914'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  const axisOrigin = worldToScreen(0, 0)
  ctx.moveTo(axisOrigin.x, padding - 10)
  ctx.lineTo(axisOrigin.x, height - padding + 10)
  ctx.stroke()

  ctx.fillStyle = '#8B6914'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'center'
  for (let y = 0; y <= 300; y += 50) {
    const sp = worldToScreen(0, y)
    if (sp.y > padding && sp.y < height - padding) {
      ctx.fillText(y + store.unit, axisOrigin.x - 18, sp.y + 4)
      ctx.beginPath()
      ctx.moveTo(axisOrigin.x - 4, sp.y)
      ctx.lineTo(axisOrigin.x + 4, sp.y)
      ctx.stroke()
    }
  }
  ctx.textAlign = 'center'
  for (let x = 0; x <= 200; x += 50) {
    const sp = worldToScreen(x, 0)
    if (sp.x > padding && sp.x < width - padding) {
      ctx.fillText(x + store.unit, sp.x, height - padding + 22)
      ctx.beginPath()
      ctx.moveTo(sp.x, axisOrigin.y - 4)
      ctx.lineTo(sp.x, axisOrigin.y + 4)
      ctx.stroke()
    }
  }
  ctx.restore()
}

function drawProfileCurve(ctx: CanvasRenderingContext2D) {
  const pts = store.controlPoints
  if (pts.length < 2) return

  ctx.save()
  ctx.lineWidth = 2.5
  ctx.strokeStyle = hasSelfIntersection.value ? '#E53935' : '#5D8A66'
  ctx.beginPath()

  const extended = [pts[0], ...pts, pts[pts.length - 1]]
  const firstSP = worldToScreen(pts[0].x, pts[0].y)
  ctx.moveTo(firstSP.x, firstSP.y)

  for (let i = 0; i < extended.length - 3; i++) {
    const p0 = extended[i]
    const p1 = extended[i + 1]
    const p2 = extended[i + 2]
    const p3 = extended[i + 3]
    const { cp1x, cp1y, cp2x, cp2y } = catmullRomToBezier(p0, p1, p2, p3)
    const s1 = worldToScreen(cp1x, cp1y)
    const s2 = worldToScreen(cp2x, cp2y)
    const ep = worldToScreen(p2.x, p2.y)
    ctx.bezierCurveTo(s1.x, s1.y, s2.x, s2.y, ep.x, ep.y)
  }

  ctx.stroke()

  const origin = worldToScreen(0, pts[0].y)
  const origin2 = worldToScreen(0, pts[pts.length - 1].y)
  ctx.strokeStyle = 'rgba(93, 138, 102, 0.4)'
  ctx.setLineDash([4, 4])
  ctx.beginPath()
  ctx.moveTo(firstSP.x, firstSP.y)
  ctx.lineTo(origin.x, origin.y)
  ctx.moveTo(worldToScreen(pts[pts.length - 1].x, pts[pts.length - 1].y).x, worldToScreen(pts[pts.length - 1].x, pts[pts.length - 1].y).y)
  ctx.lineTo(origin2.x, origin2.y)
  ctx.stroke()
  ctx.restore()
}

function drawMirroredProfile(ctx: CanvasRenderingContext2D) {
  const pts = store.controlPoints
  if (pts.length < 2) return

  ctx.save()
  ctx.lineWidth = 1.5
  ctx.strokeStyle = 'rgba(93, 138, 102, 0.25)'
  ctx.setLineDash([6, 4])
  ctx.beginPath()

  const extended = [pts[0], ...pts, pts[pts.length - 1]]
  const firstSP = worldToScreen(-pts[0].x, pts[0].y)
  ctx.moveTo(firstSP.x, firstSP.y)

  for (let i = 0; i < extended.length - 3; i++) {
    const p0 = { ...extended[i], x: -extended[i].x }
    const p1 = { ...extended[i + 1], x: -extended[i + 1].x }
    const p2 = { ...extended[i + 2], x: -extended[i + 2].x }
    const p3 = { ...extended[i + 3], x: -extended[i + 3].x }
    const { cp1x, cp1y, cp2x, cp2y } = catmullRomToBezier(p0, p1, p2, p3)
    const s1 = worldToScreen(cp1x, cp1y)
    const s2 = worldToScreen(cp2x, cp2y)
    const ep = worldToScreen(p2.x, p2.y)
    ctx.bezierCurveTo(s1.x, s1.y, s2.x, s2.y, ep.x, ep.y)
  }
  ctx.stroke()
  ctx.restore()
}

const KEY_PART_COLORS: Record<string, { fill: string; stroke: string; text: string }> = {
  '底部': { fill: 'rgba(139, 90, 43, 0.15)', stroke: '#8B5A2B', text: '#5D3A1A' },
  '圈足': { fill: 'rgba(139, 90, 43, 0.18)', stroke: '#A0522D', text: '#5D3A1A' },
  '足': { fill: 'rgba(139, 90, 43, 0.18)', stroke: '#A0522D', text: '#5D3A1A' },
  '腹部': { fill: 'rgba(93, 138, 102, 0.18)', stroke: '#5D8A66', text: '#3A5A40' },
  '腹': { fill: 'rgba(93, 138, 102, 0.18)', stroke: '#5D8A66', text: '#3A5A40' },
  '肩部': { fill: 'rgba(0, 128, 128, 0.18)', stroke: '#008080', text: '#005555' },
  '肩': { fill: 'rgba(0, 128, 128, 0.18)', stroke: '#008080', text: '#005555' },
  '颈部': { fill: 'rgba(123, 31, 162, 0.15)', stroke: '#7B1FA2', text: '#4A148C' },
  '颈': { fill: 'rgba(123, 31, 162, 0.15)', stroke: '#7B1FA2', text: '#4A148C' },
  '口沿': { fill: 'rgba(229, 57, 53, 0.15)', stroke: '#E53935', text: '#B71C1C' },
  '口': { fill: 'rgba(229, 57, 53, 0.15)', stroke: '#E53935', text: '#B71C1C' },
}

function getKeyPartColor(name: string) {
  return KEY_PART_COLORS[name] || { fill: 'rgba(158, 158, 158, 0.15)', stroke: '#9E9E9E', text: '#616161' }
}

function drawKeyParts(ctx: CanvasRenderingContext2D) {
  const parts = store.keyParts
  const pts = store.controlPoints
  if (parts.length === 0 || pts.length < 2) return

  const sampled = sampleCurvePoints(pts, 60)
  if (sampled.length === 0) return

  ctx.save()

  for (const part of parts) {
    const { startY, endY, name, diameter, confidence } = part
    if (startY === undefined || endY === undefined) continue
    if (Math.abs(endY - startY) < 0.001) continue

    const color = getKeyPartColor(name)

    const topScreen = worldToScreen(0, Math.max(startY, endY))
    const botScreen = worldToScreen(0, Math.min(startY, endY))
    const yTop = topScreen.y
    const yBot = botScreen.y
    const axisX = topScreen.x

    const sampleCount = 20
    const regionPoints: { x: number; y: number }[] = []
    for (let i = 0; i <= sampleCount; i++) {
      const t = i / sampleCount
      const y = startY + (endY - startY) * t
      let r = 0
      let nearest: any = null
      let minDist = Infinity
      for (const sp of sampled) {
        const d = Math.abs(sp.y - y)
        if (d < minDist) {
          minDist = d
          nearest = sp
        }
      }
      if (nearest) {
        r = nearest.x
      }
      const sp1 = worldToScreen(r, y)
      const sp2 = worldToScreen(-r, y)
      regionPoints.push({ x: sp1.x, y: sp1.y })
      regionPoints.unshift({ x: sp2.x, y: sp2.y })
    }

    if (regionPoints.length > 0) {
      ctx.beginPath()
      ctx.moveTo(regionPoints[0].x, regionPoints[0].y)
      for (let i = 1; i < regionPoints.length; i++) {
        ctx.lineTo(regionPoints[i].x, regionPoints[i].y)
      }
      ctx.closePath()
      ctx.fillStyle = color.fill
      ctx.fill()
    }

    ctx.strokeStyle = color.stroke
    ctx.lineWidth = 1
    ctx.setLineDash([4, 3])
    ctx.beginPath()
    ctx.moveTo(axisX - 30, yTop)
    ctx.lineTo(axisX + 30, yTop)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(axisX - 30, yBot)
    ctx.lineTo(axisX + 30, yBot)
    ctx.stroke()
    ctx.setLineDash([])

    let maxR = 0
    for (const sp of sampled) {
      if (sp.y >= Math.min(startY, endY) && sp.y <= Math.max(startY, endY)) {
        if (sp.x > maxR) maxR = sp.x
      }
    }
    const labelY = (yTop + yBot) / 2
    const labelSP = worldToScreen(maxR + 8, (startY + endY) / 2)
    const labelText = diameter !== undefined
      ? `${name} ${diameter.toFixed(0)}${store.unit}`
      : name
    const confText = confidence !== undefined ? ` ${(confidence * 100).toFixed(0)}%` : ''

    ctx.font = 'bold 10.5px sans-serif'
    ctx.textAlign = 'left'
    const textWidth = ctx.measureText(labelText + confText).width
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'
    ctx.fillRect(labelSP.x - 2, labelY - 9, textWidth + 10, 16)
    ctx.strokeStyle = color.stroke
    ctx.lineWidth = 0.8
    ctx.strokeRect(labelSP.x - 2, labelY - 9, textWidth + 10, 16)
    ctx.fillStyle = color.text
    ctx.fillText(labelText, labelSP.x + 3, labelY + 2.5)
    if (confText) {
      ctx.fillStyle = confidence && confidence < 0.6 ? '#E65100' : '#555'
      ctx.font = '10px sans-serif'
      ctx.fillText(confText, labelSP.x + 3 + ctx.measureText(labelText).width, labelY + 2.5)
    }
  }

  ctx.restore()
}

function drawControlPoints(ctx: CanvasRenderingContext2D) {
  const pts = store.controlPoints
  const repairPointIds = new Set(store.repairMarks.map(r => r.pointId))
  ctx.save()

  for (let i = 0; i < pts.length; i++) {
    const p = pts[i]
    const sp = worldToScreen(p.x, p.y)
    const isSelected = store.selectedPointId === p.id
    const isHover = hoverPoint.value === p.id
    const isRepair = repairPointIds.has(p.id)

    if (isRepair) {
      ctx.fillStyle = '#FF7043'
      ctx.beginPath()
      ctx.arc(sp.x, sp.y, 11, 0, Math.PI * 2)
      ctx.fill()
    }

    ctx.beginPath()
    ctx.arc(sp.x, sp.y, isSelected ? 8 : 6, 0, Math.PI * 2)
    ctx.fillStyle = isSelected ? '#1565C0' : isHover ? '#5D8A66' : '#8B6914'
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()

    if (isSelected || isHover) {
      ctx.fillStyle = '#333'
      ctx.font = 'bold 11px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`(${p.x.toFixed(0)}, ${p.y.toFixed(0)})`, sp.x + 12, sp.y - 10)
    }

    ctx.fillStyle = '#666'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    let label = String(i + 1)
    if (i === 0) label = '①底'
    else if (i === pts.length - 1) label = '①口'
    ctx.fillText(label, sp.x, sp.y + 20)
  }
  ctx.restore()
}

function drawRepairMarks(ctx: CanvasRenderingContext2D) {
  if (store.repairMarks.length === 0) return
  const pts = store.controlPoints
  const pointMap = new Map(pts.map(p => [p.id, p]))
  ctx.save()
  ctx.fillStyle = '#FF7043'
  ctx.font = 'bold 14px sans-serif'
  ctx.textAlign = 'left'
  for (const m of store.repairMarks) {
    const p = pointMap.get(m.pointId)
    if (p) {
      const sp = worldToScreen(p.x, p.y)
      ctx.fillText('⚒', sp.x + 10, sp.y - 14)
    }
  }
  ctx.restore()
}

function drawDimensionLines(ctx: CanvasRenderingContext2D) {
  if (!validation.value.isValid || store.controlPoints.length < 2) return
  const pts = store.controlPoints
  const sampled = sampleCurvePoints(pts, 30)
  if (sampled.length === 0) return

  const top = sampled.reduce((b, p) => (p.y > b.y ? p : b), sampled[0])
  const bottom = sampled.reduce((b, p) => (p.y < b.y ? p : b), sampled[0])
  const belly = sampled.reduce((b, p) => (p.x > b.x ? p : b), sampled[0])

  ctx.save()
  ctx.strokeStyle = 'rgba(21, 101, 192, 0.6)'
  ctx.fillStyle = '#1565C0'
  ctx.lineWidth = 1
  ctx.setLineDash([3, 3])
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'left'

  const offsetX = 180
  const botSP = worldToScreen(0, bottom.y)
  const topSP = worldToScreen(0, top.y)
  ctx.beginPath()
  ctx.moveTo(botSP.x - offsetX, botSP.y)
  ctx.lineTo(topSP.x - offsetX, topSP.y)
  ctx.stroke()
  ctx.setLineDash([])
  ctx.beginPath()
  ctx.moveTo(botSP.x - offsetX - 4, botSP.y)
  ctx.lineTo(botSP.x - offsetX + 4, botSP.y)
  ctx.moveTo(topSP.x - offsetX - 4, topSP.y)
  ctx.lineTo(topSP.x - offsetX + 4, topSP.y)
  ctx.stroke()
  ctx.fillText('H', botSP.x - offsetX - 14, (botSP.y + topSP.y) / 2 + 4)

  ctx.restore()
}

onMounted(() => {
  resize()
  window.addEventListener('resize', resize)
  draw()
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
})

watch(
  () => [store.controlPoints, store.unit, store.selectedPointId, store.repairMarks, store.keyParts],
  () => {
    draw()
  },
  { deep: true }
)

const emit = defineEmits<{
  (e: 'delete-point', id: number): void
}>()

defineExpose({
  refresh: draw,
  addWorldPoint: (x: number, y: number) => store.addPoint(x, y),
})
</script>

<template>
  <div ref="containerRef" class="relative w-full h-full bg-[#FAF6ED] rounded-lg overflow-hidden border border-[#E8DFC9]">
    <canvas
      ref="canvasRef"
      class="block cursor-crosshair"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
      @dblclick="onDoubleClick"
      @contextmenu.prevent="(e) => {
        const local = getCanvasLocal(e as any)
        const p = findPointAt(local.x, local.y)
        if (p) emit('delete-point', p.id)
      }"
    />
    <div class="absolute top-3 left-3 flex flex-col gap-1 text-xs">
      <div class="px-2 py-1 bg-white/80 backdrop-blur rounded border border-[#E8DFC9]">
        双击画布添加控制点
      </div>
      <div class="px-2 py-1 bg-white/80 backdrop-blur rounded border border-[#E8DFC9]">
        右键控制点删除
      </div>
    </div>
    <div class="absolute top-3 right-3 flex flex-col gap-1 items-end text-xs">
      <div
        v-if="validation.errors.length > 0"
        class="px-2 py-1 bg-red-50 text-red-700 rounded border border-red-200 max-w-[260px]"
      >
        <div class="font-semibold mb-0.5">⚠ 校验不通过</div>
        <div v-for="(err, i) in validation.errors" :key="i" class="opacity-80">· {{ err }}</div>
      </div>
      <div
        v-if="validation.warnings.length > 0"
        class="px-2 py-1 bg-amber-50 text-amber-700 rounded border border-amber-200 max-w-[260px]"
      >
        <div class="font-semibold mb-0.5">提示</div>
        <div v-for="(w, i) in validation.warnings" :key="i" class="opacity-80">· {{ w }}</div>
      </div>
    </div>
  </div>
</template>
