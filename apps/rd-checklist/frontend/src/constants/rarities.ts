/** Full rarity list for Rush Duel, with Chinese display names. */
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
