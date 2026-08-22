<script setup lang="ts">
/**
 * Modal (locks the background) for an in-effect card reference. Fetches every
 * card whose full name matches, lists them by card number on the left, and
 * shows the selected card's read-only info on the right.
 */
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import type { Card } from '@/types/card'
import { searchCardsByName } from '@/api/cards'
import CardBasicInfo from './CardBasicInfo.vue'

const visible = defineModel<boolean>('visible', { required: true })
const props = defineProps<{ name: string }>()

const cards = ref<Card[]>([])
const selected = ref<Card | null>(null)
const loading = ref(false)

watch([visible, () => props.name], async ([open]) => {
  if (!open || !props.name) return
  loading.value = true
  cards.value = []
  selected.value = null
  cards.value = await searchCardsByName(props.name)
  selected.value = cards.value[0] ?? null
  loading.value = false
})
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    dismissable-mask
    :header="`「${name}」`"
    :style="{ width: '48rem', maxWidth: '95vw' }"
    :content-style="{ minHeight: '20rem' }"
  >
    <div v-if="loading" class="flex items-center justify-center h-64 text-sm text-gray-400">載入中…</div>
    <div v-else-if="!cards.length" class="flex items-center justify-center h-64 text-sm text-gray-400">
      查無完全同名的卡片
    </div>
    <div v-else class="flex gap-4">
      <!-- left: card-number list -->
      <div class="w-32 shrink-0 space-y-1 border-r border-[rgba(201,168,76,0.12)] pr-3 max-h-[70vh] overflow-y-auto">
        <button
          v-for="c in cards"
          :key="c.card_id"
          @click="selected = c"
          class="w-full text-left font-mono text-[11px] rounded px-2 py-1.5 transition-colors truncate"
          :class="selected?.card_id === c.card_id
            ? 'bg-gold text-black font-bold'
            : 'text-gold hover:bg-[rgba(201,168,76,0.1)]'"
          :title="c.card_id"
        >{{ c.card_id.split('/').pop() }}</button>
      </div>

      <!-- right: selected card -->
      <div class="flex-1 min-w-0 max-h-[70vh] overflow-y-auto pr-1">
        <div v-if="selected" class="mb-2 flex justify-end">
          <a
            :href="`/set/${selected.set_id}`"
            target="_blank"
            rel="noopener"
            class="inline-flex items-center gap-1 text-[11px] font-orbitron text-gold hover:text-gold-light border border-[rgba(201,168,76,0.3)] hover:border-gold/50 rounded px-2 py-1 transition-colors"
            :title="`在新分頁開啟 ${selected.set_id} 卡組`"
          >
            前往 {{ selected.set_id }} 卡組
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14 5h5v5m0-5l-7 7M9 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-3" />
            </svg>
          </a>
        </div>
        <CardBasicInfo v-if="selected" :card="selected" />
      </div>
    </div>
  </Dialog>
</template>
