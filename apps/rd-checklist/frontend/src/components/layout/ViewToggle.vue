<script setup lang="ts">
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
</script>

<template>
  <div class="flex items-center bg-gray-700 rounded-lg p-0.5">
    <button
      @click="ui.viewMode = 'grid'"
      class="px-3 py-1 text-sm rounded-md transition-colors"
      :class="ui.viewMode === 'grid'
        ? 'bg-gray-600 text-yellow-400'
        : 'text-gray-300 hover:text-gray-100'"
    >
      <!-- Grid icon -->
      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
    </button>
    <button
      @click="ui.viewMode = 'table'"
      class="px-3 py-1 text-sm rounded-md transition-colors"
      :class="ui.viewMode === 'table'
        ? 'bg-gray-600 text-yellow-400'
        : 'text-gray-300 hover:text-gray-100'"
    >
      <!-- Table icon -->
      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
      </svg>
    </button>
  </div>
</template>
