<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import type { CardVariant } from '@/types/card'
import { variantKey } from '@/types/card'
import { RARITY_VALUES } from '@/constants/rarities'
import Button from 'primevue/button'
import Popover from 'primevue/popover'

const props = defineProps<{
  variants: CardVariant[]
  activeRarity: string
  align?: 'start' | 'end'   // default 'end' (grid); use 'start' in sidebar
}>()

const emit = defineEmits<{
  select: [rarityKey: string]
}>()

const rarityColors: Record<string, string> = {
  // ── Common ──────────────────────────────────────────────────────────────
  N:           'text-gray-400 border-gray-400',        // 普通
  NPR:         'text-gray-300 border-gray-300',        // 普鑽（N + 鑽石加工）

  // ── Rare ────────────────────────────────────────────────────────────────
  R:           'text-blue-400 border-blue-400',        // 銀字

  // ── Super Rare ──────────────────────────────────────────────────────────
  SR:          'text-orange-400 border-orange-400',    // 亮面
  SPR:         'text-amber-400 border-amber-400',      // 亮鑽（SR + 鑽石）

  // ── Ultra Rare ──────────────────────────────────────────────────────────
  UR:          'text-gold border-gold',                // 金亮
  PUR:         'text-gold-light border-gold-light',    // 金亮鑽（UR + 鑽石）
  RUR:         'text-rose-400 border-rose-400',        // 紅亮（紅色 UR）

  // ── Secret Rare ─────────────────────────────────────────────────────────
  SER:         'text-red-400 border-red-400',          // 半鑽

  // ── Rush Rare ───────────────────────────────────────────────────────────
  RR:          'text-emerald-400 border-emerald-400',  // 超速貴罕

  // ── Over Rush Rare ──────────────────────────────────────────────────────
  ORR:         'text-purple-400 border-purple-400',    // 超越超速貴罕
  ORRPBV:      'text-zinc-300 border-zinc-500',        // 黑鑽超越超速（黑色調）
  FORR:        'text-teal-400 border-teal-400',        // 全超越超速罕貴（藍綠）

  // ── Legacy / other values ────────────────────────────────────────────────
  'OVER-RUSH': 'text-purple-400 border-purple-400',
  OR:          'text-purple-300 border-purple-300',
  RUSH:        'text-emerald-300 border-emerald-300',
  L:           'text-amber-300 border-amber-300',      // Legend
}

function getColor(rarity: string): string {
  return rarityColors[rarity] ?? 'text-gray-400 border-gray-400'
}

function tabLabel(v: CardVariant): string {
  return v.is_alternate_art ? `${v.rarity} ★` : v.rarity
}

// ── Sorted variants: rarest first, alt-art before non-alt within same rarity ──
const sortedVariants = computed<CardVariant[]>(() =>
  [...props.variants].sort((a, b) => {
    const aIdx = RARITY_VALUES.indexOf(a.rarity)
    const bIdx = RARITY_VALUES.indexOf(b.rarity)
    if (aIdx !== bIdx) return bIdx - aIdx
    return (b.is_alternate_art ? 1 : 0) - (a.is_alternate_art ? 1 : 0)
  })
)

// ── Overflow measurement ──────────────────────────────────────────────────
const containerRef = ref<HTMLElement | null>(null)
const badgeRef     = ref<HTMLElement | null>(null)
const popoverRef   = ref<InstanceType<typeof Popover> | null>(null)

const cutoff    = ref<number | null>(null)  // null = show all
const measured  = ref(false)               // false = phase-1 (invisible, all tabs shown)

const GAP = 4  // gap-1 = 4px

/**
 * Two-phase measurement:
 *   Phase 1 – cutoff=null, measured=false → all tabs render invisibly → measure real widths
 *   Phase 2 – set cutoff, measured=true   → final render with correct tabs + badge
 */
async function measure() {
  if (measuring) return
  measuring = true
  // ── Phase 1: show all tabs, hide from user ──
  cutoff.value   = null
  measured.value = false
  await nextTick()

  const container = containerRef.value
  if (!container) { measured.value = true; measuring = false; return }

  const available = container.clientWidth
  // Container not yet laid out — stay invisible and wait for ResizeObserver
  if (available <= 0) { measuring = false; return }

  const tabEls = Array.from(container.querySelectorAll<HTMLElement>('[data-rarity-tab]'))
  if (!tabEls.length) { measured.value = true; measuring = false; return }

  // Measure badge width from its actual rendered element (it's always in the DOM in phase 1)
  const badgeW = badgeRef.value ? badgeRef.value.offsetWidth + GAP : 36

  let used = 0
  let newCutoff: number | null = null

  for (let i = 0; i < tabEls.length; i++) {
    const w         = tabEls[i]!.offsetWidth
    const gap       = i === 0 ? 0 : GAP
    const remaining = tabEls.length - i - 1
    const badgeCost = remaining > 0 ? badgeW : 0

    if (used + gap + w + badgeCost <= available) {
      used += gap + w
    } else {
      newCutoff = i
      break
    }
  }

  // ── Phase 2: apply cutoff, reveal ──
  cutoff.value   = newCutoff
  measured.value = true
  measuring = false
  // Update row-width baseline so ResizeObserver doesn't immediately re-fire
  lastRowW = containerRef.value?.parentElement?.parentElement?.clientWidth ?? lastRowW
}

