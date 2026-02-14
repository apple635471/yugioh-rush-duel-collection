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
  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
    <CardGridItem
      v-for="card in cards"
      :key="card.card_id"
      :card="card"
      @ownership-changed="emit('ownershipChanged')"
    />
  </div>
</template>
