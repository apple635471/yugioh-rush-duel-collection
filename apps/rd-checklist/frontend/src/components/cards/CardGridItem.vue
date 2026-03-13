<script setup lang="ts">
import { ref, computed, watch } from 'vue'
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
const cardEl = ref<HTMLElement | null>(null)
const copied = ref(false)

const activeVariant = computed(() =>
  props.card.variants.find(v => v.rarity === activeRarity.value) ?? props.card.variants[0]
)

const imageUrl = computed(() => {
  if (!activeVariant.value) return ''
  const base = getCardImageUrl(props.card.card_id, activeVariant.value.rarity)
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

async function onOwnershipUpdate(cardId: string, rarity: string, count: number) {
  await updateOwnership(cardId, rarity, count)
  const v = props.card.variants.find(v => v.card_id === cardId && v.rarity === rarity)
  if (v) v.owned_count = count
  emit('ownershipChanged')
}
</script>

<template>
  <div
    ref="cardEl"
    @click="openDetail"
    class="group relative bg-gray-800 border rounded-lg overflow-hidden cursor-pointer transition-all"
    :class="isSelected
      ? 'border-yellow-400 ring-2 ring-yellow-400 ring-offset-2 ring-offset-gray-900'
      : 'border-gray-700 hover:border-yellow-500/50'"
  >
    <!-- Card number row (above image) -->
    <div class="flex items-center gap-1 px-2 pt-1.5 pb-1">
      <span class="font-mono text-[11px] text-gray-200 truncate flex-1 leading-none">{{ fullCardId }}</span>
      <button
        @click="copyCardNumber"
        class="shrink-0 text-gray-600 hover:text-gray-300 transition-colors"
        :title="copied ? '已複製！' : '複製編號'"
      >
        <svg v-if="copied" class="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
        </svg>
      </button>
    </div>

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

    <!-- Info (below image) -->
    <div class="px-2 pt-1.5 pb-2">
      <!-- Card name -->
      <h4 class="text-sm font-medium text-gray-100 leading-snug line-clamp-2 group-hover:text-yellow-400 transition-colors">
        {{ card.name_zh || card.name_jp }}
      </h4>

      <!-- Card type -->
      <p class="text-[9px] text-gray-500 mt-0.5 leading-none">{{ card.card_type }}</p>

      <!-- Rarity — own line, right-aligned, click.stop so it doesn't open sidebar -->
      <div class="flex justify-end mt-1" @click.stop>
        <RarityTabs
          :variants="card.variants"
          :active-rarity="activeRarity"
          @select="activeRarity = $event"
        />
      </div>

      <!-- Ownership control -->
      <div class="mt-1 flex justify-center">
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
