/** Full rarity list for Rush Duel, with Chinese display names.
 *  Ordered from least rare (index 0) to most rare (last index). */
export const RARITIES: { value: string; label: string }[] = [
  { value: 'N',      label: 'N (普通)' },
  { value: 'NPR',    label: 'NPR (普鑽)' },
  { value: 'R',      label: 'R (銀字)' },
  { value: 'SR',     label: 'SR (亮面)' },
  { value: 'SPR',    label: 'SPR (亮鑽)' },
  { value: 'UR',     label: 'UR (金亮)' },
  { value: 'PUR',    label: 'PUR (金亮鑽)' },
  { value: 'RUR',    label: 'RUR (紅亮)' },
  { value: 'SER',    label: 'SER (半鑽)' },
  { value: 'RR',     label: 'RR (超速貴罕)' },
  { value: 'ORR',    label: 'ORR (超越超速貴罕)' },
  { value: 'ORRPBV', label: 'ORRPBV (黑鑽超越超速)' },
  { value: 'FORR',   label: 'FORR (全超越超速罕貴)' },
]

export const RARITY_VALUES = RARITIES.map(r => r.value)

/**
 * Picks the variant key to show by default for a card.
 *
 * Priority rules (highest wins):
 * 1. If `preferredRarity` is given and exists in variants → use it
 *    (alt-art preferred over non-alt within the same rarity).
 * 2. Otherwise → pick the rarest variant by RARITY_VALUES order.
 *    Within the same rarity, alt-art wins over non-alt.
 *
 * Returns the variant key (e.g. "UR" or "UR-alt").
 */
import type { CardVariant } from '@/types/card'
import { variantKey } from '@/types/card'

export function pickDefaultVariantKey(
  variants: CardVariant[],
  preferredRarity?: string,
): string {
  if (!variants.length) return ''

  if (preferredRarity) {
    // Match by raw rarity value (e.g. "UR" matches both "UR" and "UR-alt")
    const matches = variants.filter(v => v.rarity === preferredRarity)
    if (matches.length) {
      const alt = matches.find(v => v.is_alternate_art)
      const chosen = alt ?? matches[0]
      if (chosen) return variantKey(chosen)
    }
  }

  // Sort: rarest first, alt-art beats non-alt within same rarity
  const sorted = [...variants].sort((a, b) => {
    const aIdx = RARITY_VALUES.indexOf(a.rarity)
    const bIdx = RARITY_VALUES.indexOf(b.rarity)
    if (aIdx !== bIdx) return bIdx - aIdx
    return (b.is_alternate_art ? 1 : 0) - (a.is_alternate_art ? 1 : 0)
  })

  const first = sorted[0]
  return first ? variantKey(first) : ''
}
