import type { Card } from './card'

export interface CardSet {
  set_id: string
  set_name_jp: string
  set_name_zh: string
  product_type: string
  release_date: string | null
  post_url: string
  total_cards: number
  rarity_distribution: string | null
}

export interface CardSetWithCards extends CardSet {
  cards: Card[]
}

export interface ProductType {
  product_type: string
  display_name: string
  set_count: number
}

export interface OwnershipStats {
  total_variants: number
  owned_variants: number
  total_owned_copies: number
}
