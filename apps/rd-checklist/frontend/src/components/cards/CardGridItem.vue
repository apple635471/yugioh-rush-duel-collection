<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Card } from '@/types/card'
import { variantKey } from '@/types/card'
import { getCardImageUrl, updateOwnership } from '@/api/cards'
import { useUiStore } from '@/stores/ui'
import { pickDefaultVariantKey } from '@/constants/rarities'

import OwnershipBadge from './OwnershipBadge.vue'
import RarityTabs from './RarityTabs.vue'
import OwnershipControl from './OwnershipControl.vue'
import Button from 'primevue/button'

const props = defineProps<{
  card: Card
  preferredRarity?: string
}>()

const emit = defineEmits<{
  ownershipChanged: []
}>()

const ui = useUiStore()
const activeRarity = ref(pickDefaultVariantKey(props.card.variants, props.preferredRarity))
const cardEl = ref<HTMLElement | null>(null)
const copied = ref(false)

const activeVariant = computed(() =>
  props.card.variants.find(v => variantKey(v) === activeRarity.value) ?? props.card.variants[0]
)

const imageUrl = computed(() => {
  if (!activeVariant.value) return ''
  const key = variantKey(activeVariant.value)
  const base = getCardImageUrl(props.card.card_id, key)
  const buster = ui.imageUpdates.get(`${props.card.card_id}/${key}`)
  if (buster) return `${base}?t=${buster}`
  return activeVariant.value.image_source === 'user_upload' ? `${base}?t=1` : base
})

// card_id 有兩種格式：部分 set 已含完整路徑（如 RD/23PR-JP001），部分只有短形式（如 JP001）
// 前者直接用，後者補 RD/{set_id}-
const fullCardId = computed(() => {
  const id = props.card.card_id
  return id.includes('/') ? id : `RD/${props.card.set_id}-${id}`
})

const isOwned = computed(() => (activeVariant.value?.owned_count ?? 0) > 0)
const isSelected = computed(() => ui.sidebarCardId === props.card.card_id)

// Sidebar → Grid: sync rarity when sidebar switches rarity for this card
watch(() => ui.sidebarRarity, (r) => {
  if (isSelected.value && r) activeRarity.value = r
})

// Grid → Sidebar: sync rarity when user clicks a rarity tab while sidebar is open for this card
watch(activeRarity, (r) => {
  if (isSelected.value) ui.sidebarRarity = r
})

// Scroll selected card into view after the 500ms padding transition settles
watch(isSelected, (selected) => {
  if (selected && cardEl.value) {
    setTimeout(() => {
      cardEl.value?.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' })
    }, 520)
  }
})

function openDetail() {
  ui.openSidebar(props.card.card_id, activeRarity.value)
}

async function copyCardNumber(e: Event) {
  e.stopPropagation()
  await navigator.clipboard.writeText(fullCardId.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
}

async function onOwnershipUpdate(cardId: string, rarityKey: string, count: number) {
  await updateOwnership(cardId, rarityKey, count)
  const v = props.card.variants.find(v => v.card_id === cardId && variantKey(v) === rarityKey)
  if (v) v.owned_count = count
  emit('ownershipChanged')
}
</script>

<template>
  <div
    ref="cardEl"
    @click="openDetail"
    class="group relative bg-surface border rounded-lg overflow-hidden cursor-pointer transition-all duration-200"
    :class="isSelected
      ? 'border-gold ring-2 ring-gold/50 ring-offset-2 ring-offset-dark-bg'
      : 'border-[rgba(201,168,76,0.18)] hover:border-gold/45 hover:-translate-y-1 hover:scale-[1.02] hover:shadow-xl hover:shadow-black/40'"
  >
    <!-- Card number row (above image) -->
    <div class="flex items-center gap-1 px-2 pt-1.5 pb-1">
      <span class="font-orbitron text-[10px] text-gold/70 truncate flex-1 leading-none tracking-wide">{{ fullCardId }}</span>
      <Button
        @click="copyCardNumber"
        variant="text"
        severity="secondary"
        size="small"
        class="shrink-0 p-0"
        :title="copied ? '已複製！' : '複製編號'"
      >
        <svg v-if="copied" class="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
        </svg>
      </Button>
    </div>

    <!-- Image -->
    <div class="aspect-[59/86] bg-dark-3 relative overflow-hidden">
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

    <!-- Info (below image) -->
    <div class="px-2 pt-1.5 pb-2">
      <!-- Card name -->
      <h4 class="text-base font-medium text-gray-100 leading-snug line-clamp-2 group-hover:text-gold transition-colors">
        {{ card.name_zh || card.name_jp }}
      </h4>

      <!-- Card type -->
      <p class="text-xs text-gray-400 mt-0.5 leading-none">{{ card.card_type }}</p>

      <!-- Rarity — own line, click.stop so it doesn't open sidebar -->
      <div class="flex justify-end mt-2" @click.stop>
        <RarityTabs
          :variants="card.variants"
          :active-rarity="activeRarity"
          @select="activeRarity = $event"
        />
      </div>
    </div>

    <!-- Ownership control — separated footer -->
    <div
      class="px-2 py-2 flex justify-center border-t border-white/[0.06] bg-black/20"
      @click.stop
    >
      <OwnershipControl
        :card-id="card.card_id"
        :rarity="activeRarity"
        :owned-count="activeVariant?.owned_count ?? 0"
        @update="onOwnershipUpdate"
      />
    </div>
  </div>
</template>
