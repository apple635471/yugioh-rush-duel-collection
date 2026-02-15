<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { searchCards } from '@/api/cards'
import type { Card } from '@/types/card'
import BreadcrumbBar from '@/components/layout/BreadcrumbBar.vue'
import ViewToggle from '@/components/layout/ViewToggle.vue'
import SearchFilters from '@/components/search/SearchFilters.vue'
import CardGrid from '@/components/cards/CardGrid.vue'
import CardTable from '@/components/cards/CardTable.vue'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()

const query = ref((route.query.q as string) || '')
const cards = ref<Card[]>([])
const loading = ref(false)
const totalResults = ref(0)

const filters = ref({
  card_type: '',
  attribute: '',
  level: '',
  rarity: '',
  owned: '',
})

let debounceTimer: ReturnType<typeof setTimeout> | null = null

async function doSearch() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (query.value.trim()) params.q = query.value.trim()
    if (filters.value.card_type) params.card_type = filters.value.card_type
    if (filters.value.attribute) params.attribute = filters.value.attribute
    if (filters.value.level) params.level = Number(filters.value.level)
    if (filters.value.rarity) params.rarity = filters.value.rarity
    if (filters.value.owned) params.owned = filters.value.owned
    params.limit = 200

    cards.value = await searchCards(params)
    totalResults.value = cards.value.length
  } finally {
    loading.value = false
  }
}

function onQueryInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    router.replace({ query: { ...route.query, q: query.value || undefined } })
    doSearch()
  }, 300)
}

function onFiltersChange(f: typeof filters.value) {
  filters.value = f
  doSearch()
}

// Watch for external URL changes (e.g. header search)
watch(() => route.query.q, (newQ) => {
  const q = (newQ as string) || ''
  if (q !== query.value) {
    query.value = q
    doSearch()
  }
})

onMounted(doSearch)
</script>

<template>
  <div>
    <BreadcrumbBar :items="[{ label: 'Home', to: '/' }, { label: 'Search' }]" />

    <!-- Search input -->
    <div class="mb-4">
      <input
        v-model="query"
        @input="onQueryInput"
        type="text"
        placeholder="Search by card name, ID, or effect..."
        class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2.5 text-gray-100 placeholder-gray-400 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 transition-colors"
        autofocus
      />
    </div>

    <!-- Filters -->
    <div class="flex items-center justify-between gap-4 mb-4">
      <SearchFilters @change="onFiltersChange" />
      <ViewToggle />
    </div>

    <!-- Results info -->
    <div class="flex items-center justify-between mb-4 text-sm text-gray-400">
      <span v-if="!loading">{{ totalResults }} result{{ totalResults !== 1 ? 's' : '' }}</span>
      <span v-else>Searching...</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-32">
      <div class="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <div v-else-if="cards.length === 0" class="text-center py-12 text-gray-500">
      No cards found. Try different search terms or filters.
    </div>

    <!-- Results -->
    <template v-else>
      <CardGrid v-if="ui.viewMode === 'grid'" :cards="cards" />
      <CardTable v-else :cards="cards" />
    </template>
  </div>
</template>
