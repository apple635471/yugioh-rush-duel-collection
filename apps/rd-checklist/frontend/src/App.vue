<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/detail/AppSidebar.vue'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <AppHeader />
    <main
      class="flex-1 container mx-auto px-4 sm:px-6 py-6 max-w-screen-2xl transition-[padding-right] duration-500 ease-in-out"
      :class="{ 'sm:pr-[28rem]': ui.sidebarOpen && !ui.sidebarMinimized }"
    >
      <RouterView />
    </main>
    <AppSidebar />
  </div>
</template>
