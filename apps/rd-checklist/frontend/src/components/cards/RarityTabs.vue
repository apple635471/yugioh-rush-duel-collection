<script setup lang="ts">
import type { CardVariant } from '@/types/card'
import { variantKey } from '@/types/card'
import Button from 'primevue/button'

defineProps<{
  variants: CardVariant[]
  activeRarity: string
}>()

const emit = defineEmits<{
  select: [rarityKey: string]
}>()

const rarityColors: Record<string, string> = {
  UR: 'text-yellow-400 border-yellow-400',
  SER: 'text-red-400 border-red-400',
  SR: 'text-orange-400 border-orange-400',
  R: 'text-blue-400 border-blue-400',
  N: 'text-gray-400 border-gray-400',
  'OVER-RUSH': 'text-purple-400 border-purple-400',
  OR: 'text-purple-400 border-purple-400',
  RUSH: 'text-cyan-400 border-cyan-400',
  L: 'text-amber-300 border-amber-300',
}

function getColor(rarity: string): string {
  return rarityColors[rarity] ?? 'text-gray-400 border-gray-400'
}

function tabLabel(v: CardVariant): string {
  return v.is_alternate_art ? `${v.rarity} ★` : v.rarity
}
</script>

<template>
  <div v-if="variants.length > 1" class="flex items-center gap-1">
    <Button
      v-for="v in variants"
      :key="variantKey(v)"
      @click="emit('select', variantKey(v))"
      variant="text"
      size="small"
      :class="[
        'px-2 py-0.5 text-sm font-semibold rounded border transition-all',
        getColor(v.rarity),
        variantKey(v) === activeRarity
          ? 'bg-white/15 opacity-100'
          : 'opacity-50 hover:opacity-80 border-transparent',
      ]"
    >
      {{ tabLabel(v) }}
    </Button>
  </div>
  <span
    v-else-if="variants.length === 1 && variants[0]"
    class="text-sm font-semibold px-2 py-0.5 rounded"
    :class="getColor(variants[0].rarity)"
  >
    {{ tabLabel(variants[0]) }}
  </span>
</template>
