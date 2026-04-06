<script setup lang="ts">
import { ref } from 'vue'
import type { Card } from '@/types/card'
import { variantKey } from '@/types/card'
import { updateOwnership } from '@/api/cards'
import { useUiStore } from '@/stores/ui'
import { pickDefaultVariantKey } from '@/constants/rarities'
import OwnershipBadge from './OwnershipBadge.vue'
import RarityTabs from './RarityTabs.vue'
import OwnershipControl from './OwnershipControl.vue'

const props = defineProps<{
  cards: Card[]
  preferredRarity?: string
}>()

const emit = defineEmits<{
  ownershipChanged: []
}>()

const ui = useUiStore()

// Track active rarity per card
const activeRarities = ref<Record<string, string>>({})

function getActiveRarity(card: Card): string {
  return activeRarities.value[card.card_id] ?? pickDefaultVariantKey(card.variants, props.preferredRarity)
}

function setActiveRarity(cardId: string, rarity: string) {
  activeRarities.value[cardId] = rarity
  // Sync to sidebar if this card is currently open
  if (ui.sidebarCardId === cardId) ui.sidebarRarity = rarity
}

function getActiveVariant(card: Card) {
  const key = getActiveRarity(card)
  return card.variants.find(v => variantKey(v) === key) ?? card.variants[0]
}

function openDetail(card: Card) {
  ui.openSidebar(card.card_id, getActiveRarity(card))
}

function shortId(cardId: string): string {
  const parts = cardId.split('-')
  return parts.length > 1 ? (parts[parts.length - 1] ?? cardId) : cardId
}

async function onOwnershipUpdate(cardId: string, rarityKey: string, count: number, card: Card) {
  await updateOwnership(cardId, rarityKey, count)
  const v = card.variants.find(v => v.card_id === cardId && variantKey(v) === rarityKey)
  if (v) v.owned_count = count
  emit('ownershipChanged')
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full text-base">
      <thead>
        <tr class="border-b border-[rgba(201,168,76,0.2)] text-left text-xs text-gold/60 uppercase tracking-widest font-orbitron">
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
          class="border-b border-[rgba(201,168,76,0.07)] hover:bg-gold/5 cursor-pointer transition-colors even:bg-dark-2/40"
          :class="{
            'bg-gold/8': ui.sidebarCardId === card.card_id,
            'opacity-50': (getActiveVariant(card)?.owned_count ?? 0) === 0,
          }"
        >
          <td class="py-2.5 px-3 font-orbitron text-xs text-gold/60">{{ shortId(card.card_id) }}</td>
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
