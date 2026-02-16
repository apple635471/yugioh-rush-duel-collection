<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import type { CardSetWithCards, CardSetUpdate, CardSetOverride } from '@/types/cardSet'
import { updateCardSet, fetchCardSetOverrides, deleteCardSetOverride } from '@/api/cardSets'

const props = defineProps<{
  cardSet: CardSetWithCards
}>()

const emit = defineEmits<{
  updated: []
}>()

const editing = ref(false)
const saving = ref(false)
const error = ref('')
const overrides = ref<CardSetOverride[]>([])
const showOverrides = ref(false)

const form = reactive<CardSetUpdate>({})

const productTypes = [
  { value: 'booster', label: 'Booster Pack' },
  { value: 'starter', label: 'Starter Deck' },
  { value: 'structure_deck', label: 'Structure Deck' },
  { value: 'character_pack', label: 'Character Pack' },
  { value: 'go_rush_character', label: 'Go Rush Character' },
  { value: 'go_rush_deck', label: 'Go Rush Deck' },
  { value: 'battle_pack', label: 'Battle Pack' },
  { value: 'maximum_pack', label: 'Maximum Pack' },
  { value: 'extra_pack', label: 'Extra Pack' },
  { value: 'legend_pack', label: 'Legend Pack' },
  { value: 'vs_pack', label: 'VS Pack' },
  { value: 'tournament_pack', label: 'Tournament Pack' },
  { value: 'advanced_pack', label: 'Advanced Pack' },
  { value: 'over_rush_pack', label: 'Over Rush Pack' },
  { value: 'unknown', label: 'Other' },
]

const overriddenFields = computed(() => new Set(overrides.value.map(o => o.field_name)))

function startEdit() {
  const s = props.cardSet
  Object.assign(form, {
    set_name_jp: s.set_name_jp,
    set_name_zh: s.set_name_zh,
    product_type: s.product_type,
    release_date: s.release_date ?? '',
    total_cards: s.total_cards,
    rarity_distribution: s.rarity_distribution ?? '',
  })
  error.value = ''
  editing.value = true
  loadOverrides()
}

function cancelEdit() {
  editing.value = false
  error.value = ''
}

async function saveEdit() {
  saving.value = true
  error.value = ''
  try {
    await updateCardSet(props.cardSet.set_id, form)
    editing.value = false
    emit('updated')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to save'
  } finally {
    saving.value = false
  }
}

async function loadOverrides() {
  try {
    overrides.value = await fetchCardSetOverrides(props.cardSet.set_id)
  } catch {
    overrides.value = []
  }
}

async function removeOverride(fieldName: string) {
  try {
    await deleteCardSetOverride(props.cardSet.set_id, fieldName)
    overrides.value = overrides.value.filter(o => o.field_name !== fieldName)
    emit('updated')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to remove override'
  }
}

const fieldLabels: Record<string, string> = {
  set_name_jp: 'Japanese Name',
  set_name_zh: 'Chinese Name',
  product_type: 'Product Type',
  release_date: 'Release Date',
  total_cards: 'Total Cards',
  rarity_distribution: 'Rarity Distribution',
}

const inputClass = 'w-full bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-sm text-gray-100 focus:outline-none focus:border-yellow-500'
const selectClass = 'w-full bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-sm text-gray-100 focus:outline-none focus:border-yellow-500 appearance-none'
</script>

