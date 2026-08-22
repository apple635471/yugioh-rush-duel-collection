import api from './client'
import type { CardSet, CardSetCreate, CardSetWithCards, ProductType, OwnershipStats, CardSetUpdate, CardSetOverride } from '@/types/cardSet'

export async function fetchProductTypes(): Promise<ProductType[]> {
  const { data } = await api.get<ProductType[]>('/card-sets/product-types')
  return data
}

export async function fetchCardSets(productType?: string): Promise<CardSet[]> {
  const params = productType ? { product_type: productType } : {}
  const { data } = await api.get<CardSet[]>('/card-sets', { params })
  return data
}

export async function fetchCardSet(setId: string): Promise<CardSetWithCards> {
  const { data } = await api.get<CardSetWithCards>(`/card-sets/${setId}`)
  return data
}

export async function fetchSetStats(setId: string): Promise<OwnershipStats> {
  const { data } = await api.get<OwnershipStats>(`/ownership/stats/${setId}`)
  return data
}

export async function fetchGlobalStats(): Promise<OwnershipStats> {
  const { data } = await api.get<OwnershipStats>('/ownership/stats')
  return data
}

export async function fetchAllSetStats(): Promise<Record<string, OwnershipStats>> {
  const { data } = await api.get<Record<string, OwnershipStats>>('/ownership/stats-bulk')
  return data
}

export async function updateCardSet(setId: string, update: CardSetUpdate): Promise<CardSet> {
  const { data } = await api.patch<CardSet>(`/card-sets/${setId}`, update)
  return data
}

export async function fetchCardSetOverrides(setId: string): Promise<CardSetOverride[]> {
  const { data } = await api.get<CardSetOverride[]>(`/card-sets/${setId}/overrides`)
  return data
}

export async function deleteCardSetOverride(setId: string, fieldName: string): Promise<void> {
  await api.delete(`/card-sets/${setId}/overrides/${fieldName}`)
}

export async function createCardSet(data: CardSetCreate): Promise<CardSet> {
  const { data: result } = await api.post<CardSet>('/card-sets', data)
  return result
}

// ── 卡表對照（yugipedia）────────────────────────────────

export interface MissingPrinting {
  card_id: string
  rarity: string
  is_alternate_art: boolean
  name_en: string
  name_jp: string
  /** 卡片本身已存在，只是缺這個貴罕度 */
  card_exists: boolean
}

export interface ExtraPrinting {
  card_id: string
  rarity: string
  is_alternate_art: boolean
  name_jp: string
  name_zh: string
  owned_count: number
  /** 這是該卡唯一的 variant，刪掉等於刪整張卡 */
  is_only_variant: boolean
}

export interface RemapPrinting {
  card_id: string
  from_rarity: string
  to_rarity: string
  is_alternate_art: boolean
  name_jp: string
  name_zh: string
  owned_count: number
}

export interface SetListCompare {
  list_page: string
  expected_count: number
  actual_count: number
  missing: MissingPrinting[]
  extra: ExtraPrinting[]
  /** 貴罕度記錯：改名即可，持有數與上傳圖都保住 */
  remap: RemapPrinting[]
  unknown_rarities: string[]
}

export interface PrintingRef {
  card_id: string
  rarity: string
  is_alternate_art?: boolean
  name_jp?: string
}

export interface PrintingRemapRef {
  card_id: string
  from_rarity: string
  to_rarity: string
  is_alternate_art?: boolean
}

export interface SetListApplyResult {
  variants_remapped: number
  cards_created: number
  variants_created: number
  variants_deleted: number
  cards_deleted: number
  errors: string[]
}

export async function compareSetList(setId: string, url: string): Promise<SetListCompare> {
  const { data } = await api.post<SetListCompare>(`/card-sets/${setId}/compare`, { url })
  return data
}

export async function applySetListDiff(
  setId: string,
  payload: { remap?: PrintingRemapRef[]; create: PrintingRef[]; delete: PrintingRef[] },
): Promise<SetListApplyResult> {
  const { data } = await api.post<SetListApplyResult>(`/card-sets/${setId}/compare/apply`, payload)
  return data
}
