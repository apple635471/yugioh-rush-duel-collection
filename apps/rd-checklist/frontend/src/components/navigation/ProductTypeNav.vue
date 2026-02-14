<script setup lang="ts">
import { useRoute } from 'vue-router'
import type { ProductType } from '@/types/cardSet'

const route = useRoute()

defineProps<{
  productTypes: ProductType[]
}>()

function isActive(pt: ProductType): boolean {
  return route.params.productType === pt.product_type
}
</script>

<template>
  <div class="flex flex-wrap gap-2 mb-6">
    <router-link
      to="/"
      class="px-3 py-1.5 text-sm rounded-full border transition-colors"
      :class="!route.params.productType
        ? 'border-yellow-500 bg-yellow-500/10 text-yellow-400'
        : 'border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200'"
    >
      All
    </router-link>
    <router-link
      v-for="pt in productTypes"
      :key="pt.product_type"
      :to="`/sets/${pt.product_type}`"
      class="px-3 py-1.5 text-sm rounded-full border transition-colors"
      :class="isActive(pt)
        ? 'border-yellow-500 bg-yellow-500/10 text-yellow-400'
        : 'border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200'"
    >
      {{ pt.display_name }}
      <span class="ml-1 text-xs opacity-60">({{ pt.set_count }})</span>
    </router-link>
  </div>
</template>
