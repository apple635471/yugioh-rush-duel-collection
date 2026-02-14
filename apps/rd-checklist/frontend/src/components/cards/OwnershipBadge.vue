<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  ownedCount: number
  compact?: boolean
}>()

const isOwned = computed(() => props.ownedCount > 0)
</script>

<template>
  <span
    class="inline-flex items-center justify-center rounded-full font-medium transition-colors"
    :class="[
      compact ? 'text-xs px-1.5 py-0.5 min-w-[1.25rem]' : 'text-xs px-2 py-0.5 min-w-[1.5rem]',
      isOwned
        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
        : 'bg-gray-700/50 text-gray-500 border border-gray-700',
    ]"
  >
    {{ ownedCount }}
  </span>
</template>
