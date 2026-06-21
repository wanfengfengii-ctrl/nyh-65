<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import type { ControlPoint, KeyPart } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { sampleCurvePoints, validateProfile } from '@/utils/geometry'

const store = useProfileStore()
const containerRef = ref<HTMLDivElement | null>(null)

let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let controls: OrbitControls | null = null
let latheMesh: THREE.Mesh | null = null
let segmentMeshes: THREE.Mesh[] = []
let wireframe: THREE.LineSegments | null = null
let animationId: number | null = null

const loading = ref(true)
const autoRotate = ref(true)
const showWireframe = ref(false)
const showKeyParts3D = ref(true)

const KEY_PART_HEX_COLORS: Record<string, number> = {
  '底部': 0x8B5A2B,
  '圈足': 0xA0522D,
  '足': 0xA0522D,
  '腹部': 0x5D8A66,
  '腹': 0x5D8A66,
  '肩部': 0x008080,
  '肩': 0x008080,
  '颈部': 0x7B1FA2,
  '颈': 0x7B1FA2,
  '口沿': 0xE53935,
  '口': 0xE53935,
}

function getKeyPartHexColor(name: string): number {
  return KEY_PART_HEX_COLORS[name] || 0x9E9E9E
}

const isValid = computed(() => validateProfile(store.controlPoints).isValid)

function buildLathePoints(points: ControlPoint[]): THREE.Vector2[] {
  const sampled = sampleCurvePoints(points, 40)
  if (sampled.length < 2) return []
  const ys = sampled.map(p => p.y)
  const maxY = Math.max(...ys)
  const scale = 0.02
  return sampled
    .sort((a, b) => b.y - a.y)
    .map(p => new THREE.Vector2(p.x * scale, (maxY - p.y) * scale))
}

function createCeramicMaterial(colorHex: number = 0xd4c5a0): THREE.MeshPhysicalMaterial {
  const baseColor = new THREE.Color(colorHex)
  const lightened = baseColor.clone().lerp(new THREE.Color(0xffffff), 0.55)
  return new THREE.MeshPhysicalMaterial({
    color: lightened,
    metalness: 0.1,
    roughness: 0.35,
    clearcoat: 0.6,
    clearcoatRoughness: 0.25,
    sheen: 0.3,
    sheenColor: new THREE.Color(0xeee4cc),
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.92,
  })
}

function clearSegmentMeshes() {
  for (const m of segmentMeshes) {
    if (scene) scene.remove(m)
    m.geometry.dispose()
  }
  segmentMeshes = []
}

