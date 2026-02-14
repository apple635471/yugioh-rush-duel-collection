import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const viewMode = ref<'grid' | 'table'>('grid')
  const sidebarOpen = ref(false)
  const sidebarCardId = ref<string | null>(null)
  const sidebarRarity = ref<string | null>(null)

  function toggleView() {
    viewMode.value = viewMode.value === 'grid' ? 'table' : 'grid'
  }

  function openSidebar(cardId: string, rarity?: string) {
    sidebarCardId.value = cardId
    sidebarRarity.value = rarity ?? null
    sidebarOpen.value = true
  }

  function closeSidebar() {
    sidebarOpen.value = false
    sidebarCardId.value = null
    sidebarRarity.value = null
  }

  return { viewMode, sidebarOpen, sidebarCardId, sidebarRarity, toggleView, openSidebar, closeSidebar }
})
