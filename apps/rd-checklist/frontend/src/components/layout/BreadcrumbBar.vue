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
  <nav class="flex items-center gap-1.5 text-sm text-gray-500 mb-4 overflow-x-auto">
    <template v-for="(item, idx) in items" :key="idx">
      <span v-if="idx > 0" class="text-[rgba(201,168,76,0.3)]">/</span>
      <router-link
        v-if="item.to"
        :to="item.to"
        class="hover:text-gold transition-colors whitespace-nowrap"
      >
        {{ item.label }}
      </router-link>
      <span v-else class="text-gray-300 whitespace-nowrap">{{ item.label }}</span>
    </template>
  </nav>
</template>
