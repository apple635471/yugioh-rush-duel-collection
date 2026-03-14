import api from './client'
import type { Card, CardCreate, CardUpdate, CardVariant, ScanResult, VariantCreate } from '@/types/card'

export async function fetchCard(cardId: string): Promise<Card> {
  const { data } = await api.get<Card>(`/cards/${cardId}`)
  return data
}

export async function updateCard(cardId: string, update: CardUpdate): Promise<Card> {
  const { data } = await api.patch<Card>(`/cards/${cardId}`, update)
  return data
}

export async function updateOwnership(
  cardId: string,
  rarity: string,
  ownedCount: number,
): Promise<CardVariant> {
  const { data } = await api.patch<CardVariant>(
    `/ownership/${cardId}/${rarity}`,
    { owned_count: ownedCount },
  )
  return data
}

export async function searchCards(params: {
  q?: string
  card_type?: string
  attribute?: string
  level?: number
  set_id?: string
  rarity?: string
  owned?: string
  limit?: number
  offset?: number
}): Promise<Card[]> {
  const { data } = await api.get<Card[]>('/search', { params })
  return data
}

export function getCardImageUrl(cardId: string, rarity: string): string {
  return `/api/images/card/${cardId}/${rarity}`
}

export async function uploadCardImage(
  cardId: string,
  rarity: string,
  file: File,
): Promise<CardVariant> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<CardVariant>(
    `/images/card/${cardId}/${rarity}/upload`,
    form,
  )
  return data
}

export async function revertCardImage(
  cardId: string,
  rarity: string,
): Promise<CardVariant> {
  const { data } = await api.delete<CardVariant>(
    `/images/card/${cardId}/${rarity}/upload`,
  )
  return data
}

export async function getNextCardId(setId: string): Promise<string> {
  const { data } = await api.get<{ next_card_id: string }>(`/cards/next-id/${setId}`)
  return data.next_card_id
}

export async function createCard(cardData: CardCreate): Promise<Card> {
  const { data } = await api.post<Card>('/cards', cardData)
  return data
}

export async function addVariant(cardId: string, variantData: VariantCreate): Promise<CardVariant> {
  const { data } = await api.post<CardVariant>(`/cards/${cardId}/variants`, variantData)
  return data
}

export async function editVariantRarity(cardId: string, oldRarity: string, newRarity: string): Promise<Card> {
  const { data } = await api.patch<Card>(`/cards/${cardId}/variants/${oldRarity}`, { new_rarity: newRarity })
  return data
}

export async function deleteVariant(cardId: string, rarity: string): Promise<void> {
  await api.delete(`/cards/${cardId}/variants/${rarity}`)
}

export async function scanCard(cardId: string, rarity: string): Promise<ScanResult> {
  const { data } = await api.post<ScanResult>(`/scan/${cardId}/${rarity}`)
  return data
}
