<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import type { ControlPoint } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { sampleCurvePoints, validateProfile } from '@/utils/geometry'

const store = useProfileStore()
const containerRef = ref<HTMLDivElement | null>(null)

let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let controls: OrbitControls | null = null
let latheMesh: THREE.Mesh | null = null
let wireframe: THREE.LineSegments | null = null
let animationId: number | null = null

const loading = ref(true)
const autoRotate = ref(true)
const showWireframe = ref(false)

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

function createCeramicMaterial(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: 0xd4c5a0,
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

  if (!isValid.value) {
    loading.value = false
    return
  }

  const pts = buildLathePoints(store.controlPoints)
  if (pts.length < 2) {
    loading.value = false
    return
  }

  const geometry = new THREE.LatheGeometry(pts, 64)
  geometry.computeVertexNormals()
  latheMesh = new THREE.Mesh(geometry, createCeramicMaterial())
  scene.add(latheMesh)

  const wireGeo = new THREE.WireframeGeometry(geometry)
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
    if (autoRotate.value && latheMesh) {
      latheMesh.rotation.y += 0.005
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
  () => store.controlPoints,
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
  if (wireframe) wireframe.geometry.dispose()
})

defineExpose({ resetCamera })
</script>

<template>
  <div class="relative w-full h-full bg-[#F5F0E8] rounded-lg overflow-hidden border border-[#E8DFC9]">
    <div ref="containerRef" class="w-full h-full" />
    <div class="absolute top-3 left-3 flex gap-2 items-center">
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
        class="px-2 py-1 text-xs rounded border bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
        @click="resetCamera"
      >
        重置视角
      </button>
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
