import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CardSet, CardSetWithCards, ProductType } from '@/types/cardSet'
import type { Card } from '@/types/card'
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

  /** 即時更新 card grid 的 owned_count（側邊欄改數量時呼叫） */
  function patchVariantOwnership(cardId: string, rarity: string, count: number) {
    if (!currentSet.value) return
    const card = currentSet.value.cards.find(c => c.card_id === cardId)
    if (!card) return
    const variant = card.variants.find(v => v.rarity === rarity)
    if (variant) variant.owned_count = count
  }

  /** 用側邊欄重新載入後的 card 物件更新 store，使 card grid 即時反映變更 */
  function updateCardInSet(updated: Card) {
    if (!currentSet.value) return
    const target = currentSet.value.cards.find(c => c.card_id === updated.card_id)
    if (target) Object.assign(target, updated)
  }

  return { productTypes, sets, currentSet, loading, loadProductTypes, loadSets, loadSet, patchVariantOwnership, updateCardInSet }
})
