export interface CardVariant {
  id: number
  card_id: string
  rarity: string
  is_alternate_art: boolean
  sort_order: number
  image_source: string | null
  image_path: string | null
  owned_count: number
}

/**
 * Returns the URL-safe rarity key for a variant.
 * Normal SR  → "SR"
 * Alt-art SR → "SR-alt"
 */
export function variantKey(variant: CardVariant): string {
  return variant.is_alternate_art ? `${variant.rarity}-alt` : variant.rarity
}

/**
 * Parses a rarity key back into its components.
 * "SR"     → { rarity: "SR", isAlt: false }
 * "SR-alt" → { rarity: "SR", isAlt: true }
 */
export function parseRarityKey(key: string): { rarity: string; isAlt: boolean } {
  if (key.endsWith('-alt')) {
    return { rarity: key.slice(0, -4), isAlt: true }
  }
  return { rarity: key, isAlt: false }
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
  is_alternate_art?: boolean
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
