<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Toolbar from '@/components/Toolbar.vue'
import ProfileCanvas from '@/components/ProfileCanvas.vue'
import VesselPreview3D from '@/components/VesselPreview3D.vue'
import InfoPanel from '@/components/InfoPanel.vue'
import { useProfileStore } from '@/stores/profile'

const store = useProfileStore()
const canvasRef = ref<InstanceType<typeof ProfileCanvas> | null>(null)
const infoRef = ref<InstanceType<typeof InfoPanel> | null>(null)
const preview3DRef = ref<InstanceType<typeof VesselPreview3D> | null>(null)

onMounted(() => {
  store.loadFromStorage()
})

function handleDeletePoint(id: number) {
  store.deletePoint(id)
}
</script>

<template>
  <div class="w-screen h-screen flex flex-col overflow-hidden bg-[#F5F0E8]">
    <header class="h-14 flex items-center justify-between px-5 bg-white border-b border-[#E8DFC9] flex-shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#5D8A66] to-[#8B6914] flex items-center justify-center text-white text-sm font-bold shadow-sm">
          陶
        </div>
        <div>
          <h1 class="text-[15px] font-bold text-[#5D4E2B] leading-tight">
            陶瓷剖面绘制与器型估算系统
          </h1>
          <p class="text-[10px] text-gray-500 leading-tight mt-0.5">
            Ceramic Profile Analysis & Volume Estimation
          </p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <div
          v-if="store.currentScheme"
          class="px-3 py-1 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9] text-xs text-[#5D4E2B]"
        >
          当前方案：
          <span class="font-semibold text-[#5D8A66]">{{ store.currentScheme.name }}</span>
          <span class="text-gray-400 ml-1">（{{ store.controlPoints.length }} 控制点）</span>
        </div>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <Toolbar />

      <main class="flex-1 flex flex-col overflow-hidden p-3 gap-3">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 flex-1 min-h-0">
          <div class="lg:col-span-2 flex flex-col min-h-0">
            <div class="flex items-center justify-between mb-2 flex-shrink-0">
              <h2 class="text-sm font-bold text-[#5D4E2B] flex items-center gap-2">
                <span class="inline-block w-1 h-4 bg-[#5D8A66] rounded"></span>
                剖面曲线绘制（半侧）
              </h2>
              <div class="text-xs text-gray-500">
                沿右侧轮廓从底部到顶部绘制 · Y轴为高度 · X轴为半径
              </div>
            </div>
            <div class="flex-1 min-h-0">
              <ProfileCanvas
                ref="canvasRef"
                @delete-point="handleDeletePoint"
              />
            </div>
          </div>

          <div class="flex flex-col min-h-0">
            <div class="flex items-center justify-between mb-2 flex-shrink-0">
              <h2 class="text-sm font-bold text-[#5D4E2B] flex items-center gap-2">
                <span class="inline-block w-1 h-4 bg-[#8B6914] rounded"></span>
                器型3D预览
              </h2>
            </div>
            <div class="flex-1 min-h-[280px] min-h-0 mb-3">
              <VesselPreview3D ref="preview3DRef" />
            </div>
            <div class="h-auto lg:h-[320px] flex-shrink-0">
              <InfoPanel ref="infoRef" />
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
