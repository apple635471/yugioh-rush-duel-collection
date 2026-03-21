<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useUiStore } from '@/stores/ui'
import { useCardSetsStore } from '@/stores/cardSets'
import { fetchCard } from '@/api/cards'
import type { Card } from '@/types/card'
import CardDetailPanel from './CardDetailPanel.vue'
import CardCreatePanel from './CardCreatePanel.vue'
import Button from 'primevue/button'

const ui = useUiStore()
const cardSetsStore = useCardSetsStore()
const card = ref<Card | null>(null)
const loading = ref(false)
const loadError = ref<string | null>(null)

async function loadCard() {
  if (!ui.sidebarCardId) return
  loading.value = true
  loadError.value = null
  try {
    card.value = await fetchCard(ui.sidebarCardId)
    // 同步到 store，讓 card grid 即時反映變更（rarity、image、名稱等）
    if (card.value) cardSetsStore.updateCardInSet(card.value)
  } catch (e: any) {
    card.value = null
    const status = e?.response?.status
    const detail = e?.response?.data?.detail
    loadError.value = detail ?? (status ? `HTTP ${status}` : '網路錯誤')
    console.error('[AppSidebar] Failed to load card:', ui.sidebarCardId, e)
  } finally {
    loading.value = false
  }
}

watch(() => ui.sidebarCardId, loadCard)
onMounted(loadCard)

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && ui.sidebarOpen) ui.closeSidebar()
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))

function onCardCreated() {
  ui.closeSidebar()
}

const cardLabel = computed(() =>
  card.value?.name_zh || card.value?.name_jp || ui.sidebarCardId || ''
)
</script>

<template>
  <Teleport to="body">
    <!-- Mobile backdrop (hidden on sm+ since layout shifts instead) -->
    <div
      v-if="ui.sidebarOpen && !ui.sidebarMinimized"
      class="fixed inset-0 bg-black/50 z-40 sm:hidden"
      @click="ui.closeSidebar()"
    />

    <!-- Full sidebar panel -->
    <aside
      v-if="ui.sidebarOpen && !ui.sidebarMinimized"
      class="fixed top-0 right-0 h-full w-full max-w-md bg-dark-1 border-l border-[rgba(201,168,76,0.18)] z-50 overflow-y-auto shadow-2xl"
    >
      <!-- Create mode -->
      <template v-if="ui.sidebarMode === 'create'">
        <CardCreatePanel
          v-if="ui.sidebarCreateSetId"
          :set-id="ui.sidebarCreateSetId"
          @card-created="onCardCreated"
        />
      </template>

      <!-- Detail mode -->
      <template v-else>
        <div v-if="loading" class="flex items-center justify-center h-64">
          <div class="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin" />
        </div>

        <CardDetailPanel
          v-else-if="card"
          :card="card"
          :active-rarity="ui.sidebarRarity || card.variants[0]?.rarity || ''"
          @card-updated="loadCard"
        />

        <div v-else class="p-6 text-center text-gray-500">
          <p>Card not found.</p>
          <p v-if="loadError" class="text-xs text-red-400 mt-1 font-mono">{{ loadError }}</p>
          <p v-if="ui.sidebarCardId" class="text-xs text-gray-600 mt-1 font-mono">{{ ui.sidebarCardId }}</p>
        </div>
      </template>
    </aside>

    <!-- Collapse tab (sidebar open) -->
    <Button
      v-if="ui.sidebarOpen && !ui.sidebarMinimized"
      @click="ui.minimizeSidebar()"
      variant="text"
      severity="secondary"
      title="收起面板"
      class="fixed top-1/2 right-0 -translate-y-1/2 z-[60] bg-dark-2 border border-r-0 border-[rgba(201,168,76,0.25)] rounded-l-lg shadow-lg px-1.5 py-3 flex-col gap-1 hover:text-gold hover:bg-dark-3"
    >
      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </Button>

    <!-- Expand tab (sidebar minimized) -->
    <Button
      v-if="ui.sidebarOpen && ui.sidebarMinimized"
      @click="ui.expandSidebar()"
      variant="text"
      severity="secondary"
      title="展開面板"
      class="fixed top-1/2 right-0 -translate-y-1/2 z-50 bg-dark-1 border border-r-0 border-[rgba(201,168,76,0.25)] rounded-l-lg shadow-lg px-1.5 py-4 flex-col gap-2 hover:text-gold hover:bg-dark-2 group"
    >
      <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
      <span
        v-if="cardLabel"
        class="text-[9px] text-gray-400 group-hover:text-gold max-h-28 overflow-hidden"
        style="writing-mode: vertical-rl; text-orientation: mixed; white-space: nowrap;"
      >
        {{ cardLabel }}
      </span>
    </Button>
  </Teleport>
</template>
