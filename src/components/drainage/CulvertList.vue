<script setup lang="ts">
import { ref, watch } from 'vue'
import { Plus, Edit2, Trash2, Save, X, ChevronDown, ChevronRight } from 'lucide-vue-next'
import type { Culvert, Section, Manhole, SedimentRecord, Slope } from '@/types'
import { api } from '@/lib/api'

const props = defineProps<{
  culverts: Culvert[]
  selectedCulvert: Culvert | null
}>()

const emit = defineEmits<{
  select: [culvert: Culvert]
  refresh: []
}>()

const activeSubTab = ref<'info' | 'sections' | 'manholes' | 'sediment'>('info')
const editing = ref(false)
const editForm = ref<Partial<Culvert>>({})
const sections = ref<Section[]>([])
const manholes = ref<Manhole[]>([])
const sedimentRecords = ref<SedimentRecord[]>([])
const slopes = ref<Slope[]>([])
const showAddModal = ref(false)
const addType = ref<'culvert' | 'section' | 'manhole' | 'sediment'>('culvert')
const newItem = ref<any>({})
const expandedSection = ref<number | null>(null)

async function loadDetails(culvertId: number) {
  try {
    sections.value = await api.sections.list(culvertId)
    manholes.value = await api.manholes.list(culvertId)
    sedimentRecords.value = await api.sediment.list(culvertId)
    const sectionIds = sections.value.map(s => s.id)
    slopes.value = []
    for (const id of sectionIds) {
      const sectionSlopes = await api.slopes.list(id)
      slopes.value.push(...sectionSlopes)
    }
  } catch (e) {
    console.error('加载详情失败', e)
  }
}

watch(() => props.selectedCulvert, (culvert) => {
  if (culvert) {
    loadDetails(culvert.id)
  }
}, { immediate: true })

function startEdit() {
  if (props.selectedCulvert) {
    editForm.value = { ...props.selectedCulvert }
    editing.value = true
  }
}

function cancelEdit() {
  editing.value = false
  editForm.value = {}
}

async function saveEdit() {
  if (!props.selectedCulvert) return
  try {
    await api.culverts.update(props.selectedCulvert.id, editForm.value as any)
    editing.value = false
    emit('refresh')
  } catch (e) {
    console.error('保存失败', e)
  }
}

function openAddModal(type: string) {
  addType.value = type as any
  newItem.value = {}
  showAddModal.value = true
}

async function addItem() {
  try {
    if (addType.value === 'culvert') {
      await api.culverts.create(newItem.value)
    } else if (addType.value === 'section' && props.selectedCulvert) {
      await api.sections.create({ ...newItem.value, culvert_id: props.selectedCulvert.id })
    } else if (addType.value === 'manhole' && props.selectedCulvert) {
      await api.manholes.create({ ...newItem.value, culvert_id: props.selectedCulvert.id })
    } else if (addType.value === 'sediment' && props.selectedCulvert) {
      await api.sediment.create({ ...newItem.value, culvert_id: props.selectedCulvert.id, record_date: new Date().toISOString() })
    }
    showAddModal.value = false
    newItem.value = {}
    emit('refresh')
    if (props.selectedCulvert) {
      loadDetails(props.selectedCulvert.id)
    }
  } catch (e) {
    console.error('添加失败', e)
  }
}

async function deleteItem(type: string, id: number) {
  if (!confirm('确定要删除吗？')) return
  try {
    if (type === 'culvert') {
      await api.culverts.delete(id)
    } else if (type === 'section') {
      await api.sections.delete(id)
    } else if (type === 'manhole') {
      await api.manholes.delete(id)
    } else if (type === 'sediment') {
      await api.sediment.delete(id)
    }
    emit('refresh')
    if (props.selectedCulvert) {
      loadDetails(props.selectedCulvert.id)
    }
  } catch (e) {
    console.error('删除失败', e)
  }
}

function getSectionSlopes(sectionId: number) {
  return slopes.value.filter(s => s.section_id === sectionId)
}
</script>

