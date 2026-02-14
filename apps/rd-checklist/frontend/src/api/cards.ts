import api from './client'
import type { Card, CardUpdate, CardVariant } from '@/types/card'

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
