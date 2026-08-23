import type { Card } from './card'

export interface CardSet {
  set_id: string
  set_name_jp: string
  set_name_zh: string
  product_type: string
  release_date: string | null
  post_url: string
  /** 該卡組在 yugipedia 的頁面，供對照卡表與抓取卡組圖片使用 */
  yugipedia_url?: string | null
  total_cards: number
  rarity_distribution: string | null
  is_manual?: boolean
}

export interface CardSetCreate {
  set_id: string
  set_name_jp?: string
  set_name_zh?: string
  product_type?: string
  release_date?: string | null
}

export interface CardSetWithCards extends CardSet {
  cards: Card[]
}

export interface ProductType {
  product_type: string
  /** English name, e.g. "Booster Pack" */
  display_name: string
  /** Chinese name shown on its own line; absent for Promo / Other */
  display_name_zh?: string | null
  set_count: number
}

export interface OwnershipStats {
  total_variants: number
  owned_variants: number
  total_owned_copies: number
}

export interface CardSetUpdate {
  set_name_jp?: string
  set_name_zh?: string
  product_type?: string
  release_date?: string
  yugipedia_url?: string
}

export interface CardSetOverride {
  set_id: string
  field_name: string
  value: string | null
  updated_at: string
}
