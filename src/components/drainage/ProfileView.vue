<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { MapPin, ArrowDown, Download, Info, FileJson, Image } from 'lucide-vue-next'
import { api } from '@/lib/api'
import type { ProfileResult } from '@/types'

const props = defineProps<{
  culvertId: number | undefined
}>()

const result = ref<ProfileResult | null>(null)
const loading = ref(false)
const showTooltip = ref(false)
const tooltipPoint = ref<any>(null)
const generatingReport = ref(false)
const showExportMenu = ref(false)

async function loadProfile() {
  if (!props.culvertId) return
  loading.value = true
  try {
    result.value = await api.analysis.profile(props.culvertId)
  } catch (e) {
    console.error('加载纵断面图失败', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.culvertId, (id) => {
  if (id) {
    loadProfile()
  }
}, { immediate: true })

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.relative') && showExportMenu.value) {
    showExportMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const svgWidth = ref(800)
const svgHeight = ref(400)
const padding = { top: 40, right: 40, bottom: 60, left: 60 }

const chartWidth = computed(() => svgWidth.value - padding.left - padding.right)
const chartHeight = computed(() => svgHeight.value - padding.top - padding.bottom)

const xScale = computed(() => {
  if (!result.value?.profile_points.length) return () => 0
  const stations = result.value.profile_points.map(p => p.station)
  const min = Math.min(...stations)
  const max = Math.max(...stations)
  return (station: number) => ((station - min) / (max - min || 1)) * chartWidth.value + padding.left
})

const yScale = computed(() => {
  if (!result.value) return () => 0
  const range = result.value.max_elevation - result.value.min_elevation
  const paddingRange = range * 0.2
  const min = result.value.min_elevation - paddingRange
  const max = result.value.max_elevation + paddingRange
  return (elevation: number) => chartHeight.value - ((elevation - min) / (max - min || 1)) * chartHeight.value + padding.top
})

const pathD = computed(() => {
  if (!result.value?.profile_points.length) return ''
  const points = result.value.profile_points
    .filter(p => p.section_width > 0 || p.manhole_name)
    .sort((a, b) => a.station - b.station)

  return points.map((p, i) => {
    const x = xScale.value(p.station)
    const y = yScale.value(p.elevation)
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
  }).join(' ')
})

const xTicks = computed(() => {
  if (!result.value?.profile_points.length) return []
  const stations = result.value.profile_points.map(p => p.station)
  const min = Math.min(...stations)
  const max = Math.max(...stations)
  const step = Math.ceil((max - min) / 5 / 10) * 10
  const ticks = []
  for (let v = min; v <= max; v += step) {
    ticks.push(v)
  }
  return ticks
})

const yTicks = computed(() => {
  if (!result.value) return []
  const range = result.value.max_elevation - result.value.min_elevation
  const paddingRange = range * 0.2
  const min = result.value.min_elevation - paddingRange
  const max = result.value.max_elevation + paddingRange
  const step = Math.ceil((max - min) / 5 / 0.5) * 0.5
  const ticks = []
  for (let v = min; v <= max; v += step) {
    ticks.push(v)
  }
  return ticks
})

function showPointTooltip(point: any, event: MouseEvent) {
  tooltipPoint.value = {
    ...point,
    x: event.offsetX,
    y: event.offsetY
  }
  showTooltip.value = true
}

function hideTooltip() {
  showTooltip.value = false
}

async function exportDataReport() {
  if (!props.culvertId) return
  generatingReport.value = true
  showExportMenu.value = false
  try {
    const reportResult = await api.reports.generate(props.culvertId, 'profile', true)
    window.open(`http://localhost:8001${reportResult.file_url}`, '_blank')
  } catch (e) {
    console.error('导出报告失败', e)
  } finally {
    generatingReport.value = false
  }
}

function exportSvgImage() {
  showExportMenu.value = false
  const svgElement = document.querySelector('.profile-svg-container svg') as SVGSVGElement
  if (!svgElement) return

  const serializer = new XMLSerializer()
  let source = serializer.serializeToString(svgElement)

  if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
    source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"')
  }
  if (!source.match(/^<svg[^>]+"http\:\/\/www\.w3\.org\/1999\/xlink"/)) {
    source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"')
  }

  source = '<?xml version="1.0" standalone="no"?>\r\n' + source

  const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source)
  const link = document.createElement('a')
  link.href = url
  link.download = `纵断面图_${result.value?.culvert_name || 'profile'}_${Date.now()}.svg`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function exportPngImage() {
  showExportMenu.value = false
  const svgElement = document.querySelector('.profile-svg-container svg') as SVGSVGElement
  if (!svgElement) return

  const serializer = new XMLSerializer()
  let source = serializer.serializeToString(svgElement)

  if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
    source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"')
  }

  const svgBlob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(svgBlob)

  const img = new Image()
  img.onload = function() {
    const canvas = document.createElement('canvas')
    canvas.width = svgWidth.value * 2
    canvas.height = svgHeight.value * 2
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.fillStyle = 'white'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.scale(2, 2)
      ctx.drawImage(img, 0, 0)
      URL.revokeObjectURL(url)

      canvas.toBlob(function(blob) {
        if (blob) {
          const pngUrl = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = pngUrl
          link.download = `纵断面图_${result.value?.culvert_name || 'profile'}_${Date.now()}.png`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          URL.revokeObjectURL(pngUrl)
        }
      }, 'image/png')
    }
  }
  img.src = url
}
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-bold text-[#5D4E2B] flex items-center gap-2">
        <span class="inline-block w-1 h-5 bg-[#10B981] rounded"></span>
        纵断面图展示
      </h2>
      <div class="flex items-center gap-2 relative">
        <div class="flex items-center gap-2 text-sm text-gray-500 mr-2">
          <Info class="w-4 h-4" />
          <span>点击图上的点查看详细信息</span>
        </div>
        <div class="relative">
          <button
            :disabled="generatingReport || !result"
            class="px-4 py-1.5 bg-[#5D8A66] text-white text-sm rounded-lg hover:bg-[#4a6f52] transition-colors flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
            @click="showExportMenu = !showExportMenu"
          >
            <Download class="w-4 h-4" />
            导出
          </button>
          <div
            v-if="showExportMenu"
            class="absolute right-0 top-full mt-1 w-44 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20"
          >
            <button
              class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              @click="exportDataReport"
            >
              <FileJson class="w-4 h-4 text-blue-500" />
              导出数据报告 (JSON)
            </button>
            <button
              class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              @click="exportSvgImage"
            >
              <Image class="w-4 h-4 text-green-500" />
              导出图片 (SVG)
            </button>
            <button
              class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              @click="exportPngImage"
            >
              <Image class="w-4 h-4 text-purple-500" />
              导出图片 (PNG)
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 bg-white rounded-xl border border-[#E8DFC9] p-6 overflow-hidden flex flex-col">
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="text-gray-500">加载中...</div>
      </div>
      <div v-else-if="!result || result.profile_points.length === 0" class="flex-1 flex items-center justify-center">
        <div class="text-gray-500 text-center">
          <MapPin class="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <div>暂无纵断面数据</div>
        </div>
      </div>
      <div v-else class="flex-1 flex flex-col overflow-hidden">
        <div class="grid grid-cols-4 gap-4 mb-4">
          <div class="p-3 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
            <div class="text-xs text-blue-600 mb-1">暗渠名称</div>
            <div class="text-base font-bold text-blue-700 truncate">{{ result.culvert_name }}</div>
          </div>
          <div class="p-3 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
            <div class="text-xs text-green-600 mb-1">最高高程</div>
            <div class="text-base font-bold text-green-700">{{ result.max_elevation.toFixed(2) }} m</div>
          </div>
          <div class="p-3 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg border border-orange-200">
            <div class="text-xs text-orange-600 mb-1">最低高程</div>
            <div class="text-base font-bold text-orange-700">{{ result.min_elevation.toFixed(2) }} m</div>
          </div>
          <div class="p-3 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
            <div class="text-xs text-purple-600 mb-1">平均坡度</div>
            <div class="text-base font-bold text-purple-700">{{ (result.avg_slope * 1000).toFixed(2) }}‰</div>
          </div>
        </div>

        <div class="flex-1 relative overflow-auto bg-gray-50 rounded-lg border border-gray-200 p-4 profile-svg-container">
          <svg :width="svgWidth" :height="svgHeight" class="mx-auto">
            <defs>
              <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:#2563EB;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#10B981;stop-opacity:1" />
              </linearGradient>
              <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#2563EB;stop-opacity:0.3" />
                <stop offset="100%" style="stop-color:#2563EB;stop-opacity:0.05" />
              </linearGradient>
            </defs>

            <line
              v-for="tick in xTicks"
              :key="'x' + tick"
              :x1="xScale(tick)"
              :y1="padding.top"
              :x2="xScale(tick)"
              :y2="svgHeight - padding.bottom"
              stroke="#E5E7EB"
              stroke-dasharray="4"
            />
            <line
              v-for="tick in yTicks"
              :key="'y' + tick"
              :x1="padding.left"
              :y1="yScale(tick)"
              :x2="svgWidth - padding.right"
              :y2="yScale(tick)"
              stroke="#E5E7EB"
              stroke-dasharray="4"
            />

            <path
              :d="pathD + ` L ${xScale(result.profile_points[result.profile_points.length - 1]?.station || 0)} ${svgHeight - padding.bottom} L ${padding.left} ${svgHeight - padding.bottom} Z`"
              fill="url(#areaGradient)"
            />

            <path
              :d="pathD"
              fill="none"
              stroke="url(#lineGradient)"
              stroke-width="3"
              stroke-linecap="round"
              stroke-linejoin="round"
            />

            <text
              v-for="tick in xTicks"
              :key="'xt' + tick"
              :x="xScale(tick)"
              :y="svgHeight - padding.bottom + 20"
              text-anchor="middle"
              class="text-xs fill-gray-500"
            >{{ tick }}m</text>

            <text
              v-for="tick in yTicks"
              :key="'yt' + tick"
              :x="padding.left - 10"
              :y="yScale(tick) + 4"
              text-anchor="end"
              class="text-xs fill-gray-500"
            >{{ tick.toFixed(1) }}m</text>

            <text
              :x="svgWidth / 2"
              :y="svgHeight - 10"
              text-anchor="middle"
              class="text-sm fill-gray-600 font-medium"
            >桩号 (m)</text>
            <text
              :x="15"
              :y="svgHeight / 2"
              text-anchor="middle"
              class="text-sm fill-gray-600 font-medium"
              :transform="`rotate(-90, 15, ${svgHeight / 2})`"
            >高程 (m)</text>

            <g v-for="(point, index) in result.profile_points.filter(p => p.section_width > 0 || p.manhole_name)" :key="index">
              <circle
                :cx="xScale(point.station)"
                :cy="yScale(point.elevation)"
                :r="point.manhole_name ? 8 : 5"
                :fill="point.manhole_name ? '#F59E0B' : '#2563EB'"
                class="cursor-pointer hover:opacity-80 transition-opacity"
                stroke="white"
                stroke-width="2"
                @mouseenter="showPointTooltip(point, $event)"
                @mouseleave="hideTooltip"
              />
              <text
                v-if="point.manhole_name"
                :x="xScale(point.station)"
                :y="yScale(point.elevation) - 15"
                text-anchor="middle"
                class="text-xs fill-[#F59E0B] font-medium"
              >{{ point.manhole_name }}</text>
            </g>
          </svg>

          <div
            v-if="showTooltip && tooltipPoint"
            class="absolute bg-white rounded-lg shadow-lg border border-gray-200 p-3 z-10 pointer-events-none"
            :style="{ left: tooltipPoint.x + 20 + 'px', top: tooltipPoint.y + 'px' }"
          >
            <div class="text-xs font-semibold text-gray-700 mb-1">
              {{ tooltipPoint.manhole_name || `桩号 ${tooltipPoint.station}m` }}
            </div>
            <div class="text-xs text-gray-600 space-y-0.5">
              <div>高程: <span class="font-medium">{{ tooltipPoint.elevation.toFixed(2) }}m</span></div>
              <div v-if="tooltipPoint.section_width > 0">
                断面: <span class="font-medium">{{ tooltipPoint.section_width }}m × {{ tooltipPoint.section_height }}m</span>
              </div>
              <div v-if="tooltipPoint.sediment_thickness">
                淤积: <span :class="[
                  'font-medium',
                  tooltipPoint.sediment_thickness >= 0.8 ? 'text-red-600' :
                  tooltipPoint.sediment_thickness >= 0.5 ? 'text-orange-600' : 'text-green-600'
                ]">{{ (tooltipPoint.sediment_thickness * 100).toFixed(1) }}cm</span></div>
            </div>
          </div>
        </div>

        <div class="mt-4 p-4 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
          <h4 class="text-sm font-semibold text-[#5D4E2B] mb-2">图例说明</h4>
          <div class="flex flex-wrap gap-6 text-sm">
            <div class="flex items-center gap-2">
              <div class="w-4 h-4 rounded-full bg-[#2563EB] border-2 border-white"></div>
              <span class="text-gray-600">断面点</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-4 h-4 rounded-full bg-[#F59E0B] border-2 border-white"></div>
              <span class="text-gray-600">检查井</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-8 h-1 bg-gradient-to-r from-[#2563EB] to-[#10B981] rounded"></div>
              <span class="text-gray-600">管底高程线</span>
            </div>
            <div class="flex items-center gap-2">
              <ArrowDown class="w-4 h-4 text-blue-500" />
              <span class="text-gray-600">平均坡度: {{ (result.avg_slope * 1000).toFixed(2) }}‰</span>
            </div>
          </div>
        </div>

        <div class="mt-4 overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">桩号 (m)</th>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">高程 (m)</th>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">断面尺寸</th>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">淤积厚度</th>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">附属设施</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr
                v-for="(point, index) in result.profile_points.filter(p => p.section_width > 0 || p.manhole_name).sort((a, b) => a.station - b.station)"
                :key="index"
                class="hover:bg-gray-50"
              >
                <td class="px-4 py-2 font-medium text-[#5D4E2B]">{{ point.station }}</td>
                <td class="px-4 py-2">{{ point.elevation.toFixed(2) }}</td>
                <td class="px-4 py-2">
                  {{ point.section_width > 0 ? `${point.section_width}m × ${point.section_height}m` : '-' }}
                </td>
                <td class="px-4 py-2">
                  <span v-if="point.sediment_thickness" :class="[
                    'font-medium',
                    point.sediment_thickness >= 0.8 ? 'text-red-600' :
                    point.sediment_thickness >= 0.5 ? 'text-orange-600' : 'text-green-600'
                  ]">{{ (point.sediment_thickness * 100).toFixed(1) }}cm</span>
                  <span v-else class="text-gray-400">-</span>
                </td>
                <td class="px-4 py-2">
                  <span v-if="point.manhole_name" class="text-xs px-2 py-0.5 bg-orange-100 text-orange-700 rounded">
                    {{ point.manhole_name }}
                  </span>
                  <span v-else class="text-gray-400">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
