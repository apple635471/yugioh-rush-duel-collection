<script setup lang="ts">
import type { CardSet } from '@/types/cardSet'

defineProps<{
  sets: CardSet[]
  loading: boolean
}>()
</script>

<template>
  <!-- Loading skeleton -->
  <div v-if="loading" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
    <div
      v-for="i in 6"
      :key="i"
      class="h-24 bg-gray-800 rounded-lg animate-pulse"
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
  <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
    <router-link
      v-for="s in sets"
      :key="s.set_id"
      :to="`/set/${s.set_id}`"
      class="group bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-yellow-500/50 hover:bg-gray-800/50 transition-all"
    >
      <div class="flex items-start justify-between gap-2 mb-2">
        <span class="text-xs font-mono text-yellow-400/80 bg-yellow-400/10 px-1.5 py-0.5 rounded">
          {{ s.set_id }}
        </span>
        <span v-if="s.release_date" class="text-xs text-gray-500">
          {{ s.release_date }}
        </span>
      </div>
      <h3 class="text-sm font-medium text-gray-100 group-hover:text-yellow-400 transition-colors leading-snug mb-0.5">
        {{ s.set_name_zh || s.set_name_jp }}
      </h3>
      <p v-if="s.set_name_zh && s.set_name_jp" class="text-xs text-gray-500 leading-snug">
        {{ s.set_name_jp }}
      </p>
      <div class="mt-2 flex items-center gap-3 text-xs text-gray-500">
        <span>{{ s.total_cards }} cards</span>
      </div>
    </router-link>
  </div>
</template>
