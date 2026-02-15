<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useUiStore } from '@/stores/ui'
import { fetchCard } from '@/api/cards'
import type { Card } from '@/types/card'
import CardDetailPanel from './CardDetailPanel.vue'

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
  if (e.key === 'Escape') ui.closeSidebar()
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <div
      class="fixed inset-0 bg-black/50 z-50"
      @click="ui.closeSidebar()"
    />

    <!-- Sidebar panel -->
    <aside
      class="fixed top-0 right-0 h-full w-full max-w-md bg-gray-800 border-l border-gray-700 z-50 overflow-y-auto shadow-2xl"
    >
      <!-- Close button -->
      <button
        @click="ui.closeSidebar()"
        class="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full bg-gray-700 text-gray-300 hover:text-white hover:bg-gray-600 transition-colors z-10"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
      </div>

      <!-- Card detail -->
      <CardDetailPanel
        v-else-if="card"
        :card="card"
        :active-rarity="ui.sidebarRarity ?? card.variants[0]?.rarity ?? ''"
        @card-updated="loadCard"
      />

      <!-- Error -->
      <div v-else class="p-6 text-center text-gray-500">
        Card not found.
      </div>
    </aside>
  </Teleport>
</template>
