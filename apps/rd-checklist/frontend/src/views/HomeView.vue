<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useCardSetsStore } from '@/stores/cardSets'
import { fetchGlobalStats, fetchAllSetStats } from '@/api/cardSets'
import type { OwnershipStats } from '@/types/cardSet'
import ProductTypeSidebar from '@/components/navigation/ProductTypeSidebar.vue'
import SetList from '@/components/navigation/SetList.vue'

const route = useRoute()
const store = useCardSetsStore()

const currentProductType = computed(() =>
  (route.params.productType as string) || undefined
)

const globalStats = ref<OwnershipStats | null>(null)
const allSetStats = ref<Record<string, OwnershipStats>>({})

const globalProgressPct = computed(() => {
  if (!globalStats.value || globalStats.value.total_variants === 0) return 0
  return Math.round(globalStats.value.owned_variants / globalStats.value.total_variants * 100)
})

async function loadStats() {
  const [gs, bulk] = await Promise.all([fetchGlobalStats(), fetchAllSetStats()])
  globalStats.value = gs
  allSetStats.value = bulk
}

onMounted(async () => {
  await store.loadProductTypes()
  await Promise.all([store.loadSets(currentProductType.value), loadStats()])
})

watch(currentProductType, async (pt) => {
  await store.loadSets(pt)
})
</script>

<template>
  <div class="flex gap-0">
    <!-- Left sidebar navigation -->
    <ProductTypeSidebar
      :product-types="store.productTypes"
      class="mr-6"
    />

    <!-- Main content -->
    <div class="flex-1 min-w-0">
      <!-- Page header with global stats -->
      <div class="flex items-end justify-between gap-6 mb-6 pb-5 border-b border-[rgba(201,168,76,0.12)]">
        <div>
          <div class="font-orbitron text-[9px] font-bold tracking-[0.25em] text-gold-dim uppercase mb-2">
            Rush Duel — Collection Tracker
          </div>
          <h1 class="font-cinzel text-2xl font-bold text-gray-100 leading-snug">
            卡牌收集圖鑑<br>
            <em class="not-italic text-gold-light">
              {{ currentProductType
                ? (store.productTypes.find(p => p.product_type === currentProductType)?.display_name ?? currentProductType)
                : '全部套牌包' }}
            </em>
          </h1>
        </div>

        <!-- Stats panel -->
        <div
          v-if="globalStats"
          class="flex shrink-0 border border-[rgba(201,168,76,0.2)] rounded-lg overflow-hidden"
        >
          <div class="px-5 py-2.5 text-center border-r border-[rgba(201,168,76,0.12)]">
            <div class="font-orbitron text-xl font-bold text-gold-light leading-none mb-1">
              {{ store.sets.length }}
            </div>
            <div class="text-[10px] text-gray-500 uppercase tracking-wide">套牌包</div>
          </div>
          <div class="px-5 py-2.5 text-center border-r border-[rgba(201,168,76,0.12)]">
            <div class="font-orbitron text-xl font-bold text-gold-light leading-none mb-1">
              {{ globalStats.total_variants.toLocaleString() }}
            </div>
            <div class="text-[10px] text-gray-500 uppercase tracking-wide">卡片</div>
          </div>
          <div class="px-5 py-2.5 text-center">
            <div class="font-orbitron text-xl font-bold text-gold-light leading-none mb-1">
              {{ globalProgressPct }}%
            </div>
            <div class="text-[10px] text-gray-500 uppercase tracking-wide">收集率</div>
          </div>
        </div>
      </div>

      <!-- Set grid -->
      <SetList
        :sets="store.sets"
        :loading="store.loading"
        :set-stats="allSetStats"
      />
    </div>
  </div>
</template>
