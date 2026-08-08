<script setup lang="ts">
/**
 * Editor for an ATK/DEF-style stat: the raw value is a string that must be
 * either "?" or a whole number. Offers keyboard entry (allows "?") plus a
 * slider that adjusts in steps of 100. Shows an invalid state for bad input;
 * the parent is responsible for the authoritative save-time validation.
 */
import { computed } from 'vue'
import InputText from 'primevue/inputtext'
import Slider from 'primevue/slider'
import { isStatValid } from '@/utils/cardFields'

const props = withDefaults(defineProps<{
  modelValue: string | null | undefined
  max?: number
}>(), { max: 5000 })

const emit = defineEmits<{ 'update:modelValue': [string | null] }>()

const text = computed<string>({
  get: () => props.modelValue ?? '',
  set: (v: string) => emit('update:modelValue', v.trim() === '' ? null : v.trim()),
})

const valid = computed(() => isStatValid(props.modelValue))

const sliderVal = computed<number>({
  get: () => {
    const n = parseInt(props.modelValue ?? '', 10)
    return Number.isNaN(n) ? 0 : n
  },
  set: (v: number) => emit('update:modelValue', String(v)),
})
</script>

<template>
  <div class="space-y-2">
    <InputText
      v-model="text"
      :invalid="!valid"
      fluid
      size="small"
      placeholder="數字或 ?"
    />
    <Slider
      v-model="sliderVal"
      :min="0"
      :max="max"
      :step="100"
      :disabled="modelValue === '?'"
    />
    <p v-if="!valid" class="text-[10px] text-red-400 leading-none">只能填數字或 ?</p>
  </div>
</template>