<template>
  <!-- View mode -->
  <template v-if="!editing">
    <div class="flex items-start justify-between gap-4 mb-3">
      <div>
        <h1 class="text-xl font-bold text-gray-100">
          {{ cardSet.set_name_zh || cardSet.set_name_jp }}
        </h1>
        <p v-if="cardSet.set_name_zh && cardSet.set_name_jp" class="text-sm text-gray-400 mt-0.5">
          {{ cardSet.set_name_jp }}
        </p>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <button
          @click="startEdit"
          class="text-xs text-gray-400 hover:text-yellow-400 border border-gray-600 hover:border-yellow-500/50 rounded px-2 py-1 transition-colors"
          title="Edit set metadata"
        >
          <svg class="w-3.5 h-3.5 inline-block mr-0.5 -mt-px" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
          </svg>
          Edit
        </button>
        <slot name="view-toggle" />
      </div>
    </div>

    <!-- Set meta tags -->
    <div class="flex flex-wrap gap-3 text-xs text-gray-400">
      <span class="bg-gray-700 px-2 py-0.5 rounded">{{ cardSet.set_id }}</span>
      <span v-if="cardSet.release_date">{{ cardSet.release_date }}</span>
      <span>{{ cardSet.cards?.length ?? cardSet.total_cards }} cards</span>
    </div>
  </template>

  <!-- Edit mode -->
  <template v-else>
    <div class="bg-gray-800/50 border border-gray-700 rounded-lg p-4 mb-2">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-medium text-gray-300">Edit Set Metadata</h2>
        <span class="bg-gray-700 px-2 py-0.5 rounded text-xs text-gray-400">{{ cardSet.set_id }}</span>
      </div>

      <div class="space-y-2.5">
        <!-- Chinese Name -->
        <div class="flex items-center gap-2">
          <label class="w-24 text-xs text-gray-400 shrink-0">Chinese Name</label>
          <div class="flex-1 relative">
            <input v-model="form.set_name_zh" :class="inputClass" placeholder="e.g. 衝擊極限包" />
            <span v-if="overriddenFields.has('set_name_zh')" class="absolute right-2 top-1/2 -translate-y-1/2 text-yellow-500" title="Overridden (won't be reset by import)">
              <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 2a1 1 0 0 1 1 1v1h1a1 1 0 0 1 0 2H6v1a1 1 0 0 1-2 0V6H3a1 1 0 0 1 0-2h1V3a1 1 0 0 1 1-1Zm0 10a1 1 0 0 1 1 1v1h1a1 1 0 1 1 0 2H6v1a1 1 0 1 1-2 0v-1H3a1 1 0 1 1 0-2h1v-1a1 1 0 0 1 1-1Zm7-10a1 1 0 0 1 .967.744L14.146 7.2 17.5 9.134a1 1 0 0 1 0 1.732l-3.354 1.935-1.18 4.455a1 1 0 0 1-1.933 0L9.854 12.8 6.5 10.866a1 1 0 0 1 0-1.732l3.354-1.935 1.18-4.455A1 1 0 0 1 12 2Z" clip-rule="evenodd"/></svg>
            </span>
          </div>
        </div>

        <!-- Japanese Name -->
        <div class="flex items-center gap-2">
          <label class="w-24 text-xs text-gray-400 shrink-0">Japanese Name</label>
          <div class="flex-1 relative">
            <input v-model="form.set_name_jp" :class="inputClass" />
            <span v-if="overriddenFields.has('set_name_jp')" class="absolute right-2 top-1/2 -translate-y-1/2 text-yellow-500" title="Overridden">
              <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 2a1 1 0 0 1 1 1v1h1a1 1 0 0 1 0 2H6v1a1 1 0 0 1-2 0V6H3a1 1 0 0 1 0-2h1V3a1 1 0 0 1 1-1Zm0 10a1 1 0 0 1 1 1v1h1a1 1 0 1 1 0 2H6v1a1 1 0 1 1-2 0v-1H3a1 1 0 1 1 0-2h1v-1a1 1 0 0 1 1-1Zm7-10a1 1 0 0 1 .967.744L14.146 7.2 17.5 9.134a1 1 0 0 1 0 1.732l-3.354 1.935-1.18 4.455a1 1 0 0 1-1.933 0L9.854 12.8 6.5 10.866a1 1 0 0 1 0-1.732l3.354-1.935 1.18-4.455A1 1 0 0 1 12 2Z" clip-rule="evenodd"/></svg>
            </span>
          </div>
        </div>

        <!-- Product Type -->
        <div class="flex items-center gap-2">
          <label class="w-24 text-xs text-gray-400 shrink-0">Product Type</label>
          <div class="flex-1 relative">
            <select v-model="form.product_type" :class="selectClass">
              <option v-for="pt in productTypes" :key="pt.value" :value="pt.value">{{ pt.label }}</option>
            </select>
            <span v-if="overriddenFields.has('product_type')" class="absolute right-6 top-1/2 -translate-y-1/2 text-yellow-500" title="Overridden">
              <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 2a1 1 0 0 1 1 1v1h1a1 1 0 0 1 0 2H6v1a1 1 0 0 1-2 0V6H3a1 1 0 0 1 0-2h1V3a1 1 0 0 1 1-1Zm0 10a1 1 0 0 1 1 1v1h1a1 1 0 1 1 0 2H6v1a1 1 0 1 1-2 0v-1H3a1 1 0 1 1 0-2h1v-1a1 1 0 0 1 1-1Zm7-10a1 1 0 0 1 .967.744L14.146 7.2 17.5 9.134a1 1 0 0 1 0 1.732l-3.354 1.935-1.18 4.455a1 1 0 0 1-1.933 0L9.854 12.8 6.5 10.866a1 1 0 0 1 0-1.732l3.354-1.935 1.18-4.455A1 1 0 0 1 12 2Z" clip-rule="evenodd"/></svg>
            </span>
          </div>
        </div>

        <!-- Release Date -->
        <div class="flex items-center gap-2">
          <label class="w-24 text-xs text-gray-400 shrink-0">Release Date</label>
          <div class="flex-1 relative">
            <input v-model="form.release_date" :class="inputClass" placeholder="e.g. 2024/4/13" />
            <span v-if="overriddenFields.has('release_date')" class="absolute right-2 top-1/2 -translate-y-1/2 text-yellow-500" title="Overridden">
              <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 2a1 1 0 0 1 1 1v1h1a1 1 0 0 1 0 2H6v1a1 1 0 0 1-2 0V6H3a1 1 0 0 1 0-2h1V3a1 1 0 0 1 1-1Zm0 10a1 1 0 0 1 1 1v1h1a1 1 0 1 1 0 2H6v1a1 1 0 1 1-2 0v-1H3a1 1 0 1 1 0-2h1v-1a1 1 0 0 1 1-1Zm7-10a1 1 0 0 1 .967.744L14.146 7.2 17.5 9.134a1 1 0 0 1 0 1.732l-3.354 1.935-1.18 4.455a1 1 0 0 1-1.933 0L9.854 12.8 6.5 10.866a1 1 0 0 1 0-1.732l3.354-1.935 1.18-4.455A1 1 0 0 1 12 2Z" clip-rule="evenodd"/></svg>
            </span>
          </div>
        </div>

        <!-- Total Cards -->
        <div class="flex items-center gap-2">
          <label class="w-24 text-xs text-gray-400 shrink-0">Total Cards</label>
          <div class="flex-1 relative">
            <input v-model.number="form.total_cards" type="number" min="0" :class="inputClass" />
            <span v-if="overriddenFields.has('total_cards')" class="absolute right-2 top-1/2 -translate-y-1/2 text-yellow-500" title="Overridden">
              <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 2a1 1 0 0 1 1 1v1h1a1 1 0 0 1 0 2H6v1a1 1 0 0 1-2 0V6H3a1 1 0 0 1 0-2h1V3a1 1 0 0 1 1-1Zm0 10a1 1 0 0 1 1 1v1h1a1 1 0 1 1 0 2H6v1a1 1 0 1 1-2 0v-1H3a1 1 0 1 1 0-2h1v-1a1 1 0 0 1 1-1Zm7-10a1 1 0 0 1 .967.744L14.146 7.2 17.5 9.134a1 1 0 0 1 0 1.732l-3.354 1.935-1.18 4.455a1 1 0 0 1-1.933 0L9.854 12.8 6.5 10.866a1 1 0 0 1 0-1.732l3.354-1.935 1.18-4.455A1 1 0 0 1 12 2Z" clip-rule="evenodd"/></svg>
            </span>
          </div>
        </div>

        <!-- Rarity Distribution -->
        <div class="flex items-start gap-2">
          <label class="w-24 text-xs text-gray-400 shrink-0 pt-1.5">Rarity Dist.</label>
          <div class="flex-1 relative">
            <input v-model="form.rarity_distribution" :class="inputClass" placeholder='e.g. {"UR":4,"SR":6,"R":12,"N":28}' />
            <span v-if="overriddenFields.has('rarity_distribution')" class="absolute right-2 top-1/2 -translate-y-1/2 text-yellow-500" title="Overridden">
              <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 2a1 1 0 0 1 1 1v1h1a1 1 0 0 1 0 2H6v1a1 1 0 0 1-2 0V6H3a1 1 0 0 1 0-2h1V3a1 1 0 0 1 1-1Zm0 10a1 1 0 0 1 1 1v1h1a1 1 0 1 1 0 2H6v1a1 1 0 1 1-2 0v-1H3a1 1 0 1 1 0-2h1v-1a1 1 0 0 1 1-1Zm7-10a1 1 0 0 1 .967.744L14.146 7.2 17.5 9.134a1 1 0 0 1 0 1.732l-3.354 1.935-1.18 4.455a1 1 0 0 1-1.933 0L9.854 12.8 6.5 10.866a1 1 0 0 1 0-1.732l3.354-1.935 1.18-4.455A1 1 0 0 1 12 2Z" clip-rule="evenodd"/></svg>
            </span>
          </div>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="text-red-400 text-sm mt-3">{{ error }}</div>

      <!-- Action buttons -->
      <div class="flex gap-2 mt-4">
        <button
          @click="saveEdit"
          :disabled="saving"
          class="flex-1 py-1.5 bg-yellow-500 hover:bg-yellow-400 text-gray-900 font-medium text-sm rounded-lg transition-colors disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : 'Save' }}
        </button>
        <button
          @click="cancelEdit"
          class="flex-1 py-1.5 text-sm text-gray-300 hover:text-gray-100 border border-gray-600 rounded-lg hover:border-gray-400 transition-colors"
        >
          Cancel
        </button>
      </div>

      <!-- Overrides section -->
      <div v-if="overrides.length > 0" class="mt-3 pt-3 border-t border-gray-700">
        <button
          @click="showOverrides = !showOverrides"
          class="text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
        >
          <svg
            class="w-3 h-3 transition-transform"
            :class="{ 'rotate-90': showOverrides }"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
          {{ overrides.length }} override(s) active
        </button>
        <div v-if="showOverrides" class="mt-2 space-y-1">
          <div
            v-for="ov in overrides"
            :key="ov.field_name"
            class="flex items-center justify-between text-xs bg-gray-700/50 rounded px-2 py-1"
          >
            <span class="text-gray-300">
              <span class="text-yellow-500">{{ fieldLabels[ov.field_name] || ov.field_name }}</span>
            </span>
            <button
              @click="removeOverride(ov.field_name)"
              class="text-gray-500 hover:text-red-400 transition-colors"
              title="Remove override (revert to scraper value on next import)"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </template>
</template>
