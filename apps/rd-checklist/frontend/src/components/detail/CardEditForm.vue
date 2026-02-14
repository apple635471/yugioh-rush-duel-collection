<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { Card, CardUpdate } from '@/types/card'
import { updateCard } from '@/api/cards'

const props = defineProps<{
  card: Card
}>()

const emit = defineEmits<{
  saved: []
}>()

const saving = ref(false)
const error = ref('')

const form = reactive<CardUpdate>({
  name_jp: props.card.name_jp,
  name_zh: props.card.name_zh,
  card_type: props.card.card_type,
  attribute: props.card.attribute,
  monster_type: props.card.monster_type,
  level: props.card.level,
  atk: props.card.atk,
  defense: props.card.defense,
  condition: props.card.condition,
  effect: props.card.effect,
})

async function onSubmit() {
  saving.value = true
  error.value = ''
  try {
    await updateCard(props.card.card_id, form)
    emit('saved')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to save'
  } finally {
    saving.value = false
  }
}

const fields: { key: keyof CardUpdate; label: string; type: 'text' | 'textarea' | 'number' }[] = [
  { key: 'name_jp', label: 'Japanese Name', type: 'text' },
  { key: 'name_zh', label: 'Chinese Name', type: 'text' },
  { key: 'card_type', label: 'Card Type', type: 'text' },
  { key: 'attribute', label: 'Attribute', type: 'text' },
  { key: 'monster_type', label: 'Monster Type', type: 'text' },
  { key: 'level', label: 'Level', type: 'number' },
  { key: 'atk', label: 'ATK', type: 'text' },
  { key: 'defense', label: 'DEF', type: 'text' },
  { key: 'condition', label: 'Condition', type: 'textarea' },
  { key: 'effect', label: 'Effect', type: 'textarea' },
]
</script>

<template>
  <form @submit.prevent="onSubmit" class="space-y-3">
    <div v-for="field in fields" :key="field.key">
      <label class="block text-xs text-gray-500 mb-1">{{ field.label }}</label>
      <textarea
        v-if="field.type === 'textarea'"
        v-model="(form as any)[field.key]"
        rows="3"
        class="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500"
      />
      <input
        v-else
        :type="field.type"
        v-model="(form as any)[field.key]"
        class="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500"
      />
    </div>

    <div v-if="error" class="text-red-400 text-sm">{{ error }}</div>

    <button
      type="submit"
      :disabled="saving"
      class="w-full py-2 bg-yellow-500 hover:bg-yellow-400 text-gray-900 font-medium text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {{ saving ? 'Saving...' : 'Save Changes' }}
    </button>
  </form>
</template>
