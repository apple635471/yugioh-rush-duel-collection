<script setup lang="ts">
import type { Card } from '@/types/card'
import CardGridItem from './CardGridItem.vue'

defineProps<{
  cards: Card[]
}>()

const emit = defineEmits<{
  ownershipChanged: []
}>()
</script>

<template>
  <!-- auto-fill + minmax lets columns naturally shrink as container narrows (no hard jumps) -->
  <div
    class="grid gap-3"
    style="grid-template-columns: repeat(auto-fill, minmax(190px, 1fr))"
  >
    <CardGridItem
      v-for="card in cards"
      :key="card.card_id"
      :card="card"
      @ownership-changed="emit('ownershipChanged')"
    />
  </div>
</template>
