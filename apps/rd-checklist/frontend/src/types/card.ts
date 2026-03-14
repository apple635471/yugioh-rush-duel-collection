export interface CardVariant {
  id: number
  card_id: string
  rarity: string
  sort_order: number
  image_source: string | null
  image_path: string | null
  owned_count: number
}

export interface Card {
  card_id: string
  set_id: string
  name_jp: string
  name_zh: string
  card_type: string
  attribute: string | null
  monster_type: string | null
  level: number | null
  atk: string | null
  defense: string | null
  description: string | null
  summon_condition: string | null
  condition: string | null
  effect: string | null
  continuous_effect: string | null
  is_legend: boolean
  is_manual: boolean
  original_rarity_string: string
  variants: CardVariant[]
}

export interface CardCreate {
  card_id: string
  set_id: string
  name_jp?: string
  name_zh?: string
  card_type?: string
  attribute?: string | null
  monster_type?: string | null
  level?: number | null
  atk?: string | null
  defense?: string | null
  description?: string | null
  summon_condition?: string | null
  condition?: string | null
  effect?: string | null
  continuous_effect?: string | null
  is_legend?: boolean
  rarity: string
}

export interface VariantCreate {
  rarity: string
}

export interface CardUpdate {
  name_jp?: string
  name_zh?: string
  card_type?: string
  attribute?: string | null
  monster_type?: string | null
  level?: number | null
  atk?: string | null
  defense?: string | null
  description?: string | null
  summon_condition?: string | null
  condition?: string | null
  effect?: string | null
  continuous_effect?: string | null
}

export interface ScanResult {
  name_jp: string | null
  name_zh: string | null
  card_type: string | null
  is_legend: boolean | null
  attribute: string | null
  monster_type: string | null
  level: number | null
  atk: string | null
  defense: string | null
  description: string | null
  summon_condition: string | null
  condition: string | null
  effect: string | null
  continuous_effect: string | null
}
