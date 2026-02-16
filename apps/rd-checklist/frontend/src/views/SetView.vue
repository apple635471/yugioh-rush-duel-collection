<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCardSetsStore } from '@/stores/cardSets'
import { useUiStore } from '@/stores/ui'
import { fetchSetStats } from '@/api/cardSets'
import type { OwnershipStats } from '@/types/cardSet'
import BreadcrumbBar from '@/components/layout/BreadcrumbBar.vue'
import type { BreadcrumbItem } from '@/components/layout/BreadcrumbBar.vue'
import ViewToggle from '@/components/layout/ViewToggle.vue'
import CardGrid from '@/components/cards/CardGrid.vue'
import CardTable from '@/components/cards/CardTable.vue'
import SetMetadataEditor from '@/components/detail/SetMetadataEditor.vue'

const route = useRoute()
const store = useCardSetsStore()
const ui = useUiStore()

const setId = computed(() => route.params.setId as string)
const stats = ref<OwnershipStats | null>(null)

const breadcrumbs = computed<BreadcrumbItem[]>(() => {
  const items: BreadcrumbItem[] = [{ label: 'Home', to: '/' }]
  if (store.currentSet) {
    const pt = store.currentSet.product_type
    items.push({ label: pt, to: `/sets/${pt}` })
    items.push({ label: store.currentSet.set_name_zh || store.currentSet.set_id })
  }
  return items
})

const progressPercent = computed(() => {
  if (!stats.value || stats.value.total_variants === 0) return 0
  return Math.round((stats.value.owned_variants / stats.value.total_variants) * 100)
})

async function loadAll() {
  await store.loadSet(setId.value)
  await loadStats()
}

async function loadStats() {
  stats.value = await fetchSetStats(setId.value)
}

onMounted(loadAll)
watch(setId, loadAll)
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
            <ViewToggle />
          </template>
        </SetMetadataEditor>

        <!-- Progress bar -->
        <div v-if="stats" class="mt-3 mb-2">
          <div class="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Collection Progress</span>
            <span>
              <span class="text-emerald-400 font-medium">{{ stats.owned_variants }}</span>
              / {{ stats.total_variants }}
              <span class="ml-1 text-gray-400">({{ progressPercent }}%)</span>
            </span>
          </div>
          <div class="h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-500"
              :style="{ width: `${progressPercent}%` }"
            />
          </div>
        </div>
      </div>

      <!-- Card views -->
      <CardGrid
        v-if="ui.viewMode === 'grid'"
        :cards="store.currentSet.cards"
        @ownership-changed="loadStats"
      />
      <CardTable
        v-else
        :cards="store.currentSet.cards"
        @ownership-changed="loadStats"
      />
    </template>
  </div>
</template>
