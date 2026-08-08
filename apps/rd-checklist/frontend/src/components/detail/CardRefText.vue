<script setup lang="ts">
/**
 * Renders card text (effect / condition / …) and turns names wrapped in 「」/『』
 * into interactive references. Hovering a reference shows a floating read-only
 * preview of the matching card; clicking opens a modal that lists every card
 * sharing that exact name.
 */
import { ref, computed } from 'vue'
import type { Card } from '@/types/card'
import { searchCardsByName } from '@/api/cards'
import CardBasicInfo from './CardBasicInfo.vue'
import CardRefModal from './CardRefModal.vue'

const props = defineProps<{ text: string | null | undefined }>()

type Segment = { ref: boolean; value: string }

const segments = computed<Segment[]>(() => {
  const text = props.text ?? ''
  const re = /[「『]([^」』]+)[」』]/g
  const out: Segment[] = []
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push({ ref: false, value: text.slice(last, m.index) })
    out.push({ ref: true, value: m[1]! })
    last = m.index + m[0].length
  }
  if (last < text.length) out.push({ ref: false, value: text.slice(last) })
  return out
})

// ── Hover preview state ──
const previewVisible = ref(false)
const previewStyle = ref<Record<string, string>>({})
const hoverName = ref('')
const hoverCard = ref<Card | null>(null)
const hoverCount = ref(0)
const hoverLoading = ref(false)
let hideTimer: ReturnType<typeof setTimeout> | null = null
const cache = new Map<string, Card[]>()

function positionPreview(e: MouseEvent) {
  const pad = 12
  const w = 320
  const left = Math.min(e.clientX + pad, window.innerWidth - w - pad)
  const top = Math.min(e.clientY + pad, window.innerHeight - 200)
  previewStyle.value = { left: `${Math.max(pad, left)}px`, top: `${Math.max(pad, top)}px` }
}

async function onRefEnter(e: MouseEvent, name: string) {
  if (hideTimer) clearTimeout(hideTimer)
  hoverName.value = name
  positionPreview(e)
  previewVisible.value = true
  hoverLoading.value = true
  let list = cache.get(name)
  if (!list) {
    list = await searchCardsByName(name)
    cache.set(name, list)
  }
  if (hoverName.value !== name) return // moved to another ref meanwhile
  hoverCard.value = list[0] ?? null
  hoverCount.value = list.length
  hoverLoading.value = false
}

function scheduleHide() {
  if (hideTimer) clearTimeout(hideTimer)
  hideTimer = setTimeout(() => { previewVisible.value = false }, 160)
}

function cancelHide() {
  if (hideTimer) clearTimeout(hideTimer)
}

// ── Modal state ──
const modalVisible = ref(false)
const modalName = ref('')

function openModal(name: string) {
  modalName.value = name
  modalVisible.value = true
  previewVisible.value = false
}
</script>

<template>
  <span class="whitespace-pre-line">
    <template v-for="(seg, i) in segments" :key="i">
      <span
        v-if="seg.ref"
        class="ref-name"
        @mouseenter="onRefEnter($event, seg.value)"
        @mouseleave="scheduleHide"
        @click="openModal(seg.value)"
      >「{{ seg.value }}」</span>
      <template v-else>{{ seg.value }}</template>
    </template>
  </span>

  <Teleport to="body">
    <div
      v-if="previewVisible"
      class="ref-preview"
      :style="previewStyle"
      @mouseenter="cancelHide"
      @mouseleave="scheduleHide"
    >
      <div v-if="hoverLoading" class="text-xs text-gray-500 py-6 text-center">載入中…</div>
      <template v-else-if="hoverCard">
        <CardBasicInfo :card="hoverCard" compact />
        <button class="ref-more" @click="openModal(hoverName)">
          更多<span v-if="hoverCount > 1"> ({{ hoverCount }})</span> ›
        </button>
      </template>
      <div v-else class="text-xs text-gray-500 py-6 text-center">查無「{{ hoverName }}」</div>
    </div>
  </Teleport>

  <CardRefModal v-model:visible="modalVisible" :name="modalName" />
</template>

<style scoped>
.ref-name {
  color: var(--p-primary-color, #eac96a);
  cursor: pointer;
  text-decoration: underline dotted;
  text-underline-offset: 2px;
}
.ref-name:hover {
  color: #fff;
  background: rgba(201, 168, 76, 0.14);
  border-radius: 2px;
}
.ref-preview {
  position: fixed;
  z-index: 1200;
  width: 20rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(201, 168, 76, 0.28);
  background: #14141a;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55);
}
.ref-more {
  margin-top: 0.6rem;
  width: 100%;
  text-align: center;
  font-size: 11px;
  color: var(--p-primary-color, #eac96a);
  padding: 0.3rem;
  border-top: 1px solid rgba(201, 168, 76, 0.12);
}
.ref-more:hover {
  color: #fff;
}
</style>