function updateGeometry() {
  if (!scene) return
  if (latheMesh) {
    scene.remove(latheMesh)
    latheMesh.geometry.dispose()
    latheMesh = null
  }
  if (wireframe) {
    scene.remove(wireframe)
    wireframe.geometry.dispose()
    wireframe = null
  }
  clearSegmentMeshes()

  if (!isValid.value) {
    loading.value = false
    return
  }

  const pts = buildLathePoints(store.controlPoints)
  if (pts.length < 2) {
    loading.value = false
    return
  }

  const sampled = sampleCurvePoints(store.controlPoints, 40)
  const ys = sampled.map(p => p.y)
  const maxY = Math.max(...ys)
  const minY = Math.min(...ys)
  const scale = 0.02

  const useSegmentColors = showKeyParts3D.value && store.keyParts.length >= 2

  if (useSegmentColors) {
    const parts = [...store.keyParts].sort((a, b) => (a.startY ?? 0) - (b.startY ?? 0))
    for (const part of parts) {
      let { startY, endY } = part
      if (startY === undefined || endY === undefined) continue
      startY = Math.max(minY, Math.min(maxY, startY))
      endY = Math.max(minY, Math.min(maxY, endY))
      if (Math.abs(endY - startY) < 0.5) continue

      const segPts: THREE.Vector2[] = []
      for (const p of sampled) {
        if (p.y >= Math.min(startY, endY) - 0.01 && p.y <= Math.max(startY, endY) + 0.01) {
          segPts.push(new THREE.Vector2(p.x * scale, (maxY - p.y) * scale))
        }
      }
      if (segPts.length < 2) continue
      segPts.sort((a, b) => b.y - a.y)

      const color = getKeyPartHexColor(part.name)
      const segGeo = new THREE.LatheGeometry(segPts, 64)
      segGeo.computeVertexNormals()
      const segMesh = new THREE.Mesh(segGeo, createCeramicMaterial(color))
      scene.add(segMesh)
      segmentMeshes.push(segMesh)
    }

    if (segmentMeshes.length === 0) {
      const geometry = new THREE.LatheGeometry(pts, 64)
      geometry.computeVertexNormals()
      latheMesh = new THREE.Mesh(geometry, createCeramicMaterial())
      scene.add(latheMesh)
    }
  } else {
    const geometry = new THREE.LatheGeometry(pts, 64)
    geometry.computeVertexNormals()
    latheMesh = new THREE.Mesh(geometry, createCeramicMaterial())
    scene.add(latheMesh)
  }

  const mainGeo = latheMesh?.geometry || segmentMeshes[0]?.geometry
  if (mainGeo) {
    const wireGeo = new THREE.WireframeGeometry(mainGeo)
    wireframe = new THREE.LineSegments(
      wireGeo,
      new THREE.LineBasicMaterial({
        color: 0x5d8a66,
        transparent: true,
        opacity: 0.35,
      })
    )
    wireframe.visible = showWireframe.value
    scene.add(wireframe)
  }

  if (controls) {
    controls.target.set(0, 1.5, 0)
    controls.update()
  }
  loading.value = false
}

function initThree() {
  if (!containerRef.value) return
  const el = containerRef.value
  const w = el.clientWidth
  const h = el.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf5f0e8)

  camera = new THREE.PerspectiveCamera(40, w / h, 0.1, 100)
  camera.position.set(4, 3, 5)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(w, h)
  renderer.shadowMap.enabled = true
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.05
  el.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.target.set(0, 1.5, 0)
  controls.minDistance = 2
  controls.maxDistance = 15
  controls.maxPolarAngle = Math.PI * 0.9

  const ambient = new THREE.AmbientLight(0xffffff, 0.45)
  scene.add(ambient)

  const mainLight = new THREE.DirectionalLight(0xfff5e1, 1.0)
  mainLight.position.set(4, 6, 5)
  mainLight.castShadow = true
  scene.add(mainLight)

  const fillLight = new THREE.DirectionalLight(0xe8f0ff, 0.4)
  fillLight.position.set(-4, 3, -3)
  scene.add(fillLight)

  const rimLight = new THREE.DirectionalLight(0xffe0b0, 0.35)
  rimLight.position.set(0, 5, -5)
  scene.add(rimLight)

  const spot = new THREE.SpotLight(0xfff0d4, 0.5, 20, Math.PI / 5, 0.5)
  spot.position.set(0, 8, 2)
  scene.add(spot)

  const gridHelper = new THREE.GridHelper(8, 16, 0xc4b58a, 0xe0d5b8)
  scene.add(gridHelper)

  const axesHelper = new THREE.AxesHelper(0.5)
  scene.add(axesHelper)

  updateGeometry()
  animate()
}

