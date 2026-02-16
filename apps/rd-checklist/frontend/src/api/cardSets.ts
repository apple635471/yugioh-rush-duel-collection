import api from './client'
import type { CardSet, CardSetWithCards, ProductType, OwnershipStats, CardSetUpdate, CardSetOverride } from '@/types/cardSet'

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

export async function updateCardSet(setId: string, update: CardSetUpdate): Promise<CardSet> {
  const { data } = await api.patch<CardSet>(`/card-sets/${setId}`, update)
  return data
}

export async function fetchCardSetOverrides(setId: string): Promise<CardSetOverride[]> {
  const { data } = await api.get<CardSetOverride[]>(`/card-sets/${setId}/overrides`)
  return data
}

export async function deleteCardSetOverride(setId: string, fieldName: string): Promise<void> {
  await api.delete(`/card-sets/${setId}/overrides/${fieldName}`)
}
