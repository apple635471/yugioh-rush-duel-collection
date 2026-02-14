<script setup lang="ts">
import type { CardVariant } from '@/types/card'

defineProps<{
  variants: CardVariant[]
  activeRarity: string
}>()

const emit = defineEmits<{
  select: [rarity: string]
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
</script>

<template>
  <div v-if="variants.length > 1" class="flex items-center gap-1">
    <button
      v-for="v in variants"
      :key="v.rarity"
      @click="emit('select', v.rarity)"
      class="px-2 py-0.5 text-xs font-medium rounded border transition-all"
      :class="[
        getColor(v.rarity),
        v.rarity === activeRarity
          ? 'bg-white/10 opacity-100'
          : 'opacity-40 hover:opacity-70 border-transparent'
      ]"
    >
      {{ v.rarity }}
    </button>
  </div>
  <span
    v-else-if="variants.length === 1"
    class="text-xs font-medium px-2 py-0.5 rounded"
    :class="getColor(variants[0].rarity)"
  >
    {{ variants[0].rarity }}
  </span>
</template>