function animate() {
  animationId = requestAnimationFrame(animate)
  if (controls) {
    if (autoRotate.value) {
      if (latheMesh) latheMesh.rotation.y += 0.005
      for (const m of segmentMeshes) {
        m.rotation.y += 0.005
      }
      if (wireframe) wireframe.rotation.y += 0.005
    }
    controls.update()
  }
  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

function handleResize() {
  if (!containerRef.value || !camera || !renderer) return
  const el = containerRef.value
  const w = el.clientWidth
  const h = el.clientHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

function resetCamera() {
  if (camera && controls) {
    camera.position.set(4, 3, 5)
    controls.target.set(0, 1.5, 0)
    controls.update()
  }
}

watch(
  () => [store.controlPoints, store.keyParts, showKeyParts3D.value],
  () => {
    updateGeometry()
  },
  { deep: true }
)

watch(showWireframe, v => {
  if (wireframe) wireframe.visible = v
})

onMounted(() => {
  initThree()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (animationId) cancelAnimationFrame(animationId)
  if (renderer) {
    renderer.dispose()
    if (renderer.domElement.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement)
    }
  }
  if (latheMesh) latheMesh.geometry.dispose()
  clearSegmentMeshes()
  if (wireframe) wireframe.geometry.dispose()
})

defineExpose({ resetCamera })
</script>

<template>
  <div class="relative w-full h-full bg-[#F5F0E8] rounded-lg overflow-hidden border border-[#E8DFC9]">
    <div ref="containerRef" class="w-full h-full" />
    <div class="absolute top-3 left-3 flex flex-wrap gap-2 items-center">
      <button
        :class="[
          'px-2 py-1 text-xs rounded border transition-all',
          autoRotate ? 'bg-[#5D8A66] text-white border-[#5D8A66]' : 'bg-white text-gray-700 border-gray-300'
        ]"
        @click="autoRotate = !autoRotate"
      >
        自动旋转
      </button>
      <button
        :class="[
          'px-2 py-1 text-xs rounded border transition-all',
          showWireframe ? 'bg-[#5D8A66] text-white border-[#5D8A66]' : 'bg-white text-gray-700 border-gray-300'
        ]"
        @click="showWireframe = !showWireframe"
      >
        线框模式
      </button>
      <button
        :class="[
          'px-2 py-1 text-xs rounded border transition-all',
          showKeyParts3D && store.keyParts.length >= 2 ? 'bg-[#7B1FA2] text-white border-[#7B1FA2]' : 'bg-white text-gray-700 border-gray-300'
        ]"
        :disabled="store.keyParts.length < 2"
        :title="store.keyParts.length < 2 ? '请先识别关键部位' : '按部位分段着色显示'"
        @click="showKeyParts3D = !showKeyParts3D"
      >
        🎨 部位着色
      </button>
      <button
        class="px-2 py-1 text-xs rounded border bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
        @click="resetCamera"
      >
        重置视角
      </button>
    </div>
    <div
      v-if="showKeyParts3D && store.keyParts.length >= 2"
      class="absolute top-3 right-3 bg-white/90 backdrop-blur rounded-lg border border-[#E8DFC9] p-2 text-[10px] max-w-[140px]"
    >
      <div class="font-semibold text-gray-700 mb-1">部位图例</div>
      <div class="space-y-0.5">
        <div
          v-for="(part, idx) in [...store.keyParts].sort((a,b)=>(a.startY??0)-(b.startY??0)).slice(0,6)"
          :key="idx"
          class="flex items-center gap-1"
        >
          <span
            class="inline-block w-3 h-3 rounded-sm border"
            :style="{ backgroundColor: '#' + getKeyPartHexColor(part.name).toString(16).padStart(6, '0') + '55' }"
          ></span>
          <span class="text-gray-600 truncate">{{ part.name }}</span>
        </div>
      </div>
    </div>
    <div
      v-if="loading"
      class="absolute inset-0 flex items-center justify-center bg-[#F5F0E8]/80 text-sm text-gray-600"
    >
      渲染中...
    </div>
    <div
      v-if="!isValid"
      class="absolute bottom-3 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-red-50 text-red-700 rounded border border-red-200 text-xs"
    >
      剖面数据校验未通过，3D预览不可用
    </div>
    <div class="absolute bottom-3 right-3 px-2 py-1 bg-white/80 backdrop-blur rounded border border-[#E8DFC9] text-[10px] text-gray-500">
      拖拽旋转 · 滚轮缩放
    </div>
  </div>
</template>
