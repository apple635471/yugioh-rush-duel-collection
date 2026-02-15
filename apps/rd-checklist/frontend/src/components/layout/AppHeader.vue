<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const searchQuery = ref('')

function onSearch() {
  const q = searchQuery.value.trim()
  if (q) {
    router.push({ name: 'search', query: { q } })
  }
}
</script>

<template>
  <header class="bg-gray-800 border-b border-gray-700 sticky top-0 z-40">
    <div class="container mx-auto max-w-7xl px-4 h-14 flex items-center gap-4">
      <!-- Logo / Home link -->
      <router-link
        to="/"
        class="text-lg font-bold text-yellow-400 whitespace-nowrap hover:text-yellow-300 transition-colors"
      >
        RD Checklist
      </router-link>

      <!-- Search bar -->
      <form @submit.prevent="onSearch" class="flex-1 max-w-md">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search cards..."
            class="w-full bg-gray-700 border border-gray-600 rounded-lg pl-9 pr-3 py-1.5 text-sm text-gray-100 placeholder-gray-400 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 transition-colors"
          />
          <svg
            class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" stroke-linecap="round" />
          </svg>
        </div>
      </form>

      <!-- Spacer -->
      <div class="flex-1"></div>

      <!-- Nav links -->
      <nav class="flex items-center gap-1 text-sm">
        <router-link
          to="/"
          class="px-3 py-1.5 rounded-md transition-colors"
          :class="route.name === 'home' || route.name === 'sets-by-type'
            ? 'bg-gray-700 text-yellow-400'
            : 'text-gray-300 hover:text-gray-100 hover:bg-gray-700'"
        >
          Browse
        </router-link>
        <router-link
          :to="{ name: 'search' }"
          class="px-3 py-1.5 rounded-md transition-colors"
          :class="route.name === 'search'
            ? 'bg-gray-700 text-yellow-400'
            : 'text-gray-300 hover:text-gray-100 hover:bg-gray-700'"
        >
          Search
        </router-link>
      </nav>
    </div>
  </header>
</template>
