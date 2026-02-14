<script setup lang="ts">
import { onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useCardSetsStore } from '@/stores/cardSets'
import ProductTypeNav from '@/components/navigation/ProductTypeNav.vue'
import SetList from '@/components/navigation/SetList.vue'
import BreadcrumbBar from '@/components/layout/BreadcrumbBar.vue'
import type { BreadcrumbItem } from '@/components/layout/BreadcrumbBar.vue'

const route = useRoute()
const store = useCardSetsStore()

const currentProductType = computed(() =>
  (route.params.productType as string) || undefined
)

const breadcrumbs = computed<BreadcrumbItem[]>(() => {
  const items: BreadcrumbItem[] = [{ label: 'Home', to: '/' }]
  if (currentProductType.value) {
    const pt = store.productTypes.find(p => p.product_type === currentProductType.value)
    items.push({ label: pt?.display_name ?? currentProductType.value })
  }
  return items
})

onMounted(async () => {
  await store.loadProductTypes()
  await store.loadSets(currentProductType.value)
})

watch(currentProductType, async (pt) => {
  await store.loadSets(pt)
})
</script>

<template>
  <div>
    <BreadcrumbBar :items="breadcrumbs" />
    <ProductTypeNav :product-types="store.productTypes" />
    <SetList :sets="store.sets" :loading="store.loading" />
  </div>
</template>
