/** Full rarity list for Rush Duel, with Chinese display names.
 *  Ordered from least rare (index 0) to most rare (last index). */
export const RARITIES: { value: string; label: string }[] = [
  { value: 'N',      label: 'N (普通)' },
  { value: 'NPR',    label: 'NPR (普鑽)' },
  { value: 'R',      label: 'R (銀字)' },
  { value: 'SR',     label: 'SR (亮面)' },
  { value: 'SPR',    label: 'SPR (亮鑽)' },
  { value: 'UR',     label: 'UR (金亮)' },
  { value: 'UPR',    label: 'UPR (金亮鑽)' },
  { value: 'RUR',    label: 'RUR (紅亮)' },
  { value: 'SER',    label: 'SER (半鑽)' },
  { value: 'RR',     label: 'RR (超速貴罕)' },
  { value: 'GRR',    label: 'GRR (黃金超速貴罕)' },
  { value: 'ORR',    label: 'ORR (超越超速貴罕)' },
  { value: 'ORRPBV', label: 'ORRPBV (黑鑽超越超速)' },
  { value: 'FORR',   label: 'FORR (全超越超速罕貴)' },
]

export const RARITY_VALUES = RARITIES.map(r => r.value)

import type { CardVariant } from '@/types/card'
import { variantKey } from '@/types/card'

/** How the default-displayed variant is chosen for a card. */
export type VariantDisplayMode = 'highest' | 'owned'

/**
 * Rarity rank for display ordering — higher number = rarer / shown first.
 *
 * Deliberately differs from RARITY_VALUES in one way: **SER is treated as the
 * lowest rarity** (below N). Everything else keeps its RARITY_VALUES order.
 * Unknown rarities rank below SER.
 */
export function displayRarityRank(rarity: string): number {
  if (rarity === 'SER') return -1
  const idx = RARITY_VALUES.indexOf(rarity)
  return idx === -1 ? -2 : idx
}

/**
 * Sort comparator for variants in display order:
 *   1. rarer first (SER forced lowest, see displayRarityRank)
 *   2. within the same rarity, the original art comes before its alt-art
 */
export function compareVariantsForDisplay(a: CardVariant, b: CardVariant): number {
  const ra = displayRarityRank(a.rarity)
  const rb = displayRarityRank(b.rarity)
  if (ra !== rb) return rb - ra
  return (a.is_alternate_art ? 1 : 0) - (b.is_alternate_art ? 1 : 0)
}

/** Returns a copy of `variants` sorted in display order. */
export function orderVariantsForDisplay(variants: CardVariant[]): CardVariant[] {
  return [...variants].sort(compareVariantsForDisplay)
}

/**
 * Picks the variant key to show by default for a card.
 *
 * Priority rules (highest wins):
 * 1. If `preferredRarity` is given and exists in variants → use it
 *    (original art preferred over alt-art within the same rarity).
 * 2. If `mode === 'owned'` → the rarest variant you actually own; falls back to
 *    the rarest overall when none are owned.
 * 3. Otherwise (`mode === 'highest'`) → the rarest variant overall.
 *
 * Ordering follows `compareVariantsForDisplay` (SER lowest, original before alt).
 * Returns the variant key (e.g. "UR" or "UR-alt").
 */
export function pickDefaultVariantKey(
  variants: CardVariant[],
  preferredRarity?: string,
  mode: VariantDisplayMode = 'highest',
): string {
  if (!variants.length) return ''

  if (preferredRarity) {
    // Match by raw rarity value (e.g. "UR" matches both "UR" and "UR-alt")
    const matches = orderVariantsForDisplay(
      variants.filter(v => v.rarity === preferredRarity),
    )
    if (matches[0]) return variantKey(matches[0])
  }

  const ordered = orderVariantsForDisplay(variants)

  if (mode === 'owned') {
    const owned = ordered.find(v => v.owned_count > 0)
    if (owned) return variantKey(owned)
  }

  return ordered[0] ? variantKey(ordered[0]) : ''
}
