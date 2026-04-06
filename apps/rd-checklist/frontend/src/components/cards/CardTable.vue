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

function collectionStatus(card: Card) {
  const total = card.variants.length
  const owned = card.variants.filter(v => v.owned_count >= 1).length
  return { owned, total }
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
          <th class="py-2.5 px-3 w-40">Name</th>
          <th class="py-2.5 px-3 w-32">Type</th>
          <th class="py-2.5 px-3 w-16 text-center">LV</th>
          <th class="py-2.5 px-3 w-20 text-center">ATK</th>
          <th class="py-2.5 px-3 w-20 text-center">DEF</th>
          <th class="py-2.5 px-3 w-32">Rarity</th>
          <th class="py-2.5 px-3 w-28 text-center">Owned</th>
          <th class="py-2.5 px-3 w-10 text-center"></th>
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
          <td class="py-2.5 px-3 w-40 max-w-[10rem]">
            <div class="flex items-center gap-2 min-w-0">
              <span
                v-if="card.is_legend"
                class="shrink-0 bg-amber-500 text-black text-[10px] font-bold px-1.5 py-0 rounded"
              >
                L
              </span>
              <span class="text-gray-100 font-medium truncate">{{ card.name_zh || card.name_jp }}</span>
            </div>
          </td>
          <td class="py-2.5 px-3 text-sm text-gray-200">{{ card.card_type }}</td>
          <td class="py-2.5 px-3 text-sm text-gray-200 text-center">{{ card.level ?? '-' }}</td>
          <td class="py-2.5 px-3 text-sm text-gray-200 text-center font-medium">{{ card.atk ?? '-' }}</td>
          <td class="py-2.5 px-3 text-sm text-gray-200 text-center font-medium">{{ card.defense ?? '-' }}</td>
          <td class="py-2.5 px-3 w-36" @click.stop>
            <!-- flex wrapper 提供 flex context，讓 RarityTabs 內的 flex-1 能正確量測寬度 -->
            <div class="flex min-w-0 max-w-[9rem]">
              <RarityTabs
                :variants="card.variants"
                :active-rarity="getActiveRarity(card)"
                align="start"
                @select="setActiveRarity(card.card_id, $event)"
              />
            </div>
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
          <td class="py-2.5 px-3 text-center">
            <!-- 全收：綠色 ✓ -->
            <svg
              v-if="collectionStatus(card).owned === collectionStatus(card).total && collectionStatus(card).total > 0"
              class="w-4 h-4 text-emerald-400 inline-block"
              viewBox="0 0 20 20" fill="currentColor" title="全部稀有度已收集"
            >
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clip-rule="evenodd" />
            </svg>
            <!-- 部分收：黃色 X/N -->
            <span
              v-else-if="collectionStatus(card).owned > 0"
              class="text-xs font-bold text-amber-400"
              :title="`已收集 ${collectionStatus(card).owned}/${collectionStatus(card).total} 種稀有度`"
            >{{ collectionStatus(card).owned }}/{{ collectionStatus(card).total }}</span>
            <!-- 全無：紅色 0/N -->
            <span
              v-else-if="collectionStatus(card).total > 0"
              class="text-xs font-bold text-rose-500"
              :title="`尚未收集任何稀有度（共 ${collectionStatus(card).total} 種）`"
            >0/{{ collectionStatus(card).total }}</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
