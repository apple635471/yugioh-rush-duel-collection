import api from './client'
import type { ProductType } from '@/types/cardSet'

/** 產品分類規則：卡組屬於哪一類完全由這些規則決定，卡組本身不存分類。 */

export async function fetchProductTypes(): Promise<ProductType[]> {
  const { data } = await api.get<ProductType[]>('/product-types')
  return data
}

export interface ProductTypeDraft {
  code: string
  name_en: string
  name_zh: string | null
  group_label: string
  color: string
  rules: string[]
}

/** 每個寫入端點都回傳最新的完整清單——改規則會影響所有分類的卡組數 */
export async function createProductType(draft: ProductTypeDraft): Promise<ProductType[]> {
  const { data } = await api.post<ProductType[]>('/product-types', draft)
  return data
}

export async function updateProductType(
  code: string,
  patch: Partial<ProductTypeDraft>,
): Promise<ProductType[]> {
  const { data } = await api.patch<ProductType[]>(`/product-types/${code}`, patch)
  return data
}

export async function deleteProductType(code: string): Promise<ProductType[]> {
  const { data } = await api.delete<ProductType[]>(`/product-types/${code}`)
  return data
}

export async function reorderProductTypes(codes: string[]): Promise<ProductType[]> {
  const { data } = await api.put<ProductType[]>('/product-types/order', { codes })
  return data
}

export interface RulePreview {
  set_ids: string[]
  /** 這些卡組目前實際歸在哪一類（順序在前的類型先認領） */
  claimed_elsewhere: Record<string, string>
}

export async function previewRules(patterns: string[]): Promise<RulePreview> {
  const { data } = await api.post<RulePreview>('/product-types/preview', { patterns })
  return data
}
