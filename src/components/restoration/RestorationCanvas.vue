<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import type { ControlPoint, RestorationPoint } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { catmullRomToBezier, sampleCurvePoints, validateProfile } from '@/utils/geometry'

const props = defineProps<{
  showOriginal: boolean
  showRestored: boolean
  showSpeculation: boolean
}>()

const store = useProfileStore()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const dpr = window.devicePixelRatio || 1

const viewConfig = ref({
  padding: 60,
  scale: 2,
  offsetX: 0,
  offsetY: 0,
})

const dragging = ref<number | null>(null)
const hoverPoint = ref<number | null>(null)
const canvasSize = ref({ width: 600, height: 500 })

const originalPoints = computed(() => store.controlPoints)
const restoredPoints = computed(() => store.currentRestoration?.restoredPoints || [])

const allPoints = computed(() => {
  if (!props.showRestored) return originalPoints.value
  return restoredPoints.value
})

const validation = computed(() => {
  if (props.showRestored && restoredPoints.value.length > 0) {
    return validateProfile(restoredPoints.value)
  }
  return validateProfile(originalPoints.value)
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

function findPointAt(sx: number, sy: number, tol: number = 12): RestorationPoint | ControlPoint | null {
  const points = props.showRestored ? restoredPoints.value : originalPoints.value
  for (let i = points.length - 1; i >= 0; i--) {
    const p = points[i]
    const sp = worldToScreen(p.x, p.y)
    const dx = sx - sp.x
    const dy = sy - sp.y
    if (dx * dx + dy * dy <= tol * tol) {
      return p
    }
  }
  return null
}

function getPointConfidence(p: RestorationPoint | ControlPoint): number {
  if ('confidence' in p && typeof p.confidence === 'number') {
    return p.confidence
  }
  return 1.0
}

function isRestorationPoint(p: RestorationPoint | ControlPoint): p is RestorationPoint {
  return 'source' in p
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
    const isRestored = isRestorationPoint(p) && p.source === 'restored'
    store.selectPoint(p.id)
    if (isRestored) {
      dragging.value = p.id
    }
  }
}

function onMouseMove(e: MouseEvent) {
  const { x, y } = getCanvasLocal(e)
  if (dragging.value !== null) {
    const w = screenToWorld(x, y)
    store.updateRestorationPointPos(dragging.value, w.x, w.y)
  } else {
    const p = findPointAt(x, y)
    hoverPoint.value = p ? p.id : null
  }
}

function onMouseUp() {
  dragging.value = null
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
  const pts = allPoints.value
  if (pts.length === 0) return
  const maxX = Math.max(...pts.map(p => p.x), 100)
  const maxY = Math.max(...pts.map(p => p.y), 200)
  const availW = canvasSize.value.width - 2 * viewConfig.value.padding - 40
  const availH = canvasSize.value.height - 2 * viewConfig.value.padding - 40
  const s = Math.min(availW / (maxX * 1.3), availH / (maxY * 1.2))
  viewConfig.value.scale = Math.max(0.5, s)
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return '#4CAF50'
  if (confidence >= 0.6) return '#FF9800'
  if (confidence >= 0.4) return '#FF5722'
  return '#F44336'
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

  if (props.showOriginal && originalPoints.value.length > 0) {
    drawMirroredProfile(ctx, originalPoints.value, 'rgba(93, 138, 102, 0.3)')
    drawProfileCurve(ctx, originalPoints.value, '#5D8A66', 2.5, false)
  }

  if (props.showRestored && restoredPoints.value.length > 0) {
    if (props.showOriginal) {
      drawMirroredProfile(ctx, restoredPoints.value, 'rgba(139, 105, 20, 0.2)')
      drawRestoredCurve(ctx)
    } else {
      drawMirroredProfile(ctx, restoredPoints.value, 'rgba(139, 105, 20, 0.3)')
      drawRestoredCurve(ctx)
    }
  }

  if (props.showSpeculation && restoredPoints.value.length > 0) {
    drawSpeculationInterval(ctx)
  }

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

function drawProfileCurve(
  ctx: CanvasRenderingContext2D,
  pts: ControlPoint[],
  color: string,
  lineWidth: number,
  dashed: boolean
) {
  if (pts.length < 2) return

  ctx.save()
  ctx.lineWidth = lineWidth
  ctx.strokeStyle = color
  if (dashed) ctx.setLineDash([6, 4])
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
  ctx.restore()
}

function drawRestoredCurve(ctx: CanvasRenderingContext2D) {
  const pts = restoredPoints.value
  if (pts.length < 2) return

  ctx.save()
  ctx.lineWidth = 3
  ctx.strokeStyle = '#8B6914'
  ctx.beginPath()

  const extended = [pts[0], ...pts, pts[pts.length - 1]]
  let currentSource = pts[0].source

  const firstSP = worldToScreen(pts[0].x, pts[0].y)
  ctx.moveTo(firstSP.x, firstSP.y)

  for (let i = 0; i < extended.length - 3; i++) {
    const p0 = extended[i + 1]
    const p1 = extended[i + 2]
    const isRestoredSegment = (p0.source === 'restored' || p1.source === 'restored')

    if (isRestoredSegment) {
      ctx.strokeStyle = '#E65100'
      ctx.setLineDash([8, 4])
    } else {
      ctx.strokeStyle = '#5D8A66'
      ctx.setLineDash([])
    }

    const { cp1x, cp1y, cp2x, cp2y } = catmullRomToBezier(
      extended[i], extended[i + 1], extended[i + 2], extended[i + 3]
    )
    const s1 = worldToScreen(cp1x, cp1y)
    const s2 = worldToScreen(cp2x, cp2y)
    const ep = worldToScreen(extended[i + 2].x, extended[i + 2].y)
    ctx.bezierCurveTo(s1.x, s1.y, s2.x, s2.y, ep.x, ep.y)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(ep.x, ep.y)
  }

  ctx.restore()
}

function drawMirroredProfile(
  ctx: CanvasRenderingContext2D,
  pts: ControlPoint[],
  color: string
) {
  if (pts.length < 2) return

  ctx.save()
  ctx.lineWidth = 1.5
  ctx.strokeStyle = color
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

function drawSpeculationInterval(ctx: CanvasRenderingContext2D) {
  const pts = restoredPoints.value
  if (pts.length < 2) return

  const restoration = store.currentRestoration
  if (!restoration) return

  const intervals = restoration.specIntervals
  if (!intervals || intervals.length === 0) return

  ctx.save()

  for (const interval of intervals) {
    const startSP = worldToScreen(0, interval.yStart)
    const endSP = worldToScreen(0, interval.yEnd)
    const topY = Math.min(startSP.y, endSP.y)
    const bottomY = Math.max(startSP.y, endSP.y)

    ctx.fillStyle = 'rgba(230, 81, 0, 0.08)'
    ctx.fillRect(
      viewConfig.value.padding - 30,
      topY,
      canvasSize.value.width - 2 * viewConfig.value.padding + 60,
      bottomY - topY
    )

    ctx.strokeStyle = 'rgba(230, 81, 0, 0.3)'
    ctx.setLineDash([4, 4])
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(viewConfig.value.padding - 30, startSP.y)
    ctx.lineTo(canvasSize.value.width - viewConfig.value.padding + 30, startSP.y)
    ctx.moveTo(viewConfig.value.padding - 30, endSP.y)
    ctx.lineTo(canvasSize.value.width - viewConfig.value.padding + 30, endSP.y)
    ctx.stroke()

    ctx.fillStyle = '#E65100'
    ctx.font = 'bold 11px sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText(
      interval.label,
      canvasSize.value.width - viewConfig.value.padding + 25,
      (topY + bottomY) / 2 + 4
    )
  }

  ctx.restore()
}

function drawControlPoints(ctx: CanvasRenderingContext2D) {
  const pts = props.showRestored ? restoredPoints.value : originalPoints.value
  ctx.save()

  for (let i = 0; i < pts.length; i++) {
    const p = pts[i]
    const sp = worldToScreen(p.x, p.y)
    const isSelected = store.selectedPointId === p.id
    const isHover = hoverPoint.value === p.id
    const isRestored = isRestorationPoint(p) && p.source === 'restored'
    const confidence = getPointConfidence(p)

    if (isRestored) {
      ctx.fillStyle = getConfidenceColor(confidence)
      ctx.beginPath()
      ctx.arc(sp.x, sp.y, 11, 0, Math.PI * 2)
      ctx.fill()
    }

    ctx.beginPath()
    ctx.arc(sp.x, sp.y, isSelected ? 8 : 6, 0, Math.PI * 2)

    if (isSelected) {
      ctx.fillStyle = '#1565C0'
    } else if (isHover) {
      ctx.fillStyle = isRestored ? '#E65100' : '#5D8A66'
    } else {
      ctx.fillStyle = isRestored ? '#8B6914' : '#5D8A66'
    }

    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()

    if (isSelected || isHover) {
      ctx.fillStyle = '#333'
      ctx.font = 'bold 11px sans-serif'
      ctx.textAlign = 'left'
      const confText = isRestored ? ` (可信度: ${(confidence * 100).toFixed(0)}%)` : ''
      ctx.fillText(`(${p.x.toFixed(0)}, ${p.y.toFixed(0)})${confText}`, sp.x + 12, sp.y - 10)
    }

    ctx.fillStyle = '#666'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    let label = String(i + 1)
    if (i === 0) label = '①底'
    else if (i === pts.length - 1) label = '①口'
    ctx.fillText(label, sp.x, sp.y + 20)

    if (isRestored) {
      ctx.fillStyle = '#E65100'
      ctx.font = 'bold 9px sans-serif'
      ctx.fillText('?', sp.x, sp.y + 3)
    }
  }
  ctx.restore()
}

function drawDimensionLines(ctx: CanvasRenderingContext2D) {
  if (!validation.value.isValid || allPoints.value.length < 2) return
  const pts = allPoints.value
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
  () => [
    store.controlPoints,
    store.currentRestoration,
    store.selectedPointId,
    props.showOriginal,
    props.showRestored,
    props.showSpeculation,
  ],
  () => {
    draw()
  },
  { deep: true }
)

defineExpose({
  refresh: draw,
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
    />
    <div class="absolute top-3 left-3 flex flex-col gap-1 text-xs">
      <div class="px-2 py-1 bg-white/80 backdrop-blur rounded border border-[#E8DFC9]">
        拖动<span class="text-orange-600 font-semibold">橙色控制点</span>可手动调整复原段
      </div>
      <div class="px-2 py-1 bg-white/80 backdrop-blur rounded border border-[#E8DFC9]">
        <span class="inline-block w-3 h-3 rounded-full bg-[#5D8A66] mr-1"></span>原始点
        <span class="inline-block w-3 h-3 rounded-full bg-[#8B6914] ml-2 mr-1"></span>复原点
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
