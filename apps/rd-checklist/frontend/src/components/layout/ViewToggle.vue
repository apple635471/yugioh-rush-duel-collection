<script setup lang="ts">
import { computed } from 'vue'
import { useUiStore } from '@/stores/ui'
import SelectButton from 'primevue/selectbutton'

const ui = useUiStore()

const viewMode = computed({
  get: () => ui.viewMode,
  set: (v: 'grid' | 'table') => { ui.viewMode = v },
})

const viewOptions = [
  { value: 'grid' },
  { value: 'table' },
]
</script>

<template>
  <SelectButton v-model="viewMode" :options="viewOptions" option-value="value">
    <template #option="{ option }">
      <!-- Grid icon -->
      <svg v-if="option.value === 'grid'" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
      <!-- Table icon -->
      <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
      </svg>
    </template>
  </SelectButton>
</template>
