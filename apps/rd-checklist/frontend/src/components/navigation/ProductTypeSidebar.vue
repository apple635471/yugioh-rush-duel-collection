<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import type { ProductType } from '@/types/cardSet'
import Button from 'primevue/button'
import ProductTypeRulesDialog from '@/components/navigation/ProductTypeRulesDialog.vue'

const route = useRoute()
const collapsed = ref(false)

const props = defineProps<{
  productTypes: ProductType[]
}>()

const emit = defineEmits<{
  /** 分類規則改了：卡組的分類跟著變，外面要重抓 */
  rulesChanged: []
}>()

const rulesDialog = ref<InstanceType<typeof ProductTypeRulesDialog> | null>(null)

/**
 * 分組也來自資料（`group_label`），跟代號、名稱、顏色、規則一樣存在 DB。
 * 組的順序 = 該組第一個類型的順序；組內順序 = 類型自己的順序。
 */
const sections = computed(() => {
  const groups: { label: string; types: ProductType[] }[] = []
  for (const pt of props.productTypes) {
    const label = pt.group_label || '其他'
    const existing = groups.find(g => g.label === label)
    if (existing) existing.types.push(pt)
    else groups.push({ label, types: [pt] })
  }
  return groups
})

const totalSets = computed(() => props.productTypes.reduce((sum, pt) => sum + pt.set_count, 0))

function isActive(pt: ProductType): boolean {
  return route.params.productType === pt.code
}

const ITEM_CLASS = 'flex items-center justify-between gap-1 px-4 py-1.5 text-xs border-l-2 transition-all'
const ACTIVE_CLASS = 'border-l-gold text-gold-light bg-[rgba(201,168,76,0.08)] font-medium'
const INACTIVE_CLASS = 'border-l-transparent text-gray-400 hover:text-gray-200 hover:bg-[rgba(201,168,76,0.04)]'
const BADGE_CLASS = 'font-orbitron text-[10px] px-1 py-0.5 rounded shrink-0'
</script>

<template>
  <!-- Collapsed: narrow strip with expand button -->
  <div
    v-if="collapsed"
    class="shrink-0 flex flex-col items-center pt-3 gap-2"
    style="width: 36px"
  >
    <Button
      @click="collapsed = false"
      variant="text"
      severity="secondary"
      size="small"
      class="p-1 text-gold/60 hover:text-gold"
      title="展開側欄"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </Button>
  </div>

  <!-- Expanded sidebar -->
  <aside
    v-else
    class="shrink-0 sticky top-[56px] self-start h-[calc(100vh-56px)] overflow-y-auto overflow-x-hidden bg-dark-1 border-r border-[rgba(201,168,76,0.10)]"
    style="width: 200px"
  >
    <!-- Header row with collapse button -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-[rgba(201,168,76,0.1)]">
      <span class="font-orbitron text-[10px] font-bold tracking-[0.16em] text-gold uppercase">
        Browse
      </span>
      <Button
        @click="collapsed = true"
        variant="text"
        severity="secondary"
        size="small"
        class="p-1 text-gold/40 hover:text-gold"
        title="收合側欄"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </Button>
    </div>

    <!-- All section -->
    <div class="py-2">
      <router-link
        to="/"
        :class="[ITEM_CLASS, !route.params.productType ? ACTIVE_CLASS : INACTIVE_CLASS]"
      >
        <span>全部</span>
        <span
          :class="[BADGE_CLASS, !route.params.productType ? 'text-gold bg-[rgba(201,168,76,0.15)]' : 'text-gray-400 bg-dark-3']"
        >
          {{ totalSets }}
        </span>
      </router-link>
    </div>

    <!-- Grouped sections -->
    <template v-for="section in sections" :key="section.label">
      <div class="h-px bg-[rgba(201,168,76,0.08)] mx-4 my-1" />
      <div class="pt-2 pb-1">
        <div class="font-orbitron text-[10px] font-bold tracking-[0.16em] text-gold uppercase px-4 mb-1">
          {{ section.label }}
        </div>
        <router-link
          v-for="pt in section.types"
          :key="pt.code"
          :to="`/sets/${pt.code}`"
          :class="[ITEM_CLASS, isActive(pt) ? ACTIVE_CLASS : INACTIVE_CLASS]"
        >
          <!-- English name, with the Chinese name on its own line -->
          <span class="leading-snug min-w-0">
            {{ pt.name_en }}
            <span v-if="pt.name_zh" class="block">{{ pt.name_zh }}</span>
          </span>
          <span
            :class="[BADGE_CLASS, isActive(pt) ? 'text-gold bg-[rgba(201,168,76,0.15)]' : 'text-gray-400 bg-dark-3']"
          >
            {{ pt.set_count }}
          </span>
        </router-link>
      </div>
    </template>

    <!-- 分類規則：卡組屬於哪一類由這些規則決定 -->
    <div class="h-px bg-[rgba(201,168,76,0.08)] mx-4 my-1" />
    <div class="px-2 py-2">
      <button
        type="button"
        class="w-full flex items-center gap-1.5 px-2 py-1.5 rounded text-[11px] text-gray-400
               hover:text-gold-light hover:bg-[rgba(201,168,76,0.06)] transition-colors"
        @click="rulesDialog?.open()"
      >
        <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path stroke-linecap="round" stroke-linejoin="round"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        編輯分類規則
      </button>
    </div>
  </aside>

  <ProductTypeRulesDialog ref="rulesDialog" @changed="emit('rulesChanged')" />
</template>
