/**
 * 產品類型的單一來源：下拉選單、時間軸配色都從這裡長出來。
 *
 * **必須與後端 `product_types.PRODUCT_TYPE_LABELS` 保持同步**——那邊是分類的
 * 權威（匯入時會重新推導 product_type），這裡只是顯示。順序照側邊欄的
 * `SECTIONS`：補充包系列 → 預組 → 其他。
 *
 * `zh` 為 null 代表沒有慣用中文名（Promo / Other），側邊欄與下拉都只顯示英文。
 */
export const PRODUCT_TYPES: {
  value: string
  en: string
  zh: string | null
  color: string
}[] = [
  { value: 'booster',           en: 'Booster Pack',      zh: '補充包',     color: '#C9A84C' },
  { value: 'advanced_pack',     en: 'Advanced Pack',     zh: '上級包',     color: '#E0776B' },
  { value: 'maximum_pack',      en: 'Maximum Pack',      zh: '巨極包',     color: '#6FBF9B' },
  { value: 'over_rush_pack',    en: 'Over Rush Pack',    zh: '超越超速包', color: '#A78BFA' },
  { value: 'legend_pack',       en: 'Legend Pack',       zh: '傳說包',     color: '#7DB8E8' },
  { value: 'triple_build_pack', en: 'Triple Build Pack', zh: '三重構築包', color: '#E8A0C8' },
  { value: 'structure_deck',    en: 'Structure Deck',    zh: '預組',       color: '#5FB3A1' },
  { value: 'battle_pack',       en: 'Battle Pack',       zh: '戰鬥包',     color: '#E0A458' },
  { value: 'promo',             en: 'Promo',             zh: null,         color: '#B9A3D6' },
  { value: 'other',             en: 'Other',             zh: null,         color: '#8C90A3' },
]

/** 建立/編輯卡組的下拉選項，標籤與側邊欄一致（英文 + 中文） */
export const PRODUCT_TYPE_OPTIONS = PRODUCT_TYPES.map(t => ({
  value: t.value,
  label: t.zh ? `${t.en} (${t.zh})` : t.en,
}))

const THEME_FALLBACK = { label: '—', color: '#8C90A3' }

/** 時間軸用：顏色本身就是圖例，標籤取空間省的那個（中文優先） */
export function productTypeTheme(productType: string): { label: string; color: string } {
  const t = PRODUCT_TYPES.find(p => p.value === productType)
  return t ? { label: t.zh ?? t.en, color: t.color } : THEME_FALLBACK
}
