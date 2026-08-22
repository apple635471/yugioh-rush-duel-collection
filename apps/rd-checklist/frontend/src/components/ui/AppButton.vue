<script setup lang="ts">
/**
 * 全站共用的 action 按鈕。
 *
 * 包一層 PrimeVue Button，把尺寸（高度／水平 padding／字級／icon 間距）鎖成固定
 * 的幾種，避免各處自己刻 <button> 或用不同 size 造成同一列按鈕高度不一致。
 *
 * 用法：
 *   <AppButton label="Edit" @click="..."><template #icon><svg .../></template></AppButton>
 *   <AppButton variant="filled" severity="warn" size="lg" fluid>Save</AppButton>
 *   <AppButton icon-only title="Add rarity"><template #icon><svg .../></template></AppButton>
 *   <AppButton tone="gold" size="sm">同名卡片</AppButton>
 *
 * 顏色分兩層：`severity` 走 PrimeVue 的語意色（warn/danger/...），`tone` 走本 App
 * 自己的色票（目前只有 gold），兩者擇一即可，給了 tone 就以 tone 為準。
 *
 * 不適用（維持各自寫法）：卡圖上的浮動 overlay 圓角小按鈕、OwnershipControl 的
 * ± 微調鈕、RarityTabs 的分頁、側邊欄收合把手 —— 這些是定位／形狀特殊的控制項，
 * 不是一般 action 按鈕。
 */
import { computed } from 'vue'
import Button from 'primevue/button'

const props = withDefaults(defineProps<{
  label?: string
  /** filled = 實心（主要動作）；outlined = 外框（次要）；text = 無框（輔助） */
  variant?: 'filled' | 'outlined' | 'text'
  severity?: 'primary' | 'secondary' | 'warn' | 'danger' | 'success' | 'info'
  /** App 自訂色票，覆蓋 severity；gold = 金色系（卡牌主題色） */
  tone?: 'gold'
  /** sm = 24px（密集列表／輔助）、md = 32px（工具列預設）、lg = 40px（主要 CTA）
   *  字級 sm 與 md 皆 12px、lg 14px；個別按鈕要調整就加 `!text-sm` 之類的 class */
  size?: 'sm' | 'md' | 'lg'
  /** 只有 icon 沒有文字 → 正方形 */
  iconOnly?: boolean
  /** 撐滿容器寬度 */
  fluid?: boolean
  disabled?: boolean
}>(), {
  variant: 'outlined',
  severity: 'secondary',
  size: 'md',
})

/** 高度固定，PrimeVue 的 padding 由 Tailwind utilities layer 覆蓋 */
const SIZES = {
  sm: { box: 'h-6', pad: 'px-2 gap-1', font: '0.75rem', icon: '0.75rem' },
  md: { box: 'h-8', pad: 'px-3 gap-1.5', font: '0.75rem', icon: '0.875rem' },
  lg: { box: 'h-10', pad: 'px-4 gap-2', font: '0.875rem', icon: '1rem' },
} as const

const sizeClass = computed(() => {
  const s = SIZES[props.size]
  return [s.box, props.iconOnly ? 'px-0 justify-center' : s.pad]
})
const iconSize = computed(() => SIZES[props.size].icon)
const fontSize = computed(() => SIZES[props.size].font)

const primeVariant = computed(() => props.variant === 'filled' ? undefined : props.variant)
</script>

<template>
  <Button
    :severity="severity"
    :variant="primeVariant"
    :disabled="disabled"
    :fluid="fluid"
    class="app-button whitespace-nowrap !py-0 leading-none"
    :class="[
      sizeClass,
      // fluid 按鈕要能被 flex 壓縮，不然並排兩顆各要 100% 寬會擠爆容器
      fluid ? 'flex-1 min-w-0' : 'shrink-0',
      tone ? `app-button--${tone} app-button--${tone}-${variant}` : null,
      { '!w-6': iconOnly && size === 'sm', '!w-8': iconOnly && size === 'md', '!w-10': iconOnly && size === 'lg' },
    ]"
    :style="{ '--app-button-icon': iconSize, '--app-button-font': fontSize }"
  >
    <slot name="icon" />
    <span v-if="!iconOnly && ($slots.default || label)"><slot>{{ label }}</slot></span>
  </Button>
</template>

<style scoped>
/* icon slot 內的 svg 統一尺寸，各處不用再各自標 w-3.5 h-3.5 */
.app-button :slotted(svg) {
  width: var(--app-button-icon);
  height: var(--app-button-icon);
  flex-shrink: 0;
}

/* ── tone: gold ──────────────────────────────────────────────────────────
   scoped style 未進 @layer，優先度高於 primevue layer，足以蓋掉 severity 配色 */
.app-button--gold {
  /* gold-dim (#6B5428) 是裝飾色，當文字只有 2.76:1；文字用 gold */
  color: var(--color-gold);
  transition: color .15s, border-color .15s, background-color .15s;
}
.app-button--gold:hover:not(:disabled) {
  color: var(--color-gold-light);
}
.app-button--gold-outlined {
  border-color: rgba(201, 168, 76, 0.3);
  background: transparent;
}
.app-button--gold-outlined:hover:not(:disabled) {
  border-color: rgba(201, 168, 76, 0.5);
  background: rgba(201, 168, 76, 0.08);
}
.app-button--gold-text {
  border-color: transparent;
  background: transparent;
}
.app-button--gold-text:hover:not(:disabled) {
  background: rgba(201, 168, 76, 0.1);
}
.app-button--gold-filled,
.app-button--gold-filled:hover:not(:disabled) {
  background: var(--color-gold);
  border-color: var(--color-gold);
  color: #09090f;
}
.app-button--gold-filled:hover:not(:disabled) {
  background: var(--color-gold-light);
}
</style>
