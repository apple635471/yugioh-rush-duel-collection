/** Shared product type options used in create/edit forms and sidebar display. */
export const PRODUCT_TYPE_OPTIONS = [
  { value: 'booster',           label: 'Booster Pack (補充包)' },
  { value: 'structure_deck',    label: 'Structure Deck (預組)' },
  { value: 'character_pack',    label: 'Character Pack (角色包)' },
  { value: 'go_rush_character', label: 'Go Rush Character (GRC 角色包)' },
  { value: 'battle_pack',       label: 'Battle Pack (戰鬥包)' },
  { value: 'maximum_pack',      label: 'Maximum Pack (Maximum 包)' },
  { value: 'extra_pack',        label: 'Extra Pack (Extra 包)' },
  { value: 'legend_pack',       label: 'Legend Pack (傳說包)' },
  { value: 'vs_pack',           label: 'VS Pack (VS 包)' },
  { value: 'tournament_pack',   label: 'Tournament Pack (大會包)' },
  { value: 'advanced_pack',     label: 'Advanced Pack (進階包)' },
  { value: 'over_rush_pack',    label: 'Over Rush Pack (Over Rush 包)' },
  { value: 'other',             label: 'Promo (Promo)' },
  { value: 'unknown',           label: 'Other (其他)' },
]

/** 時間軸用：每個產品線一個顏色 + 短標籤（盒子空間有限，不放英文全名）。
 *  顏色本身就是圖例——同色即同產品線。 */
export const PRODUCT_TYPE_THEME: Record<string, { label: string; color: string }> = {
  booster:           { label: '補充包',       color: '#C9A84C' },
  advanced_pack:     { label: '上級包',       color: '#E0776B' },
  maximum_pack:      { label: '巨極包',       color: '#6FBF9B' },
  over_rush_pack:    { label: '超越超速包',   color: '#A78BFA' },
  legend_pack:       { label: '傳說包',       color: '#7DB8E8' },
  triple_build_pack: { label: '三重構築包',   color: '#E8A0C8' },
  structure_deck:    { label: '預組',         color: '#5FB3A1' },
  battle_pack:       { label: '戰鬥包',       color: '#E0A458' },
  promo:             { label: 'Promo',        color: '#B9A3D6' },
  other:             { label: 'Other',        color: '#8C90A3' },
}

export const PRODUCT_TYPE_FALLBACK = { label: '—', color: '#8C90A3' }

export function productTypeTheme(productType: string) {
  return PRODUCT_TYPE_THEME[productType] ?? PRODUCT_TYPE_FALLBACK
}
