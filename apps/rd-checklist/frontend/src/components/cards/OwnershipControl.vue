<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  cardId: string
  rarity: string
  ownedCount: number
}>()

const emit = defineEmits<{
  update: [cardId: string, rarity: string, count: number]
}>()

const localCount = ref(props.ownedCount)

watch(() => props.ownedCount, (v) => { localCount.value = v })

function increment() {
  localCount.value++
  emit('update', props.cardId, props.rarity, localCount.value)
}

function decrement() {
  if (localCount.value > 0) {
    localCount.value--
    emit('update', props.cardId, props.rarity, localCount.value)
  }
}
</script>

<template>
  <div class="flex items-center gap-1" @click.stop>
    <button
      @click="decrement"
      :disabled="localCount <= 0"
      class="w-7 h-7 flex items-center justify-center rounded text-base font-bold transition-colors"
      :class="localCount > 0
        ? 'bg-gray-600 text-gray-200 hover:bg-gray-500 hover:text-white'
        : 'bg-gray-700 text-gray-500 cursor-not-allowed'"
    >
      -
    </button>
    <span
      class="w-8 text-center text-base font-semibold"
      :class="localCount > 0 ? 'text-emerald-400' : 'text-gray-400'"
    >
      {{ localCount }}
    </span>
    <button
      @click="increment"
      class="w-7 h-7 flex items-center justify-center rounded bg-gray-600 text-gray-200 hover:bg-gray-500 hover:text-white text-base font-bold transition-colors"
    >
      +
    </button>
  </div>
</template>
