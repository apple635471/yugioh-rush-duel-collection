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
  maximum_atk: string | null
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
  maximum_atk?: string | null
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
  maximum_atk?: string | null
  description?: string | null
  summon_condition?: string | null
  condition?: string | null
  effect?: string | null
  continuous_effect?: string | null
}

/** Phase 1 OCR result — raw Japanese text, no translation. */
export interface CardRawExtract {
  name_jp: string | null
  card_type_jp: string | null
  is_legend: boolean | null
  attribute_jp: string | null
  monster_type_jp: string | null
  level: number | null
  atk: string | null
  defense: string | null
  description_jp: string | null
  summon_condition_jp: string | null
  condition_jp: string | null
  effect_jp: string | null
  continuous_effect_jp: string | null
}

/** Combined two-phase scan result: raw OCR + translated fields. */
export interface ScanResult {
  // Phase 1
  raw: CardRawExtract
  // Phase 2 translated
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
