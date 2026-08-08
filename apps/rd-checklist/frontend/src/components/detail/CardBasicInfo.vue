<script setup lang="ts">
/**
 * Read-only summary of a card: image + names + id + type/stats + text sections.
 * Used by the in-effect card-reference hover preview and its "更多" modal.
 * Effect texts are rendered as plain text here (no nested reference hovering).
 */
import { computed } from 'vue'
import type { Card } from '@/types/card'
import { getCardImageUrl } from '@/api/cards'
import { pickDefaultVariantKey } from '@/constants/rarities'

const props = defineProps<{ card: Card; compact?: boolean }>()

const isMonster = computed(() => props.card.card_type.includes('怪獸'))
const isMaximum = computed(() => props.card.card_type.includes('巨極'))

const imageKey = computed(() => pickDefaultVariantKey(props.card.variants))
const imageUrl = computed(() =>
  imageKey.value ? getCardImageUrl(props.card.card_id, imageKey.value) : '',
)

const textSections = [
  { key: 'summon_condition', label: '召喚條件' },
  { key: 'condition', label: '條件' },
  { key: 'effect', label: '效果' },
  { key: 'continuous_effect', label: '永續效果' },
  { key: 'description', label: '描述' },
] as const
</script>

<template>
  <div>
    <div class="flex gap-3">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="card.name_zh || card.name_jp"
        class="w-24 shrink-0 self-start rounded border border-[rgba(201,168,76,0.2)] bg-dark-3 object-cover"
        loading="lazy"
      />
      <div class="min-w-0 flex-1">
        <div class="font-mono text-[10px] text-gold/70 tracking-wide">{{ card.card_id }}</div>
        <h4 class="font-cinzel text-base font-bold text-gray-100 leading-snug mt-0.5 break-words">
          {{ card.name_zh || card.name_jp }}
        </h4>
        <p v-if="card.name_zh && card.name_jp" class="text-[11px] text-gray-500 break-words leading-snug">
          {{ card.name_jp }}
        </p>

        <div class="mt-2 flex flex-wrap gap-1.5 text-[11px]">
          <span class="rounded bg-[rgba(201,168,76,0.1)] px-1.5 py-0.5 text-gold-dim">{{ card.card_type }}</span>
          <span v-if="isMonster && card.attribute" class="rounded bg-[rgba(255,255,255,0.06)] px-1.5 py-0.5 text-gray-300">{{ card.attribute }}</span>
          <span v-if="isMonster && card.monster_type" class="rounded bg-[rgba(255,255,255,0.06)] px-1.5 py-0.5 text-gray-300">{{ card.monster_type }}</span>
          <span v-if="isMonster && card.level != null" class="rounded bg-[rgba(255,255,255,0.06)] px-1.5 py-0.5 text-gray-300">Lv.{{ card.level }}</span>
        </div>

        <div v-if="isMonster" class="mt-1.5 flex gap-3 text-xs font-orbitron">
          <span class="text-[#f87171]">ATK {{ card.atk ?? '?' }}</span>
          <span class="text-[#60a5fa]">DEF {{ card.defense ?? '?' }}</span>
          <span v-if="isMaximum && card.maximum_atk != null" class="text-gold">MAX {{ card.maximum_atk }}</span>
        </div>
      </div>
    </div>

    <div v-if="!compact" class="mt-3 space-y-2">
      <div v-for="s in textSections" :key="s.key" v-show="(card as any)[s.key]">
        <div class="font-orbitron text-[9px] font-bold tracking-[0.2em] text-gold-dim uppercase mb-1">{{ s.label }}</div>
        <p class="text-xs text-gray-300 leading-relaxed whitespace-pre-line bg-[rgba(201,168,76,0.03)] border border-[rgba(201,168,76,0.08)] rounded px-2.5 py-1.5">{{ (card as any)[s.key] }}</p>
      </div>
    </div>
  </div>
</template>
