<script setup lang="ts">
import { ref } from 'vue'
import type { Card } from '@/types/card'
import { updateOwnership } from '@/api/cards'
import { useUiStore } from '@/stores/ui'
import OwnershipBadge from './OwnershipBadge.vue'
import RarityTabs from './RarityTabs.vue'
import OwnershipControl from './OwnershipControl.vue'

defineProps<{
  cards: Card[]
}>()

const emit = defineEmits<{
  ownershipChanged: []
}>()

const ui = useUiStore()

// Track active rarity per card
const activeRarities = ref<Record<string, string>>({})

function getActiveRarity(card: Card): string {
  return activeRarities.value[card.card_id] ?? card.variants[0]?.rarity ?? ''
}

function setActiveRarity(cardId: string, rarity: string) {
  activeRarities.value[cardId] = rarity
}

function getActiveVariant(card: Card) {
  const rarity = getActiveRarity(card)
  return card.variants.find(v => v.rarity === rarity) ?? card.variants[0]
}

function openDetail(card: Card) {
  ui.openSidebar(card.card_id, getActiveRarity(card))
}

function shortId(cardId: string): string {
  const parts = cardId.split('-')
  return parts.length > 1 ? parts[parts.length - 1] : cardId
}

async function onOwnershipUpdate(cardId: string, rarity: string, count: number, card: Card) {
  await updateOwnership(cardId, rarity, count)
  const v = card.variants.find(v => v.card_id === cardId && v.rarity === rarity)
  if (v) v.owned_count = count
  emit('ownershipChanged')
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full text-base">
      <thead>
        <tr class="border-b-2 border-gray-600 text-left text-xs text-gray-300 uppercase tracking-wider font-semibold">
          <th class="py-2.5 px-3 w-24">ID</th>
          <th class="py-2.5 px-3">Name</th>
          <th class="py-2.5 px-3 w-32">Type</th>
          <th class="py-2.5 px-3 w-16 text-center">LV</th>
          <th class="py-2.5 px-3 w-20 text-center">ATK</th>
          <th class="py-2.5 px-3 w-20 text-center">DEF</th>
          <th class="py-2.5 px-3 w-32">Rarity</th>
          <th class="py-2.5 px-3 w-28 text-center">Owned</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="card in cards"
          :key="card.card_id"
          @click="openDetail(card)"
          class="border-b border-gray-700/60 hover:bg-gray-700/50 cursor-pointer transition-colors even:bg-gray-800/40"
          :class="{
            'bg-gray-700/30': ui.sidebarCardId === card.card_id,
            'opacity-50': (getActiveVariant(card)?.owned_count ?? 0) === 0,
          }"
        >
          <td class="py-2.5 px-3 font-mono text-sm text-gray-300">{{ shortId(card.card_id) }}</td>
          <td class="py-2.5 px-3">
            <div class="flex items-center gap-2">
              <span
                v-if="card.is_legend"
                class="bg-amber-500 text-black text-[10px] font-bold px-1.5 py-0 rounded"
              >
                L
              </span>
              <span class="text-gray-100 font-medium">{{ card.name_zh || card.name_jp }}</span>
            </div>
          </td>
          <td class="py-2.5 px-3 text-sm text-gray-200">{{ card.card_type }}</td>
          <td class="py-2.5 px-3 text-sm text-gray-200 text-center">{{ card.level ?? '-' }}</td>
          <td class="py-2.5 px-3 text-sm text-gray-200 text-center font-medium">{{ card.atk ?? '-' }}</td>
          <td class="py-2.5 px-3 text-sm text-gray-200 text-center font-medium">{{ card.defense ?? '-' }}</td>
          <td class="py-2.5 px-3" @click.stop>
            <RarityTabs
              :variants="card.variants"
              :active-rarity="getActiveRarity(card)"
              @select="setActiveRarity(card.card_id, $event)"
            />
          </td>
          <td class="py-2.5 px-3" @click.stop>
            <div class="flex justify-center">
              <OwnershipControl
                :card-id="card.card_id"
                :rarity="getActiveRarity(card)"
                :owned-count="getActiveVariant(card)?.owned_count ?? 0"
                @update="(cid, r, cnt) => onOwnershipUpdate(cid, r, cnt, card)"
              />
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
