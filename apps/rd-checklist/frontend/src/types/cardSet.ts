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
  /** 沒有 product_type：分類由 set_id 規則決定（後端 product_types.py）*/
  release_date?: string | null
}

export interface CardSetWithCards extends CardSet {
  cards: Card[]
}

/** 一個產品線，以及決定哪些 set_id 屬於它的規則（存在 DB）*/
export interface ProductType {
  /** 代號，也是網址用的 key，例如 booster */
  code: string
  /** English name, e.g. "Booster Pack" */
  name_en: string
  /** Chinese name shown on its own line; absent for Promo / Other */
  name_zh?: string | null
  /** 側邊欄分組，例如「補充包系列」*/
  group_label: string
  /** 時間軸配色 */
  color: string
  sort_order: number
  /** fallback 類型沒有規則，收所有沒被認領的卡組 */
  is_fallback: boolean
  /** 正規表示式，依序比對 set_id */
  rules: string[]
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
  /** 沒有 product_type：分類由 set_id 規則決定，不可編輯 */
  release_date?: string
  yugipedia_url?: string
}

export interface CardSetOverride {
  set_id: string
  field_name: string
  value: string | null
  updated_at: string
}
