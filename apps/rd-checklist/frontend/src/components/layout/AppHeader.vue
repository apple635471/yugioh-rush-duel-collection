<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import InputText from 'primevue/inputtext'

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
  <header class="bg-dark-1 border-b border-[rgba(201,168,76,0.18)] sticky top-0 z-40 backdrop-blur-sm">
    <div class="container mx-auto max-w-screen-2xl px-4 h-14 flex items-center gap-4">
      <!-- Logo / Home link -->
      <router-link
        to="/"
        class="font-cinzel text-xl font-bold text-gold whitespace-nowrap hover:text-gold-light transition-colors tracking-wide"
      >
        RD Checklist
      </router-link>

      <!-- Search bar -->
      <form @submit.prevent="onSearch" class="flex-1 max-w-md">
        <div class="relative">
          <InputText
            v-model="searchQuery"
            placeholder="Search cards..."
            size="small"
            fluid
            class="pl-9"
          />
          <svg
            class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
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
          class="px-3 py-1.5 rounded-md transition-colors font-medium"
          :class="route.name === 'home' || route.name === 'sets-by-type'
            ? 'bg-gold/10 text-gold border border-gold/30'
            : 'text-gray-400 hover:text-gray-100 hover:bg-white/5'"
        >
          Browse
        </router-link>
        <router-link
          :to="{ name: 'search' }"
          class="px-3 py-1.5 rounded-md transition-colors font-medium"
          :class="route.name === 'search'
            ? 'bg-gold/10 text-gold border border-gold/30'
            : 'text-gray-400 hover:text-gray-100 hover:bg-white/5'"
        >
          Search
        </router-link>
      </nav>
    </div>
  </header>
</template>
