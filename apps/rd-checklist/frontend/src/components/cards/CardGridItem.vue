<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Card } from '@/types/card'
import { getCardImageUrl, updateOwnership } from '@/api/cards'
import { useUiStore } from '@/stores/ui'
import OwnershipBadge from './OwnershipBadge.vue'
import RarityTabs from './RarityTabs.vue'
import OwnershipControl from './OwnershipControl.vue'

const props = defineProps<{
  card: Card
}>()

const emit = defineEmits<{
  ownershipChanged: []
}>()

const ui = useUiStore()
const activeRarity = ref(props.card.variants[0]?.rarity ?? '')

const activeVariant = computed(() =>
  props.card.variants.find(v => v.rarity === activeRarity.value) ?? props.card.variants[0]
)

const imageUrl = computed(() => {
  if (!activeVariant.value) return ''
  const base = getCardImageUrl(props.card.card_id, activeVariant.value.rarity)
  // Bust cache for user-uploaded images (URL stays the same but file changes)
  return activeVariant.value.image_source === 'user_upload' ? `${base}?t=1` : base
})

const isOwned = computed(() => activeVariant.value?.owned_count ?? 0 > 0)

const shortId = computed(() => {
  // "RD/KP23-JP000" → "JP000"
  const parts = props.card.card_id.split('-')
  return parts.length > 1 ? parts[parts.length - 1] : props.card.card_id
})

function openDetail() {
  ui.openSidebar(props.card.card_id, activeRarity.value)
}

async function onOwnershipUpdate(cardId: string, rarity: string, count: number) {
  await updateOwnership(cardId, rarity, count)
  // Update local variant
  const v = props.card.variants.find(v => v.card_id === cardId && v.rarity === rarity)
  if (v) v.owned_count = count
  emit('ownershipChanged')
}
</script>

<template>
  <div
    @click="openDetail"
    class="group relative bg-gray-800 border border-gray-700 rounded-lg overflow-hidden cursor-pointer hover:border-yellow-500/50 transition-all"
    :class="{ 'ring-1 ring-yellow-500/20': ui.sidebarCardId === card.card_id }"
  >
    <!-- Image -->
    <div class="aspect-[59/86] bg-gray-700 relative overflow-hidden">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="card.name_zh || card.name_jp"
        class="w-full h-full object-cover transition-all"
        :class="{ 'grayscale opacity-40': !isOwned }"
        loading="lazy"
      />
      <div
        v-else
        class="w-full h-full flex items-center justify-center text-gray-600 text-xs"
      >
        No Image
      </div>

      <!-- Ownership badge overlay -->
      <div class="absolute top-1.5 right-1.5">
        <OwnershipBadge :owned-count="activeVariant?.owned_count ?? 0" compact />
      </div>

      <!-- Legend badge -->
      <div
        v-if="card.is_legend"
        class="absolute top-1.5 left-1.5 bg-amber-500/90 text-black text-[10px] font-bold px-1 py-0.5 rounded"
      >
        LEGEND
      </div>
    </div>

    <!-- Info -->
    <div class="p-2.5">
      <div class="flex items-center justify-between gap-1 mb-1">
        <span class="text-xs font-mono text-gray-400">{{ shortId }}</span>
        <RarityTabs
          :variants="card.variants"
          :active-rarity="activeRarity"
          @select="activeRarity = $event"
        />
      </div>
      <h4 class="text-sm font-medium text-gray-100 leading-snug line-clamp-2 group-hover:text-yellow-400 transition-colors">
        {{ card.name_zh || card.name_jp }}
      </h4>
      <p class="text-xs text-gray-400 mt-0.5">{{ card.card_type }}</p>

      <!-- Ownership control -->
      <div class="mt-2 flex justify-center">
        <OwnershipControl
          :card-id="card.card_id"
          :rarity="activeRarity"
          :owned-count="activeVariant?.owned_count ?? 0"
          @update="onOwnershipUpdate"
        />
      </div>
    </div>
  </div>
</template>
