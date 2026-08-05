<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCardSetsStore } from '@/stores/cardSets'
import { useUiStore } from '@/stores/ui'
import type { Card } from '@/types/card'
import { RARITIES, displayRarityRank } from '@/constants/rarities'
import BreadcrumbBar from '@/components/layout/BreadcrumbBar.vue'
import type { BreadcrumbItem } from '@/components/layout/BreadcrumbBar.vue'
import ViewToggle from '@/components/layout/ViewToggle.vue'
import CardGrid from '@/components/cards/CardGrid.vue'
import CardTable from '@/components/cards/CardTable.vue'
import SetMetadataEditor from '@/components/detail/SetMetadataEditor.vue'
import Select from 'primevue/select'

const route = useRoute()
const store = useCardSetsStore()
const ui = useUiStore()

const setId = computed(() => route.params.setId as string)

const breadcrumbs = computed<BreadcrumbItem[]>(() => {
  const items: BreadcrumbItem[] = [{ label: 'Home', to: '/' }]
  if (store.currentSet) {
    const pt = store.currentSet.product_type
    items.push({ label: pt, to: `/sets/${pt}` })
    items.push({ label: store.currentSet.set_name_zh || store.currentSet.set_id })
  }
  return items
})

const cards = computed<Card[]>(() => store.currentSet?.cards ?? [])

// ── Filters (options limited to what actually appears in this set) ──
const filterRarity = ref('')
const filterCardType = ref('')

const rarityOptions = computed(() => {
  const present = new Set<string>()
  for (const c of cards.value) for (const v of c.variants) present.add(v.rarity)
  const label = (r: string) => RARITIES.find(x => x.value === r)?.label ?? r
  const opts = [...present]
    .sort((a, b) => displayRarityRank(b) - displayRarityRank(a))
    .map(r => ({ label: label(r), value: r }))
  return [{ label: '全部貴罕度', value: '' }, ...opts]
})

const cardTypeOptions = computed(() => {
  const present = new Set<string>()
  for (const c of cards.value) if (c.card_type) present.add(c.card_type)
  const opts = [...present].sort().map(t => ({ label: t, value: t }))
  return [{ label: '全部種類', value: '' }, ...opts]
})

const filteredCards = computed<Card[]>(() =>
  cards.value.filter(c => {
    if (filterCardType.value && c.card_type !== filterCardType.value) return false
    if (filterRarity.value && !c.variants.some(v => v.rarity === filterRarity.value)) return false
    return true
  }),
)

// ── Progress (computed client-side so both modes stay live on ownership edits) ──
function pct(owned: number, total: number): number {
  return total ? Math.round((owned / total) * 100) : 0
}

const standardProgress = computed(() => {
  let owned = 0, total = 0
  for (const c of cards.value) {
    for (const v of c.variants) {
      total++
      if (v.owned_count > 0) owned++
    }
  }
  return { owned, total, percent: pct(owned, total) }
})

// "net": drop alt-art, and drop SER unless SER is the card's only (non-alt) rarity
const netProgress = computed(() => {
  let owned = 0, total = 0
  for (const c of cards.value) {
    const nonAlt = c.variants.filter(v => !v.is_alternate_art)
    if (!nonAlt.length) continue
    const rarities = new Set(nonAlt.map(v => v.rarity))
    const onlySER = rarities.size === 1 && rarities.has('SER')
    const candidates = onlySER ? nonAlt : nonAlt.filter(v => v.rarity !== 'SER')
    for (const v of candidates) {
      total++
      if (v.owned_count > 0) owned++
    }
  }
  return { owned, total, percent: pct(owned, total) }
})

const progress = computed(() =>
  ui.progressMode === 'net' ? netProgress.value : standardProgress.value,
)

async function loadAll() {
  await store.loadSet(setId.value)
}

onMounted(loadAll)
watch(setId, () => {
  filterRarity.value = ''
  filterCardType.value = ''
  loadAll()
})

// Reload data when sidebar closes (card may have been created or edited)
watch(() => ui.sidebarOpen, (isOpen, wasOpen) => {
  if (!isOpen && wasOpen) loadAll()
})
</script>

