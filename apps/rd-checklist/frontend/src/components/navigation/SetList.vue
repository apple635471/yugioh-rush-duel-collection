<script setup lang="ts">
import { ref } from 'vue'
import type { CardSet, OwnershipStats } from '@/types/cardSet'
import { fetchSetImages, getSetImageUrl, type CardSetImage } from '@/api/cardSets'

const props = defineProps<{
  sets: CardSet[]
  loading: boolean
  setStats?: Record<string, OwnershipStats>
}>()

function getStats(setId: string) {
  return props.setStats?.[setId] ?? null
}

function progressPct(stats: OwnershipStats | null) {
  if (!stats || stats.total_variants === 0) return 0
  return Math.round(stats.owned_variants / stats.total_variants * 100)
}

/* ── hover 時顯示卡組圖片 ──────────────────────────────────
   浮動視窗掛在 body（卡片本身 overflow-hidden，放在裡面會被裁掉）。
   每個卡組只查一次就記在 cache；沒有圖的卡組不彈視窗——就是空白。 */
const imageCache = new Map<string, CardSetImage[]>()
const hoverImages = ref<CardSetImage[]>([])
const hoverStyle = ref<Record<string, string>>({})
const hoverVisible = ref(false)
let hoverSetId = ''
let enterTimer: ReturnType<typeof setTimeout> | null = null

function position(e: MouseEvent) {
  const pad = 12
  const w = 260
  const h = 150
  hoverStyle.value = {
    left: `${Math.max(pad, Math.min(e.clientX + pad, window.innerWidth - w - pad))}px`,
    top: `${Math.max(pad, Math.min(e.clientY + pad, window.innerHeight - h - pad))}px`,
  }
}

function onEnter(e: MouseEvent, setId: string) {
  hoverSetId = setId
  position(e)
  // 滑過一整排時不要每張都打一次 API
  if (enterTimer) clearTimeout(enterTimer)
  enterTimer = setTimeout(() => show(setId), 120)
}

async function show(setId: string) {
  let images = imageCache.get(setId)
  if (!images) {
    try {
      images = await fetchSetImages(setId)
    } catch {
      images = []
    }
    imageCache.set(setId, images)
  }
  if (hoverSetId !== setId) return // 已經移到別的卡組
  hoverImages.value = images
  hoverVisible.value = images.length > 0
}

function onLeave() {
  hoverSetId = ''
  hoverVisible.value = false
  if (enterTimer) clearTimeout(enterTimer)
}
</script>

<template>
  <!-- Loading skeleton -->
  <div v-if="loading" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
    <div
      v-for="i in 8"
      :key="i"
      class="h-28 bg-surface rounded-lg animate-pulse border border-[rgba(201,168,76,0.08)]"
    />
  </div>

  <!-- Empty state -->
  <div
    v-else-if="sets.length === 0"
    class="text-center py-12 text-gray-400"
  >
    No card sets found.
  </div>

  <!-- Set cards -->
  <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
    <router-link
      v-for="s in sets"
      :key="s.set_id"
      :to="`/set/${s.set_id}`"
      class="group bg-surface border border-[rgba(201,168,76,0.14)] rounded-lg p-4 overflow-hidden
             hover:border-gold/40 hover:bg-dark-4 hover:-translate-y-0.5 hover:shadow-lg
             transition-all duration-200 flex flex-col"
      @mouseenter="onEnter($event, s.set_id)"
      @mousemove="position"
      @mouseleave="onLeave"
    >
      <!-- Top row: set_id badge + date -->
      <div class="flex items-start justify-between gap-2 mb-2">
        <span class="text-[11px] font-orbitron text-gold/80 bg-[rgba(201,168,76,0.1)] px-1.5 py-0.5 rounded tracking-wide">
          {{ s.set_id }}
        </span>
        <span v-if="s.release_date" class="text-[11px] font-orbitron text-gray-400 shrink-0">
          {{ s.release_date }}
        </span>
      </div>

      <!-- Set name -->
      <h3 class="text-sm font-medium text-gray-100 group-hover:text-gold transition-colors leading-snug mb-0.5">
        {{ s.set_name_zh || s.set_name_jp }}
      </h3>
      <p v-if="s.set_name_zh && s.set_name_jp" class="text-xs text-gray-400 leading-snug">
        {{ s.set_name_jp }}
      </p>

      <!-- Spacer -->
      <div class="flex-1" />

      <!-- Bottom: progress or card count -->
      <template v-if="getStats(s.set_id)">
        <div class="mt-3">
          <!-- Stats row -->
          <div class="flex items-center justify-between text-[10px] mb-1.5">
            <span class="font-orbitron text-gray-400">
              {{ getStats(s.set_id)!.owned_variants }}
              <span class="opacity-60">/ {{ getStats(s.set_id)!.total_variants }}</span>
            </span>
            <span
              class="font-orbitron font-bold"
              :class="progressPct(getStats(s.set_id)) === 100 ? 'text-emerald-400' : 'text-gold'"
            >
              {{ progressPct(getStats(s.set_id)) }}%
            </span>
          </div>
          <!-- Progress bar -->
          <div class="h-[3px] w-full rounded-full bg-[rgba(201,168,76,0.1)] overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="progressPct(getStats(s.set_id)) === 100
                ? 'bg-emerald-500'
                : 'bg-gradient-to-r from-[#C9A84C] to-[#EAC96A]'"
              :style="{ width: `${progressPct(getStats(s.set_id))}%` }"
            />
          </div>
        </div>
      </template>
      <template v-else>
        <div class="mt-3 flex items-center justify-between text-[11px] text-gray-400">
          <span class="font-orbitron">{{ s.total_cards }} <span class="opacity-70">cards</span></span>
          <span class="text-gold/40 group-hover:text-gold/70 transition-colors">→</span>
        </div>
      </template>
    </router-link>
  </div>

  <!-- 卡組圖片的 hover 預覽：固定高度，圖多就橫向捲動 -->
  <Teleport to="body">
    <div
      v-if="hoverVisible"
      class="fixed z-[70] pointer-events-none flex h-[150px] max-w-[260px] gap-2 overflow-hidden
             rounded-lg border border-[rgba(201,168,76,0.25)] bg-dark-1/95 p-2 shadow-2xl"
      :style="hoverStyle"
    >
      <img
        v-for="img in hoverImages"
        :key="img.id"
        :src="getSetImageUrl(img.id)"
        :alt="img.title"
        class="h-full w-auto rounded object-contain"
      />
    </div>
  </Teleport>
</template>