<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-bold text-[#5D4E2B] flex items-center gap-2">
        <span class="inline-block w-1 h-5 bg-[#2563EB] rounded"></span>
        暗渠管理
      </h2>
      <div class="flex gap-2">
        <button
          class="px-3 py-1.5 bg-[#2563EB] text-white text-sm rounded-lg hover:bg-[#1E40AF] transition-colors flex items-center gap-1.5"
          @click="openAddModal('culvert')"
        >
          <Plus class="w-4 h-4" />
          新增暗渠
        </button>
      </div>
    </div>

    <div v-if="selectedCulvert" class="flex-1 flex flex-col bg-white rounded-xl border border-[#E8DFC9] overflow-hidden">
      <div class="flex border-b border-[#E8DFC9]">
        <button
          v-for="tab in [
            { id: 'info', label: '基本信息' },
            { id: 'sections', label: '断面管理' },
            { id: 'manholes', label: '检查井管理' },
            { id: 'sediment', label: '淤积记录' },
          ]"
          :key="tab.id"
          :class="[
            'px-4 py-2.5 text-sm font-medium transition-colors',
            activeSubTab === tab.id
              ? 'text-[#2563EB] border-b-2 border-[#2563EB] bg-[#2563EB]/5'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          ]"
          @click="activeSubTab = tab.id as any"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="flex-1 p-4 overflow-auto">
        <div v-if="activeSubTab === 'info'" class="space-y-4">
          <div v-if="editing" class="bg-[#FAF6ED] p-4 rounded-lg border border-[#E8DFC9]">
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">暗渠名称</label>
                <input v-model="editForm.name" class="w-full px-3 py-2 border rounded-lg text-sm" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">暗渠编号</label>
                <input v-model="editForm.code" class="w-full px-3 py-2 border rounded-lg text-sm" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">位置</label>
                <input v-model="editForm.location" class="w-full px-3 py-2 border rounded-lg text-sm" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">长度(米)</label>
                <input v-model.number="editForm.length" type="number" class="w-full px-3 py-2 border rounded-lg text-sm" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">材质</label>
                <input v-model="editForm.material" class="w-full px-3 py-2 border rounded-lg text-sm" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">建设年份</label>
                <input v-model.number="editForm.construction_year" type="number" class="w-full px-3 py-2 border rounded-lg text-sm" />
              </div>
            </div>
            <div class="flex gap-2">
              <button @click="saveEdit" class="px-4 py-2 bg-[#5D8A66] text-white text-sm rounded-lg hover:bg-[#4a6f52] flex items-center gap-1.5">
                <Save class="w-4 h-4" /> 保存
              </button>
              <button @click="cancelEdit" class="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 flex items-center gap-1.5">
                <X class="w-4 h-4" /> 取消
              </button>
            </div>
          </div>

          <div v-else class="grid grid-cols-2 gap-4">
            <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
              <div class="text-xs text-gray-500 mb-1">暗渠名称</div>
              <div class="text-base font-semibold text-[#5D4E2B]">{{ selectedCulvert.name }}</div>
            </div>
            <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
              <div class="text-xs text-gray-500 mb-1">暗渠编号</div>
              <div class="text-base font-semibold text-[#5D4E2B]">{{ selectedCulvert.code }}</div>
            </div>
            <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
              <div class="text-xs text-gray-500 mb-1">位置</div>
              <div class="text-base font-semibold text-[#5D4E2B]">{{ selectedCulvert.location || '-' }}</div>
            </div>
            <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
              <div class="text-xs text-gray-500 mb-1">长度</div>
              <div class="text-base font-semibold text-[#5D4E2B]">{{ selectedCulvert.length }} 米</div>
            </div>
            <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
              <div class="text-xs text-gray-500 mb-1">材质</div>
              <div class="text-base font-semibold text-[#5D4E2B]">{{ selectedCulvert.material || '-' }}</div>
            </div>
            <div class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9]">
              <div class="text-xs text-gray-500 mb-1">建设年份</div>
              <div class="text-base font-semibold text-[#5D4E2B]">{{ selectedCulvert.construction_year || '-' }}</div>
            </div>
          </div>

          <div class="flex gap-2 mt-4">
            <button @click="startEdit" class="px-4 py-2 bg-[#2563EB] text-white text-sm rounded-lg hover:bg-[#1E40AF] flex items-center gap-1.5">
              <Edit2 class="w-4 h-4" /> 编辑
            </button>
            <button @click="deleteItem('culvert', selectedCulvert.id)" class="px-4 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 flex items-center gap-1.5">
              <Trash2 class="w-4 h-4" /> 删除
            </button>
          </div>
        </div>

        <div v-else-if="activeSubTab === 'sections'" class="space-y-3">
          <div class="flex justify-between items-center mb-3">
            <div class="text-sm text-gray-600">共 {{ sections.length }} 个断面</div>
            <button @click="openAddModal('section')" class="px-3 py-1.5 bg-[#2563EB] text-white text-sm rounded-lg hover:bg-[#1E40AF] flex items-center gap-1.5">
              <Plus class="w-4 h-4" /> 新增断面
            </button>
          </div>
          <div v-for="section in sections" :key="section.id" class="border rounded-lg overflow-hidden">
            <div
              class="p-3 bg-[#FAF6ED] flex items-center justify-between cursor-pointer hover:bg-[#F0E8D8]"
              @click="expandedSection = expandedSection === section.id ? null : section.id"
            >
              <div class="flex items-center gap-3">
                <component :is="expandedSection === section.id ? ChevronDown : ChevronRight" class="w-4 h-4 text-gray-500" />
                <span class="font-medium text-[#5D4E2B]">桩号 {{ section.station }}m</span>
                <span class="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">{{ section.shape }}</span>
                <span class="text-xs text-gray-500">{{ section.width }}m × {{ section.height }}m</span>
              </div>
              <button @click.stop="deleteItem('section', section.id)" class="p-1.5 text-red-500 hover:bg-red-50 rounded">
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
            <div v-if="expandedSection === section.id" class="p-3 bg-white border-t">
              <div class="grid grid-cols-4 gap-3 text-sm">
                <div>
                  <div class="text-xs text-gray-500">过水面积</div>
                  <div class="font-medium">{{ section.area?.toFixed(2) }} m²</div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">湿周</div>
                  <div class="font-medium">{{ section.perimeter?.toFixed(2) }} m</div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">水力半径</div>
                  <div class="font-medium">{{ section.hydraulic_radius?.toFixed(3) }} m</div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">坡度数量</div>
                  <div class="font-medium">{{ getSectionSlopes(section.id).length }}</div>
                </div>
              </div>
              <div v-if="getSectionSlopes(section.id).length > 0" class="mt-3">
                <div class="text-xs text-gray-500 mb-2">坡度记录</div>
                <div class="space-y-1">
                  <div v-for="slope in getSectionSlopes(section.id)" :key="slope.id" class="flex items-center gap-3 text-xs bg-gray-50 p-2 rounded">
                    <span>桩号 {{ slope.start_station }} - {{ slope.end_station }}m</span>
                    <span class="text-blue-600 font-medium">坡度: {{ (slope.slope_value * 1000).toFixed(1) }}‰</span>
                    <span v-if="slope.start_elevation" class="text-gray-500">高程: {{ slope.start_elevation }} → {{ slope.end_elevation }}m</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeSubTab === 'manholes'" class="space-y-3">
          <div class="flex justify-between items-center mb-3">
            <div class="text-sm text-gray-600">共 {{ manholes.length }} 个检查井</div>
            <button @click="openAddModal('manhole')" class="px-3 py-1.5 bg-[#2563EB] text-white text-sm rounded-lg hover:bg-[#1E40AF] flex items-center gap-1.5">
              <Plus class="w-4 h-4" /> 新增检查井
            </button>
          </div>
          <div class="grid gap-3">
            <div v-for="mh in manholes" :key="mh.id" class="p-3 bg-[#FAF6ED] rounded-lg border border-[#E8DFC9] flex items-center justify-between">
              <div class="flex items-center gap-4">
                <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                  {{ mh.name.slice(0, 1) }}
                </div>
                <div>
                  <div class="font-medium text-[#5D4E2B]">{{ mh.name }}</div>
                  <div class="text-xs text-gray-500">{{ mh.code }} · 桩号 {{ mh.station }}m</div>
                </div>
                <div class="flex gap-2">
                  <span v-if="mh.has_inlet" class="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">有进水</span>
                  <span v-if="mh.has_outlet" class="text-xs px-2 py-0.5 bg-orange-100 text-orange-700 rounded">有出水</span>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <div class="text-right">
                  <div class="text-xs text-gray-500">井深</div>
                  <div class="text-sm font-medium">{{ mh.depth }}m</div>
                </div>
                <div class="text-right">
                  <div class="text-xs text-gray-500">状态</div>
                  <div :class="[
                    'text-sm font-medium',
                    mh.condition === '良好' ? 'text-green-600' : 'text-orange-600'
                  ]">{{ mh.condition }}</div>
                </div>
                <button @click="deleteItem('manhole', mh.id)" class="p-1.5 text-red-500 hover:bg-red-50 rounded">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeSubTab === 'sediment'" class="space-y-3">
          <div class="flex justify-between items-center mb-3">
            <div class="text-sm text-gray-600">共 {{ sedimentRecords.length }} 条淤积记录</div>
            <button @click="openAddModal('sediment')" class="px-3 py-1.5 bg-[#2563EB] text-white text-sm rounded-lg hover:bg-[#1E40AF] flex items-center gap-1.5">
              <Plus class="w-4 h-4" /> 新增记录
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-[#FAF6ED]">
                <tr>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">记录日期</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">桩号范围</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">淤积厚度</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">淤积量</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">淤积类型</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">测量人</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="record in sedimentRecords" :key="record.id" class="hover:bg-gray-50">
                  <td class="px-4 py-2">{{ new Date(record.record_date).toLocaleDateString() }}</td>
                  <td class="px-4 py-2">{{ record.start_station }} - {{ record.end_station }}m</td>
                  <td class="px-4 py-2">
                    <span :class="[
                      'font-medium',
                      record.sediment_thickness >= 0.8 ? 'text-red-600' :
                      record.sediment_thickness >= 0.5 ? 'text-orange-600' :
                      'text-green-600'
                    ]">{{ record.sediment_thickness.toFixed(2) }}m</span>
                  </td>
                  <td class="px-4 py-2">{{ record.sediment_volume?.toFixed(1) }} m³</td>
                  <td class="px-4 py-2">{{ record.sediment_type || '-' }}</td>
                  <td class="px-4 py-2">{{ record.operator || '-' }}</td>
                  <td class="px-4 py-2">
                    <button @click="deleteItem('sediment', record.id)" class="text-red-500 hover:text-red-700">
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAddModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-bold text-[#5D4E2B] mb-4">
          新增{{ addType === 'culvert' ? '暗渠' : addType === 'section' ? '断面' : addType === 'manhole' ? '检查井' : '淤积记录' }}
        </h3>
        <div class="space-y-3 mb-4">
          <div v-if="addType === 'culvert'">
            <label class="block text-xs font-medium text-gray-600 mb-1">名称 *</label>
            <input v-model="newItem.name" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入暗渠名称" />
          </div>
          <div v-if="addType === 'culvert'">
            <label class="block text-xs font-medium text-gray-600 mb-1">编号 *</label>
            <input v-model="newItem.code" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入暗渠编号" />
          </div>
          <div v-if="addType === 'culvert'">
            <label class="block text-xs font-medium text-gray-600 mb-1">长度(米) *</label>
            <input v-model.number="newItem.length" type="number" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入长度" />
          </div>
          <div v-if="addType === 'section'">
            <label class="block text-xs font-medium text-gray-600 mb-1">桩号位置(米) *</label>
            <input v-model.number="newItem.station" type="number" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入桩号" />
          </div>
          <div v-if="addType === 'section'">
            <label class="block text-xs font-medium text-gray-600 mb-1">断面形式 *</label>
            <select v-model="newItem.shape" class="w-full px-3 py-2 border rounded-lg text-sm">
              <option value="矩形">矩形</option>
              <option value="圆形">圆形</option>
              <option value="拱形">拱形</option>
              <option value="马蹄形">马蹄形</option>
            </select>
          </div>
          <div v-if="addType === 'section'">
            <label class="block text-xs font-medium text-gray-600 mb-1">宽度(米) *</label>
            <input v-model.number="newItem.width" type="number" step="0.1" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入宽度" />
          </div>
          <div v-if="addType === 'section'">
            <label class="block text-xs font-medium text-gray-600 mb-1">高度(米)</label>
            <input v-model.number="newItem.height" type="number" step="0.1" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入高度" />
          </div>
          <div v-if="addType === 'manhole'">
            <label class="block text-xs font-medium text-gray-600 mb-1">名称 *</label>
            <input v-model="newItem.name" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入检查井名称" />
          </div>
          <div v-if="addType === 'manhole'">
            <label class="block text-xs font-medium text-gray-600 mb-1">编号 *</label>
            <input v-model="newItem.code" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入检查井编号" />
          </div>
          <div v-if="addType === 'manhole'">
            <label class="block text-xs font-medium text-gray-600 mb-1">桩号位置(米) *</label>
            <input v-model.number="newItem.station" type="number" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入桩号" />
          </div>
          <div v-if="addType === 'sediment'">
            <label class="block text-xs font-medium text-gray-600 mb-1">起始桩号 *</label>
            <input v-model.number="newItem.start_station" type="number" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入起始桩号" />
          </div>
          <div v-if="addType === 'sediment'">
            <label class="block text-xs font-medium text-gray-600 mb-1">结束桩号 *</label>
            <input v-model.number="newItem.end_station" type="number" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入结束桩号" />
          </div>
          <div v-if="addType === 'sediment'">
            <label class="block text-xs font-medium text-gray-600 mb-1">淤积厚度(米) *</label>
            <input v-model.number="newItem.sediment_thickness" type="number" step="0.01" class="w-full px-3 py-2 border rounded-lg text-sm" placeholder="请输入淤积厚度" />
          </div>
        </div>
        <div class="flex gap-2 justify-end">
          <button @click="showAddModal = false" class="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300">
            取消
          </button>
          <button @click="addItem" class="px-4 py-2 bg-[#2563EB] text-white text-sm rounded-lg hover:bg-[#1E40AF]">
            确认添加
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
