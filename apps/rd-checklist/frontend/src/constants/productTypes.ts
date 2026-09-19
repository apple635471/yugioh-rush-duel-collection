import type { ProductType } from '@/types/cardSet'

/**
 * 顯示用的小工具。分類本身（代號、名稱、顏色、規則）全部存在 DB，
 * 由 `GET /api/product-types` 取得後放在 cardSets store —— 這裡不再有任何
 * 寫死的清單，新增或改名一個分類不用動程式。
 */

/** 沒有對應資料時的顏色（例如規則剛被刪掉、清單還沒重抓）*/
export const PRODUCT_TYPE_FALLBACK_COLOR = '#8C90A3'

/** 完整標籤（英文 + 中文），與側邊欄一致 */
export function productTypeLabel(pt: ProductType | undefined, code = ''): string {
  if (!pt) return code
  return pt.name_zh ? `${pt.name_en} (${pt.name_zh})` : pt.name_en
}

/** 時間軸用：顏色本身就是圖例，標籤取省空間的那個（中文優先）*/
export function productTypeTheme(pt: ProductType | undefined) {
  return {
    label: pt?.name_zh || pt?.name_en || '—',
    color: pt?.color || PRODUCT_TYPE_FALLBACK_COLOR,
  }
}
