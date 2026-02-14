import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CardSet, CardSetWithCards, ProductType } from '@/types/cardSet'
import { fetchProductTypes, fetchCardSets, fetchCardSet } from '@/api/cardSets'

export const useCardSetsStore = defineStore('cardSets', () => {
  const productTypes = ref<ProductType[]>([])
  const sets = ref<CardSet[]>([])
  const currentSet = ref<CardSetWithCards | null>(null)
  const loading = ref(false)

  async function loadProductTypes() {
    productTypes.value = await fetchProductTypes()
  }

  async function loadSets(productType?: string) {
    loading.value = true
    try {
      sets.value = await fetchCardSets(productType)
    } finally {
      loading.value = false
    }
  }

  async function loadSet(setId: string) {
    loading.value = true
    try {
      currentSet.value = await fetchCardSet(setId)
    } finally {
      loading.value = false
    }
  }

  return { productTypes, sets, currentSet, loading, loadProductTypes, loadSets, loadSet }
})
