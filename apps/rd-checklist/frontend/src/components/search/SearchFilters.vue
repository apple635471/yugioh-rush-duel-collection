<script setup lang="ts">
import { reactive, watch } from 'vue'
import { RARITIES } from '@/constants/rarities'
import Select from 'primevue/select'

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

const cardTypeOptions = [
  { label: 'All Types', value: '' },
  ...cardTypes.map(t => ({ label: t, value: t })),
]

const attributeOptions = [
  { label: 'All Attributes', value: '' },
  ...attributes.map(a => ({ label: a, value: a })),
]

const levelOptions = [
  { label: 'All Levels', value: '' },
  ...Array.from({ length: 12 }, (_, i) => ({ label: `Lv.${i + 1}`, value: String(i + 1) })),
]

const rarityOptions = [
  { label: 'All Rarities', value: '' },
  ...RARITIES,
]

const ownedOptions = [
  { label: 'All Cards', value: '' },
  { label: 'Owned', value: 'owned' },
  { label: 'Missing', value: 'missing' },
]
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <Select
      v-model="filters.card_type"
      :options="cardTypeOptions"
      option-label="label"
      option-value="value"
      size="small"
    />

    <Select
      v-model="filters.attribute"
      :options="attributeOptions"
      option-label="label"
      option-value="value"
      size="small"
    />

    <Select
      v-model="filters.level"
      :options="levelOptions"
      option-label="label"
      option-value="value"
      size="small"
    />

    <Select
      v-model="filters.rarity"
      :options="rarityOptions"
      option-label="label"
      option-value="value"
      size="small"
    />

    <Select
      v-model="filters.owned"
      :options="ownedOptions"
      option-label="label"
      option-value="value"
      size="small"
    />
  </div>
</template>
