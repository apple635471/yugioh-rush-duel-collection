<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useUiStore } from '@/stores/ui'
import { fetchCard } from '@/api/cards'
import type { Card } from '@/types/card'
import CardDetailPanel from './CardDetailPanel.vue'
import CardCreatePanel from './CardCreatePanel.vue'

const ui = useUiStore()
const card = ref<Card | null>(null)
const loading = ref(false)

async function loadCard() {
  if (!ui.sidebarCardId) return
  loading.value = true
  try {
    card.value = await fetchCard(ui.sidebarCardId)
  } catch {
    card.value = null
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

    <!-- Full sidebar panel (no close button inside — handled by the tab below) -->
    <aside
      v-if="ui.sidebarOpen && !ui.sidebarMinimized"
      class="fixed top-0 right-0 h-full w-full max-w-md bg-gray-800 border-l border-gray-700 z-50 overflow-y-auto shadow-2xl"
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
          <div class="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
        </div>

        <CardDetailPanel
          v-else-if="card"
          :card="card"
          :active-rarity="ui.sidebarRarity ?? card.variants[0]?.rarity ?? ''"
          @card-updated="loadCard"
        />

        <div v-else class="p-6 text-center text-gray-500">
          Card not found.
        </div>
      </template>
    </aside>

    <!--
      Collapse tab (sidebar open): fixed at vertical center, right edge, z above sidebar.
      Expand tab (sidebar minimized): same exact position.
      Both render in same spot so the button never jumps.
    -->
    <button
      v-if="ui.sidebarOpen && !ui.sidebarMinimized"
      @click="ui.minimizeSidebar()"
      class="fixed top-1/2 right-0 -translate-y-1/2 z-[60] bg-gray-700 border border-r-0 border-gray-600 rounded-l-lg shadow-lg px-1.5 py-3 flex flex-col items-center gap-1 text-gray-300 hover:text-yellow-400 hover:bg-gray-600 transition-colors"
      title="收起面板"
    >
      <!-- chevron → (collapse) -->
      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </button>

    <button
      v-if="ui.sidebarOpen && ui.sidebarMinimized"
      @click="ui.expandSidebar()"
      class="fixed top-1/2 right-0 -translate-y-1/2 z-50 bg-gray-800 border border-r-0 border-gray-600 rounded-l-lg shadow-lg px-1.5 py-4 flex flex-col items-center gap-2 text-gray-300 hover:text-yellow-400 hover:bg-gray-700 transition-colors group"
      title="展開面板"
    >
      <!-- chevron ← (expand) -->
      <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
      <span
        v-if="cardLabel"
        class="text-[9px] text-gray-400 group-hover:text-yellow-400 max-h-28 overflow-hidden"
        style="writing-mode: vertical-rl; text-orientation: mixed; white-space: nowrap;"
      >
        {{ cardLabel }}
      </span>
    </button>
  </Teleport>
</template>
