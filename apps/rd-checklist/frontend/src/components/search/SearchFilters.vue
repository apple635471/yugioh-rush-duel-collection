<script setup lang="ts">
import { reactive, watch } from 'vue'

const emit = defineEmits<{
  change: [filters: FilterState]
}>()

interface FilterState {
  card_type: string
  attribute: string
  level: string
  rarity: string
  owned: string
}

const filters = reactive<FilterState>({
  card_type: '',
  attribute: '',
  level: '',
  rarity: '',
  owned: '',
})

watch(filters, () => {
  emit('change', { ...filters })
}, { deep: true })

const cardTypes = [
  '通常怪獸', '效果怪獸', '融合怪獸', '儀式怪獸',
  '儀式/效果怪獸', '融合/效果怪獸', '巨極/效果怪獸',
  '通常魔法', '速攻魔法', '永續魔法', '裝備魔法', '場地魔法', '儀式魔法',
  '通常陷阱', '永續陷阱', '反擊陷阱',
]

const attributes = ['光', '暗', '炎', '水', '風', '地']
const rarities = ['N', 'R', 'SR', 'UR', 'SER', 'OVER-RUSH', 'RUSH', 'L']
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <select
      v-model="filters.card_type"
      class="bg-gray-800 border border-gray-700 rounded-md px-2 py-1 text-sm text-gray-300 focus:outline-none focus:border-yellow-500"
    >
      <option value="">All Types</option>
      <option v-for="t in cardTypes" :key="t" :value="t">{{ t }}</option>
    </select>

    <select
      v-model="filters.attribute"
      class="bg-gray-800 border border-gray-700 rounded-md px-2 py-1 text-sm text-gray-300 focus:outline-none focus:border-yellow-500"
    >
      <option value="">All Attributes</option>
      <option v-for="a in attributes" :key="a" :value="a">{{ a }}</option>
    </select>

    <select
      v-model="filters.level"
      class="bg-gray-800 border border-gray-700 rounded-md px-2 py-1 text-sm text-gray-300 focus:outline-none focus:border-yellow-500"
    >
      <option value="">All Levels</option>
      <option v-for="l in 12" :key="l" :value="String(l)">Lv.{{ l }}</option>
    </select>

    <select
      v-model="filters.rarity"
      class="bg-gray-800 border border-gray-700 rounded-md px-2 py-1 text-sm text-gray-300 focus:outline-none focus:border-yellow-500"
    >
      <option value="">All Rarities</option>
      <option v-for="r in rarities" :key="r" :value="r">{{ r }}</option>
    </select>

    <select
      v-model="filters.owned"
      class="bg-gray-800 border border-gray-700 rounded-md px-2 py-1 text-sm text-gray-300 focus:outline-none focus:border-yellow-500"
    >
      <option value="">All Cards</option>
      <option value="owned">Owned</option>
      <option value="missing">Missing</option>
    </select>
  </div>
</template>