<template>
  <div>
    <BreadcrumbBar :items="breadcrumbs" />

    <!-- Loading -->
    <div v-if="store.loading" class="flex items-center justify-center h-64">
      <div class="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
    </div>

    <template v-else-if="store.currentSet">
      <!-- Set header (editable) -->
      <div class="mb-6">
        <SetMetadataEditor
          :card-set="store.currentSet"
          @updated="loadAll"
        >
          <template #view-toggle>
            <button
              @click="ui.openCreateSidebar(setId)"
              class="text-xs text-gray-400 hover:text-yellow-400 border border-gray-600 hover:border-yellow-500/50 rounded px-2 py-1 transition-colors"
              title="Add new card"
            >
              <svg class="w-3.5 h-3.5 inline-block mr-0.5 -mt-px" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add Card
            </button>
            <ViewToggle />
          </template>
        </SetMetadataEditor>

        <!-- Progress bar (mode-switchable, single bar) -->
        <div class="mt-4 mb-3 bg-dark-2 border border-[rgba(201,168,76,0.14)] rounded-lg px-4 py-3">
          <div class="flex items-center justify-between mb-2 gap-3 flex-wrap">
            <div class="flex items-center gap-2">
              <span class="text-xs font-orbitron text-gray-400 tracking-widest uppercase">Collection Progress</span>
              <!-- progress mode toggle -->
              <div class="inline-flex rounded-md border border-[rgba(201,168,76,0.25)] overflow-hidden text-[10px] font-orbitron">
                <button
                  @click="ui.progressMode = 'net'"
                  class="px-2 py-0.5 transition-colors"
                  :class="ui.progressMode === 'net' ? 'bg-gold text-black font-bold' : 'text-gray-400 hover:text-gold'"
                  title="排除異圖，並排除 SER（該卡只有 SER 則保留）"
                >淨收集</button>
                <button
                  @click="ui.progressMode = 'standard'"
                  class="px-2 py-0.5 transition-colors border-l border-[rgba(201,168,76,0.25)]"
                  :class="ui.progressMode === 'standard' ? 'bg-gold text-black font-bold' : 'text-gray-400 hover:text-gold'"
                  title="所有 variant 皆計入"
                >標準</button>
              </div>
            </div>
            <span class="text-xs font-orbitron">
              <span class="text-gold font-bold">{{ progress.owned }}</span>
              <span class="text-gray-500"> / {{ progress.total }}</span>
              <span class="ml-2 text-gold-light font-bold">{{ progress.percent }}%</span>
            </span>
          </div>
          <div class="h-2 bg-dark-4 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-700"
              :style="{ width: `${progress.percent}%`, background: 'linear-gradient(90deg, #6B5428, #EAC96A)' }"
            />
          </div>
        </div>

        <!-- Controls: display mode + filters -->
        <div class="flex items-center gap-3 flex-wrap">
          <!-- display mode toggle -->
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] font-orbitron text-gray-500 tracking-wider uppercase">顯示</span>
            <div class="inline-flex rounded-md border border-[rgba(201,168,76,0.25)] overflow-hidden text-[11px] font-orbitron">
              <button
                @click="ui.displayMode = 'owned'"
                class="px-2.5 py-1 transition-colors"
                :class="ui.displayMode === 'owned' ? 'bg-gold text-black font-bold' : 'text-gray-400 hover:text-gold'"
                title="優先顯示你擁有的貴罕度（多種取最高），都沒有則顯示最高"
              >擁有優先</button>
              <button
                @click="ui.displayMode = 'highest'"
                class="px-2.5 py-1 transition-colors border-l border-[rgba(201,168,76,0.25)]"
                :class="ui.displayMode === 'highest' ? 'bg-gold text-black font-bold' : 'text-gray-400 hover:text-gold'"
                title="一律顯示最高貴罕度"
              >最高貴罕度</button>
            </div>
          </div>

          <div class="flex items-center gap-2 ml-auto">
            <Select
              v-model="filterRarity"
              :options="rarityOptions"
              option-label="label"
              option-value="value"
              size="small"
            />
            <Select
              v-model="filterCardType"
              :options="cardTypeOptions"
              option-label="label"
              option-value="value"
              size="small"
            />
          </div>
        </div>
      </div>

      <!-- Card views -->
      <div v-if="filteredCards.length === 0" class="text-center text-gray-500 py-16 text-sm">
        沒有符合篩選條件的卡片。
      </div>
      <CardGrid
        v-else-if="ui.viewMode === 'grid'"
        :cards="filteredCards"
        :display-mode="ui.displayMode"
      />
      <CardTable
        v-else
        :cards="filteredCards"
        :display-mode="ui.displayMode"
      />
    </template>
  </div>
</template>
