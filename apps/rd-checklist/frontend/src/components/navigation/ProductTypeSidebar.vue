<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import type { ProductType } from '@/types/cardSet'
import Button from 'primevue/button'

const route = useRoute()
const collapsed = ref(false)

const props = defineProps<{
  productTypes: ProductType[]
}>()

/**
 * Sidebar sections, by product type. Listed explicitly (rather than matched
 * on the display name) so renaming a label never reshuffles the nav, and the
 * order within a section is the order here.
 */
const SECTIONS: { label: string; types: string[] }[] = [
  {
    label: '補充包系列',
    types: ['booster', 'advanced_pack', 'maximum_pack', 'over_rush_pack', 'legend_pack', 'triple_build_pack'],
  },
  { label: '預組', types: ['structure_deck'] },
  { label: '其他', types: ['battle_pack', 'promo', 'other'] },
]

const PLACED = new Set(SECTIONS.flatMap(s => s.types))

/** Types in this section, in SECTIONS order; unlisted types land in the last section. */
function typesIn(section: { label: string; types: string[] }): ProductType[] {
  const byType = new Map(props.productTypes.map(pt => [pt.product_type, pt]))
  const listed = section.types.map(t => byType.get(t)).filter((pt): pt is ProductType => !!pt)

  const isLast = section === SECTIONS[SECTIONS.length - 1]
  if (!isLast) return listed
  const unlisted = props.productTypes.filter(pt => !PLACED.has(pt.product_type))
  return [...listed, ...unlisted]
}

const sections = computed(() =>
  SECTIONS.map(s => ({ label: s.label, types: typesIn(s) })).filter(s => s.types.length > 0)
)

const totalSets = computed(() => props.productTypes.reduce((sum, pt) => sum + pt.set_count, 0))

function isActive(pt: ProductType): boolean {
  return route.params.productType === pt.product_type
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
          :key="pt.product_type"
          :to="`/sets/${pt.product_type}`"
          :class="[ITEM_CLASS, isActive(pt) ? ACTIVE_CLASS : INACTIVE_CLASS]"
        >
          <!-- English name, with the Chinese name on its own line -->
          <span class="leading-snug min-w-0">
            {{ pt.display_name }}
            <span v-if="pt.display_name_zh" class="block">{{ pt.display_name_zh }}</span>
          </span>
          <span
            :class="[BADGE_CLASS, isActive(pt) ? 'text-gold bg-[rgba(201,168,76,0.15)]' : 'text-gray-400 bg-dark-3']"
          >
            {{ pt.set_count }}
          </span>
        </router-link>
      </div>
    </template>
  </aside>
</template>
