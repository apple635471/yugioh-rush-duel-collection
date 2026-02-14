<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Card } from '@/types/card'
import { getCardImageUrl, updateOwnership } from '@/api/cards'
import RarityTabs from '@/components/cards/RarityTabs.vue'
import OwnershipControl from '@/components/cards/OwnershipControl.vue'
import CardEditForm from './CardEditForm.vue'

const props = defineProps<{
  card: Card
  activeRarity: string
}>()

const emit = defineEmits<{
  cardUpdated: []
}>()

const currentRarity = ref(props.activeRarity)
const showEditForm = ref(false)

const activeVariant = computed(() =>
  props.card.variants.find(v => v.rarity === currentRarity.value) ?? props.card.variants[0]
)

const imageUrl = computed(() =>
  activeVariant.value ? getCardImageUrl(props.card.card_id, activeVariant.value.rarity) : ''
)

async function onOwnershipUpdate(cardId: string, rarity: string, count: number) {
  await updateOwnership(cardId, rarity, count)
  const v = props.card.variants.find(v => v.card_id === cardId && v.rarity === rarity)
  if (v) v.owned_count = count
}

// Detail rows for card info
const detailRows = computed(() => {
  const c = props.card
  const rows: { label: string; value: string }[] = []
  rows.push({ label: 'Card ID', value: c.card_id })
  rows.push({ label: 'Type', value: c.card_type })
  if (c.attribute) rows.push({ label: 'Attribute', value: c.attribute })
  if (c.monster_type) rows.push({ label: 'Race', value: c.monster_type })
  if (c.level != null) rows.push({ label: 'Level', value: String(c.level) })
  if (c.atk != null) rows.push({ label: 'ATK', value: String(c.atk) })
  if (c.defense != null) rows.push({ label: 'DEF', value: String(c.defense) })
  return rows
})
</script>

<template>
  <div class="p-5">
    <!-- Image -->
    <div class="aspect-[59/86] bg-gray-800 rounded-lg overflow-hidden mb-4">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="card.name_zh || card.name_jp"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-gray-600">
        No Image
      </div>
    </div>

    <!-- Rarity tabs -->
    <div class="flex items-center justify-between mb-3">
      <RarityTabs
        :variants="card.variants"
        :active-rarity="currentRarity"
        @select="currentRarity = $event"
      />
      <OwnershipControl
        :card-id="card.card_id"
        :rarity="currentRarity"
        :owned-count="activeVariant?.owned_count ?? 0"
        @update="onOwnershipUpdate"
      />
    </div>

    <!-- Card names -->
    <div class="mb-4">
      <h2 class="text-lg font-bold text-gray-100 leading-snug">
        {{ card.name_zh || card.name_jp }}
      </h2>
      <p v-if="card.name_zh && card.name_jp" class="text-sm text-gray-400 mt-0.5">
        {{ card.name_jp }}
      </p>
      <div v-if="card.is_legend" class="mt-1">
        <span class="bg-amber-500/90 text-black text-xs font-bold px-1.5 py-0.5 rounded">LEGEND</span>
      </div>
    </div>

    <!-- Detail table -->
    <div class="bg-gray-800/50 rounded-lg overflow-hidden mb-4">
      <div
        v-for="row in detailRows"
        :key="row.label"
        class="flex items-center px-3 py-2 border-b border-gray-800 last:border-b-0"
      >
        <span class="w-20 text-xs text-gray-500 shrink-0">{{ row.label }}</span>
        <span class="text-sm text-gray-200 font-mono">{{ row.value }}</span>
      </div>
    </div>

    <!-- Condition / Effect -->
    <div v-if="card.condition" class="mb-3">
      <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-1">Condition</h3>
      <p class="text-sm text-gray-300 leading-relaxed whitespace-pre-line">{{ card.condition }}</p>
    </div>
    <div v-if="card.effect" class="mb-4">
      <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-1">Effect</h3>
      <p class="text-sm text-gray-300 leading-relaxed whitespace-pre-line">{{ card.effect }}</p>
    </div>

    <!-- Edit button -->
    <button
      @click="showEditForm = !showEditForm"
      class="w-full py-2 text-sm text-gray-400 hover:text-yellow-400 border border-gray-700 rounded-lg hover:border-yellow-500/50 transition-colors"
    >
      {{ showEditForm ? 'Cancel Edit' : 'Edit Card Info' }}
    </button>

    <!-- Edit form -->
    <CardEditForm
      v-if="showEditForm"
      :card="card"
      class="mt-4"
      @saved="showEditForm = false; emit('cardUpdated')"
    />
  </div>
</template>
