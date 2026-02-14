<script setup lang="ts">
export interface BreadcrumbItem {
  label: string
  to?: string
}

defineProps<{
  items: BreadcrumbItem[]
}>()
</script>

<template>
  <nav class="flex items-center gap-1.5 text-sm text-gray-400 mb-4 overflow-x-auto">
    <template v-for="(item, idx) in items" :key="idx">
      <span v-if="idx > 0" class="text-gray-600">/</span>
      <router-link
        v-if="item.to"
        :to="item.to"
        class="hover:text-yellow-400 transition-colors whitespace-nowrap"
      >
        {{ item.label }}
      </router-link>
      <span v-else class="text-gray-200 whitespace-nowrap">{{ item.label }}</span>
    </template>
  </nav>
</template>
