<script setup lang="ts">
import type { CardSet, OwnershipStats } from '@/types/cardSet'

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
    class="text-center py-12 text-gray-500"
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
    >
      <!-- Top row: set_id badge + date -->
      <div class="flex items-start justify-between gap-2 mb-2">
        <span class="text-[11px] font-orbitron text-gold/80 bg-[rgba(201,168,76,0.1)] px-1.5 py-0.5 rounded tracking-wide">
          {{ s.set_id }}
        </span>
        <span v-if="s.release_date" class="text-[11px] font-orbitron text-gray-500 shrink-0">
          {{ s.release_date }}
        </span>
      </div>

      <!-- Set name -->
      <h3 class="text-sm font-medium text-gray-100 group-hover:text-gold transition-colors leading-snug mb-0.5">
        {{ s.set_name_zh || s.set_name_jp }}
      </h3>
      <p v-if="s.set_name_zh && s.set_name_jp" class="text-xs text-gray-500 leading-snug">
        {{ s.set_name_jp }}
      </p>

      <!-- Spacer -->
      <div class="flex-1" />

      <!-- Bottom: progress or card count -->
      <template v-if="getStats(s.set_id)">
        <div class="mt-3">
          <!-- Stats row -->
          <div class="flex items-center justify-between text-[10px] mb-1.5">
            <span class="font-orbitron text-gray-500">
              {{ getStats(s.set_id)!.owned_variants }}
              <span class="opacity-60">/ {{ getStats(s.set_id)!.total_variants }}</span>
            </span>
            <span
              class="font-orbitron font-bold"
              :class="progressPct(getStats(s.set_id)) === 100 ? 'text-emerald-400' : 'text-gold-dim'"
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
        <div class="mt-3 flex items-center justify-between text-[11px] text-gray-500">
          <span class="font-orbitron">{{ s.total_cards }} <span class="opacity-70">cards</span></span>
          <span class="text-gold/40 group-hover:text-gold/70 transition-colors">→</span>
        </div>
      </template>
    </router-link>
  </div>
</template>
