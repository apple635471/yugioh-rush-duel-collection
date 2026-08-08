/** Validation helpers for card stat fields. */

/** ATK / DEF / Maximum-ATK: must be empty, "?", or a whole number. */
export function isStatValid(v: string | null | undefined): boolean {
  return v == null || v === '' || v === '?' || /^\d+$/.test(v)
}

/** Level: must be empty, or an integer within 1–12. */
export function isLevelValid(v: number | null | undefined): boolean {
  return v == null || (Number.isInteger(v) && v >= 1 && v <= 12)
}
