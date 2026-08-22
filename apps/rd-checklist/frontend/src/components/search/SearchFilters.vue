<script setup lang="ts">
import { reactive, computed, watch } from 'vue'
import { MONSTER_TYPES } from '@/constants/monsterTypes'
import { RARITIES } from '@/constants/rarities'
import Select from 'primevue/select'
import IftaLabel from 'primevue/iftalabel'
import AppButton from '@/components/ui/AppButton.vue'

const emit = defineEmits<{
  change: [filters: FilterState]
}>()

interface FilterState {
  card_type: string
  attribute: string
  monster_type: string
  level: string
  rarity: string
  is_legend: string
  owned: string
}

const filters = reactive<FilterState>({
  card_type: '',
  attribute: '',
  monster_type: '',
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
  { label: '全部', value: '' },
  ...cardTypes.map(t => ({ label: t, value: t })),
]

const attributeOptions: Option[] = [
  { label: '全部', value: '' },
  ...attributes.map(a => ({ label: a, value: a })),
]

/* 種族清單與編輯卡牌時共用 constants/monsterTypes.ts，兩邊選項一致 */
const monsterTypeOptions: Option[] = [
  { label: '全部', value: '' },
  ...MONSTER_TYPES.map(m => ({ label: m, value: m })),
]

const levelOptions: Option[] = [
  { label: '全部', value: '' },
  ...Array.from({ length: 12 }, (_, i) => ({ label: `Lv.${i + 1}`, value: String(i + 1) })),
]

const rarityOptions: Option[] = [
  { label: '全部', value: '' },
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

const filterConfigs: { key: keyof FilterState; title: string; options: Option[] }[] = [
  { key: 'card_type', title: '卡種', options: cardTypeOptions },
  { key: 'attribute', title: '屬性', options: attributeOptions },
  { key: 'monster_type', title: '種族', options: monsterTypeOptions },
  { key: 'level', title: '等級', options: levelOptions },
  { key: 'rarity', title: '貴罕度', options: rarityOptions },
  { key: 'is_legend', title: 'Legend', options: legendOptions },
  { key: 'owned', title: '持有', options: ownedOptions },
]

const hasActiveFilters = computed(() =>
  (Object.keys(filters) as (keyof FilterState)[]).some(k => filters[k] !== ''),
)

function clearFilters() {
  ;(Object.keys(filters) as (keyof FilterState)[]).forEach(k => { filters[k] = '' })
}
</script>

<template>
  <div class="rounded-xl border border-[rgba(201,168,76,0.16)] bg-dark-2/70 px-3 py-3">
    <div class="flex flex-wrap items-center gap-2.5">
      <IftaLabel v-for="cfg in filterConfigs" :key="cfg.key" class="w-[9.5rem]">
        <Select
          :input-id="`filter-${cfg.key}`"
          v-model="filters[cfg.key]"
          :options="cfg.options"
          option-label="label"
          option-value="value"
          placeholder="全部"
          class="w-full"
          :class="{ 'filter-active': filters[cfg.key] }"
        />
        <label :for="`filter-${cfg.key}`">{{ cfg.title }}</label>
      </IftaLabel>

      <AppButton
        v-if="hasActiveFilters"
        @click="clearFilters"
        variant="text"
        label="清除篩選"
        class="ml-auto"
      >
        <template #icon>
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </template>
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
/* Highlight a dropdown when it holds a non-default value */
.filter-active {
  border-color: rgba(201, 168, 76, 0.7);
  box-shadow: 0 0 0 1px rgba(201, 168, 76, 0.35);
}
</style>
