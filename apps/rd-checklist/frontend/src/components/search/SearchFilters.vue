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
  is_legend: string
  owned: string
}

const filters = reactive<FilterState>({
  card_type: '',
  attribute: '',
  level: '',
  rarity: '',
  is_legend: '',
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

type Option = { label: string; value: string }

const cardTypeOptions: Option[] = [
  { label: '全部種類', value: '' },
  ...cardTypes.map(t => ({ label: t, value: t })),
]

const attributeOptions: Option[] = [
  { label: '全部屬性', value: '' },
  ...attributes.map(a => ({ label: a, value: a })),
]

const levelOptions: Option[] = [
  { label: '全部等級', value: '' },
  ...Array.from({ length: 12 }, (_, i) => ({ label: `Lv.${i + 1}`, value: String(i + 1) })),
]

const rarityOptions: Option[] = [
  { label: '全部貴罕度', value: '' },
  ...RARITIES,
]

const legendOptions: Option[] = [
  { label: '全部', value: '' },
  { label: 'Legend 卡', value: 'true' },
  { label: '非 Legend', value: 'false' },
]

const ownedOptions: Option[] = [
  { label: '全部', value: '' },
  { label: '已持有', value: 'owned' },
  { label: '未持有', value: 'missing' },
]

// Each filter carries its own visible title so the row of dropdowns is legible.
const filterConfigs: { key: keyof FilterState; title: string; options: Option[] }[] = [
  { key: 'card_type', title: '種類', options: cardTypeOptions },
  { key: 'attribute', title: '屬性', options: attributeOptions },
  { key: 'level', title: '等級', options: levelOptions },
  { key: 'rarity', title: '貴罕度', options: rarityOptions },
  { key: 'is_legend', title: 'Legend', options: legendOptions },
  { key: 'owned', title: '持有', options: ownedOptions },
]
</script>

<template>
  <div class="flex flex-wrap gap-x-3 gap-y-2">
    <div v-for="cfg in filterConfigs" :key="cfg.key" class="flex items-center gap-1.5">
      <label class="text-[10px] font-orbitron text-gray-500 tracking-wider uppercase whitespace-nowrap">{{ cfg.title }}</label>
      <Select
        v-model="filters[cfg.key]"
        :options="cfg.options"
        option-label="label"
        option-value="value"
        :placeholder="cfg.options[0]?.label"
        size="small"
      />
    </div>
  </div>
</template>
