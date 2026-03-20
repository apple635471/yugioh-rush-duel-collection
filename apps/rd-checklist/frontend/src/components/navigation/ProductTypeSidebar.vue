<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import type { ProductType } from '@/types/cardSet'
import Button from 'primevue/button'

const route = useRoute()
const collapsed = ref(false)

defineProps<{
  productTypes: ProductType[]
}>()

// Group product types into sections by display_name keywords
const sections = computed(() => {
  // Keep ordering consistent with how backend returns them
  return [
    {
      label: '補充包系列',
      test: (name: string) => /booster|advanced|maximum|over rush|go rush/i.test(name),
    },
    {
      label: '構築 / 預組',
      test: (name: string) => /starter|structure|character|預組|deck/i.test(name),
    },
    {
      label: '活動 / 限定',
      test: (name: string) => /battle|tournament|legend|extra/i.test(name),
    },
  ]
})

function getSection(displayName: string): string {
  for (const s of sections.value) {
    if (s.test(displayName)) return s.label
  }
  return '其他'
}

function getSectionTypes(label: string, productTypes: ProductType[]) {
  return productTypes.filter(pt => getSection(pt.display_name) === label)
}

const allSectionLabels = computed(() => {
  const s = ['總覽', ...sections.value.map(s => s.label), '其他']
  return s
})

function isActive(pt: ProductType): boolean {
  return route.params.productType === pt.product_type
}
</script>

<template>
  <!-- Collapsed: narrow strip with expand button -->
  <div
    v-if="collapsed"
    class="shrink-0 flex flex-col items-center pt-3 gap-2"
    style="width: 36px"
  >
    <Button
      @click="collapsed = false"
      variant="text"
      severity="secondary"
      size="small"
      class="p-1 text-gold/60 hover:text-gold"
      title="展開側欄"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </Button>
  </div>

  <!-- Expanded sidebar -->
  <aside
    v-else
    class="shrink-0 sticky top-[56px] self-start h-[calc(100vh-56px)] overflow-y-auto overflow-x-hidden"
    style="width: 200px"
  >
    <!-- Header row with collapse button -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-[rgba(201,168,76,0.1)]">
      <span class="font-orbitron text-[9px] font-bold tracking-[0.22em] text-gold-dim uppercase">
        Browse
      </span>
      <Button
        @click="collapsed = true"
        variant="text"
        severity="secondary"
        size="small"
        class="p-1 text-gold/40 hover:text-gold"
        title="收合側欄"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </Button>
    </div>

    <!-- All section -->
    <div class="py-2">
      <router-link
        to="/"
        class="flex items-center justify-between px-4 py-1.5 text-xs border-l-2 transition-all"
        :class="!route.params.productType
          ? 'border-l-gold text-gold-light bg-[rgba(201,168,76,0.08)] font-medium'
          : 'border-l-transparent text-gray-500 hover:text-gray-200 hover:bg-[rgba(201,168,76,0.04)]'"
      >
        <span>全部</span>
        <span
          class="font-orbitron text-[9px] px-1 py-0.5 rounded"
          :class="!route.params.productType
            ? 'text-gold-dim bg-[rgba(201,168,76,0.15)]'
            : 'text-gray-600 bg-dark-3'"
        >
          {{ productTypes.reduce((sum, pt) => sum + pt.set_count, 0) }}
        </span>
      </router-link>
    </div>

    <!-- Grouped sections -->
    <template v-for="section in sections" :key="section.label">
      <template v-if="getSectionTypes(section.label, productTypes).length > 0">
        <div class="h-px bg-[rgba(201,168,76,0.08)] mx-4 my-1" />
        <div class="pt-2 pb-1">
          <div class="font-orbitron text-[9px] font-bold tracking-[0.22em] text-gold-dim uppercase px-4 mb-1">
            {{ section.label }}
          </div>
          <router-link
            v-for="pt in getSectionTypes(section.label, productTypes)"
            :key="pt.product_type"
            :to="`/sets/${pt.product_type}`"
            class="flex items-center justify-between px-4 py-1.5 text-xs border-l-2 transition-all"
            :class="isActive(pt)
              ? 'border-l-gold text-gold-light bg-[rgba(201,168,76,0.08)] font-medium'
              : 'border-l-transparent text-gray-500 hover:text-gray-200 hover:bg-[rgba(201,168,76,0.04)]'"
          >
            <span class="leading-snug">{{ pt.display_name }}</span>
            <span
              class="font-orbitron text-[9px] px-1 py-0.5 rounded shrink-0 ml-1"
              :class="isActive(pt)
                ? 'text-gold-dim bg-[rgba(201,168,76,0.15)]'
                : 'text-gray-600 bg-dark-3'"
            >
              {{ pt.set_count }}
            </span>
          </router-link>
        </div>
      </template>
    </template>

    <!-- Ungrouped / 其他 -->
    <template v-if="getSectionTypes('其他', productTypes).length > 0">
      <div class="h-px bg-[rgba(201,168,76,0.08)] mx-4 my-1" />
      <div class="pt-2 pb-1">
        <div class="font-orbitron text-[9px] font-bold tracking-[0.22em] text-gold-dim uppercase px-4 mb-1">
          其他
        </div>
        <router-link
          v-for="pt in getSectionTypes('其他', productTypes)"
          :key="pt.product_type"
          :to="`/sets/${pt.product_type}`"
          class="flex items-center justify-between px-4 py-1.5 text-xs border-l-2 transition-all"
          :class="isActive(pt)
            ? 'border-l-gold text-gold-light bg-[rgba(201,168,76,0.08)] font-medium'
            : 'border-l-transparent text-gray-500 hover:text-gray-200 hover:bg-[rgba(201,168,76,0.04)]'"
        >
          <span>{{ pt.display_name }}</span>
          <span
            class="font-orbitron text-[9px] px-1 py-0.5 rounded shrink-0 ml-1"
            :class="isActive(pt)
              ? 'text-gold-dim bg-[rgba(201,168,76,0.15)]'
              : 'text-gray-600 bg-dark-3'"
          >
            {{ pt.set_count }}
          </span>
        </router-link>
      </div>
    </template>
  </aside>
</template>
