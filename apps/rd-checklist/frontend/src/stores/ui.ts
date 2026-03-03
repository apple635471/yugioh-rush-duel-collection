import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const viewMode = ref<'grid' | 'table'>('grid')
  const sidebarOpen = ref(false)
  const sidebarCardId = ref<string | null>(null)
  const sidebarRarity = ref<string | null>(null)
  const sidebarMode = ref<'detail' | 'create'>('detail')
  const sidebarCreateSetId = ref<string | null>(null)

  function toggleView() {
    viewMode.value = viewMode.value === 'grid' ? 'table' : 'grid'
  }

  function openSidebar(cardId: string, rarity?: string) {
    sidebarMode.value = 'detail'
    sidebarCardId.value = cardId
    sidebarRarity.value = rarity ?? null
    sidebarCreateSetId.value = null
    sidebarOpen.value = true
  }

  function openCreateSidebar(setId: string) {
    sidebarMode.value = 'create'
    sidebarCardId.value = null
    sidebarRarity.value = null
    sidebarCreateSetId.value = setId
    sidebarOpen.value = true
  }

  function closeSidebar() {
    sidebarOpen.value = false
    sidebarCardId.value = null
    sidebarRarity.value = null
    sidebarMode.value = 'detail'
    sidebarCreateSetId.value = null
  }

  return {
    viewMode, sidebarOpen, sidebarCardId, sidebarRarity,
    sidebarMode, sidebarCreateSetId,
    toggleView, openSidebar, openCreateSidebar, closeSidebar,
  }
})
