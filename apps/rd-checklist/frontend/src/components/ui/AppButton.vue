<script setup lang="ts">
/**
 * 全站共用的 action 按鈕。
 *
 * 包一層 PrimeVue Button，把尺寸（高度／水平 padding／字級／icon 間距）鎖成固定
 * 的幾種，避免各處自己刻 <button> 或用不同 size 造成同一列按鈕高度不一致。
 *
 * 用法：
 *   <AppButton label="Edit" @click="..."><template #icon><svg .../></template></AppButton>
 *   <AppButton variant="filled" severity="warn">Save</AppButton>
 */
import { computed } from 'vue'
import Button from 'primevue/button'

const props = withDefaults(defineProps<{
  label?: string
  /** filled = 實心（主要動作）；outlined = 外框（次要）；text = 無框（輔助） */
  variant?: 'filled' | 'outlined' | 'text'
  severity?: 'primary' | 'secondary' | 'warn' | 'danger' | 'success' | 'info'
  /** sm = 24px 高（密集列表內），md = 32px 高（工具列預設） */
  size?: 'sm' | 'md'
  disabled?: boolean
}>(), {
  variant: 'outlined',
  severity: 'secondary',
  size: 'md',
})

/** 高度固定，PrimeVue 的 padding 由 Tailwind utilities layer 覆蓋 */
const sizeClass = computed(() => props.size === 'sm'
  ? 'h-6 px-2 gap-1 !text-[11px]'
  : 'h-8 px-3 gap-1.5 !text-xs')

const primeVariant = computed(() => props.variant === 'filled' ? undefined : props.variant)
</script>

<template>
  <Button
    :severity="severity"
    :variant="primeVariant"
    :disabled="disabled"
    class="app-button shrink-0 whitespace-nowrap !py-0 leading-none"
    :class="sizeClass"
  >
    <slot name="icon" />
    <span v-if="$slots.default || label"><slot>{{ label }}</slot></span>
  </Button>
</template>

<style scoped>
/* icon slot 內的 svg 統一尺寸，各處不用再各自標 w-3.5 h-3.5 */
.app-button :slotted(svg) {
  width: 0.875rem;
  height: 0.875rem;
  flex-shrink: 0;
}
</style>