// ── Visible / hidden split ───────────────────────────────────────────────
const visibleVariants = computed<CardVariant[]>(() => {
  // Phase 1 or all-fit: show everything
  if (cutoff.value === null) return sortedVariants.value

  const sliced    = sortedVariants.value.slice(0, cutoff.value)
  const activeIdx = sortedVariants.value.findIndex(v => variantKey(v) === props.activeRarity)

  // If active tab would be hidden, swap it into the last visible slot
  if (activeIdx === -1 || activeIdx < cutoff.value) return sliced
  return [...sliced.slice(0, -1), sortedVariants.value[activeIdx]!]
})

const hiddenVariants = computed<CardVariant[]>(() => {
  if (cutoff.value === null) return []
  const visKeys = new Set(visibleVariants.value.map(v => variantKey(v)))
  return sortedVariants.value.filter(v => !visKeys.has(variantKey(v)))
})

// ── Popover ──────────────────────────────────────────────────────────────
function openPopover(e: MouseEvent) {
  popoverRef.value?.toggle(e)
}

function selectHidden(v: CardVariant) {
  popoverRef.value?.hide()
  emit('select', variantKey(v))
}

// ── Lifecycle ────────────────────────────────────────────────────────────
let ro: ResizeObserver | null = null
let measuring = false
// Track the last grandparent (row) width so we only re-measure on external
// layout changes, not on our own phase-1↔2 container resize.
let lastRowW = -1

function scheduleIfRowChanged() {
  const rowW = containerRef.value?.parentElement?.parentElement?.clientWidth ?? 0
  if (rowW !== lastRowW) {
    lastRowW = rowW
    measure()
  }
}

onMounted(() => {
  measure()
  if (containerRef.value) {
    ro = new ResizeObserver(scheduleIfRowChanged)
    ro.observe(containerRef.value)
  }
})
onBeforeUnmount(() => ro?.disconnect())
watch(() => [props.variants, props.activeRarity], measure, { deep: true })
</script>

<template>
  <template v-if="sortedVariants.length > 1">
    <!--
      Single container for both phases.
      Phase 1 (measured=false): opacity-0, all tabs visible, no overflow clipping → measure real widths.
      Phase 2 (measured=true):  opacity-100, overflow-hidden, only visibleVariants shown.
    -->
    <div
      ref="containerRef"
      class="flex-1 flex items-center gap-1 min-w-0 transition-none"
      :class="[
        measured ? 'overflow-hidden opacity-100' : 'overflow-visible opacity-0',
        align === 'start' ? 'justify-start' : 'justify-end',
      ]"
    >
      <Button
        v-for="v in visibleVariants"
        :key="variantKey(v)"
        data-rarity-tab
        @click="emit('select', variantKey(v))"
        variant="text"
        size="small"
        :class="[
          'px-2 py-0.5 text-sm font-semibold rounded border transition-all shrink-0',
          getColor(v.rarity),
          variantKey(v) === activeRarity
            ? 'bg-white/15 opacity-100'
            : 'opacity-50 hover:opacity-80 border-transparent',
        ]"
      >{{ tabLabel(v) }}</Button>

      <!--
        Badge: always rendered in phase 1 so we can measure its real width.
        Hidden in phase 2 when there's nothing to collapse.
      -->
      <button
        ref="badgeRef"
        @click.stop="openPopover($event)"
        :class="[
          'shrink-0 px-2 py-0.5 text-sm font-semibold rounded border whitespace-nowrap transition-colors cursor-pointer',
          'border-gold/40 text-gold/55 hover:text-gold hover:border-gold/70',
          // Phase 1: invisible placeholder for measurement; Phase 2: hide if not needed
          !measured || hiddenVariants.length > 0 ? '' : 'hidden',
        ]"
      >+{{ measured ? hiddenVariants.length : sortedVariants.length }}</button>

      <Popover ref="popoverRef">
        <div class="flex flex-col gap-0.5 p-1 min-w-[80px]">
          <button
            v-for="v in hiddenVariants"
            :key="variantKey(v)"
            @click="selectHidden(v)"
            :class="[
              'px-3 py-1 text-sm font-semibold rounded border text-left transition-all whitespace-nowrap',
              getColor(v.rarity),
              variantKey(v) === activeRarity
                ? 'bg-white/15 opacity-100'
                : 'opacity-60 hover:opacity-100 border-transparent hover:border-current',
            ]"
          >{{ tabLabel(v) }}</button>
        </div>
      </Popover>
    </div>
  </template>

  <span
    v-else-if="sortedVariants.length === 1 && sortedVariants[0]"
    class="text-sm font-semibold px-2 py-0.5 rounded border bg-white/15"
    :class="getColor(sortedVariants[0].rarity)"
  >{{ tabLabel(sortedVariants[0]) }}</span>
</template>
