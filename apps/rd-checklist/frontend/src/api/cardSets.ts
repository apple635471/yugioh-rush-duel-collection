import api from './client'
import type { CardSet, CardSetWithCards, ProductType, OwnershipStats } from '@/types/cardSet'

export async function fetchProductTypes(): Promise<ProductType[]> {
  const { data } = await api.get<ProductType[]>('/card-sets/product-types')
  return data
}

export async function fetchCardSets(productType?: string): Promise<CardSet[]> {
  const params = productType ? { product_type: productType } : {}
  const { data } = await api.get<CardSet[]>('/card-sets', { params })
  return data
}

export async function fetchCardSet(setId: string): Promise<CardSetWithCards> {
  const { data } = await api.get<CardSetWithCards>(`/card-sets/${setId}`)
  return data
}

export async function fetchSetStats(setId: string): Promise<OwnershipStats> {
  const { data } = await api.get<OwnershipStats>(`/ownership/stats/${setId}`)
  return data
}
