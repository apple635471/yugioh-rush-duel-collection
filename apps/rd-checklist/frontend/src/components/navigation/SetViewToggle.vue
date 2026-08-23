<script setup lang="ts">
import { computed } from 'vue'
import { useUiStore } from '@/stores/ui'
import SelectButton from 'primevue/selectbutton'

const ui = useUiStore()

const mode = computed({
  get: () => ui.setViewMode,
  set: (v: 'card' | 'timeline') => { ui.setViewMode = v },
})

const options = [
  { value: 'card', title: '卡片牆' },
  { value: 'timeline', title: '時間軸' },
]
</script>

<template>
  <SelectButton
    v-model="mode"
    :options="options"
    option-value="value"
    :allow-empty="false"
    class="app-toolbar-toggle"
  >
    <template #option="{ option }">
      <span :title="option.title" class="flex items-center">
        <!-- Card wall icon -->
        <svg v-if="option.value === 'card'" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
        <!-- Timeline icon: a vertical axis with nodes on both sides -->
        <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 20 20" stroke="currentColor" stroke-width="1.6">
          <path stroke-linecap="round" d="M10 2.5v15" />
          <circle cx="10" cy="6" r="1.6" fill="currentColor" stroke="none" />
          <circle cx="10" cy="14" r="1.6" fill="currentColor" stroke="none" />
          <path stroke-linecap="round" d="M8.4 6H3.5M11.6 14h4.9" />
        </svg>
      </span>
    </template>
  </SelectButton>
</template>
