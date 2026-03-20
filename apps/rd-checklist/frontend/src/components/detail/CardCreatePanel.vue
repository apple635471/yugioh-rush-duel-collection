<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import type { CardCreate } from '@/types/card'
import { createCard, getNextCardId } from '@/api/cards'
import { RARITIES } from '@/constants/rarities'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import Checkbox from 'primevue/checkbox'

const props = defineProps<{
  setId: string
}>()

const emit = defineEmits<{
  cardCreated: []
}>()

const saving = ref(false)
const error = ref('')
const loadingId = ref(true)

const allRarities = RARITIES

const allCardTypes = [
  '通常怪獸', '效果怪獸', '融合怪獸', '儀式怪獸',
  '儀式/效果怪獸', '融合/效果怪獸', '巨極/效果怪獸',
  '通常魔法', '速攻魔法', '永續魔法', '裝備魔法', '場地魔法', '儀式魔法',
  '通常陷阱', '永續陷阱', '反擊陷阱',
]

const attributes = ['光', '暗', '炎', '水', '風', '地']

const rarityOptions = allRarities
const cardTypeOptions = [
  { label: '-- Select --', value: '' },
  ...allCardTypes.map(t => ({ label: t, value: t })),
]
const attributeOptions = [
  { label: '-', value: null },
  ...attributes.map(a => ({ label: a, value: a })),
]

const form = reactive<CardCreate>({
  card_id: '',
  set_id: props.setId,
  name_jp: '',
  name_zh: '',
  card_type: '',
  rarity: 'N',
})

const isMonster = computed(() => (form.card_type ?? '').includes('怪獸'))
const isMaximum = computed(() => (form.card_type ?? '').includes('巨極'))

// Text section expand toggles (same pattern as CardDetailPanel)
const expandedSections = reactive<Record<string, boolean>>({
  description: false,
  summon_condition: false,
  condition: false,
  effect: false,
  continuous_effect: false,
})

const textSections = [
  { key: 'description' as const, label: 'Description', monsterOnly: false },
  { key: 'summon_condition' as const, label: 'Summon Condition', monsterOnly: true },
  { key: 'condition' as const, label: 'Condition', monsterOnly: false },
  { key: 'effect' as const, label: 'Effect', monsterOnly: false },
  { key: 'continuous_effect' as const, label: 'Continuous Effect', monsterOnly: false },
]

function toggleSection(key: string) {
  expandedSections[key] = !expandedSections[key]
  if (!expandedSections[key]) {
    ;(form as any)[key] = null
  }
}

onMounted(async () => {
  try {
    form.card_id = await getNextCardId(props.setId)
  } catch {
    form.card_id = `RD/${props.setId}-JP???`
  } finally {
    loadingId.value = false
  }
})

async function onSubmit() {
  if (!form.card_id || !form.set_id) {
    error.value = 'Card ID and Set ID are required'
    return
  }
  saving.value = true
  error.value = ''
  try {
    // Clear monster-only fields if not a monster
    if (!isMonster.value) {
      form.attribute = null
      form.monster_type = null
      form.level = null
      form.atk = null
      form.defense = null
      form.maximum_atk = null
      form.summon_condition = null
    }
    await createCard(form)
    emit('cardCreated')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to create card'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="p-5">
    <!-- Title -->
    <h2 class="text-lg font-bold text-gray-100 mb-4">Create New Card</h2>

    <!-- Card ID -->
    <div class="bg-gray-700/50 rounded-lg overflow-hidden mb-4">
      <div class="flex items-center px-3 py-2 border-b border-gray-700">
        <span class="w-20 text-xs text-gray-400 shrink-0">Card ID</span>
        <div class="flex-1">
          <div v-if="loadingId" class="text-sm text-gray-500">Loading...</div>
          <InputText
            v-else
            v-model="form.card_id"
            placeholder="e.g. RD/KP01-JP050"
            fluid
            size="small"
          />
        </div>
      </div>

      <!-- Set ID (read-only) -->
      <div class="flex items-center px-3 py-2 border-b border-gray-700">
        <span class="w-20 text-xs text-gray-400 shrink-0">Set</span>
        <span class="text-sm text-gray-200 font-mono">{{ form.set_id }}</span>
      </div>

      <!-- Rarity -->
      <div class="flex items-center px-3 py-2 border-b border-gray-700">
        <span class="w-20 text-xs text-gray-400 shrink-0">Rarity</span>
        <Select
          v-model="form.rarity"
          :options="rarityOptions"
          option-label="label"
          option-value="value"
          size="small"
          class="flex-1"
        />
      </div>

      <!-- Card Type -->
      <div class="flex items-center px-3 py-2 border-b border-gray-700">
        <span class="w-20 text-xs text-gray-400 shrink-0">Type</span>
        <Select
          v-model="form.card_type"
          :options="cardTypeOptions"
          option-label="label"
          option-value="value"
          size="small"
          class="flex-1"
        />
      </div>

      <!-- Monster-only fields -->
      <template v-if="isMonster">
        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">Attribute</span>
          <Select
            v-model="form.attribute"
            :options="attributeOptions"
            option-label="label"
            option-value="value"
            size="small"
            class="flex-1"
          />
        </div>

        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">Race</span>
          <InputText
            v-model="form.monster_type"
            placeholder="e.g. 龍族"
            fluid
            size="small"
            class="flex-1"
          />
        </div>

        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">Level</span>
          <InputNumber
            v-model="form.level"
            :min="1"
            :max="12"
            :use-grouping="false"
            fluid
            size="small"
            class="flex-1"
          />
        </div>

        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">ATK</span>
          <InputText
            v-model="form.atk"
            fluid
            size="small"
            class="flex-1"
          />
        </div>

        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">DEF</span>
          <InputText
            v-model="form.defense"
            fluid
            size="small"
            class="flex-1"
          />
        </div>

        <div v-if="isMaximum" class="flex items-center px-3 py-2 border-b border-gray-700 last:border-b-0">
          <span class="w-20 text-xs text-gold shrink-0">MAX ATK</span>
          <InputText
            v-model="form.maximum_atk"
            fluid
            size="small"
            class="flex-1"
          />
        </div>
      </template>
    </div>

    <!-- Card names -->
    <div class="mb-4">
      <InputText v-model="form.name_zh" placeholder="Chinese Name" fluid size="small" />
      <InputText v-model="form.name_jp" placeholder="Japanese Name" fluid size="small" class="mt-1.5" />
    </div>

    <!-- Legend toggle -->
    <label class="flex items-center gap-2 mb-4 cursor-pointer">
      <Checkbox v-model="form.is_legend" :binary="true" input-id="legend-create" />
      <span class="text-sm text-gray-300">LEGEND Card</span>
    </label>

    <!-- Text sections -->
    <template v-for="section in textSections" :key="section.key">
      <template v-if="!section.monsterOnly || isMonster">
        <div v-if="expandedSections[section.key]" class="mb-3">
          <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-1">{{ section.label }}</h3>
          <Textarea
            v-model="(form as any)[section.key]"
            :rows="2"
            fluid
            size="small"
            class="resize-y"
          />
          <Button
            @click="toggleSection(section.key)"
            variant="text"
            severity="secondary"
            size="small"
            class="text-xs mt-0.5"
          >
            Remove
          </Button>
        </div>
        <Button
          v-else
          @click="toggleSection(section.key)"
          variant="text"
          severity="secondary"
          size="small"
          class="gap-1 text-xs mb-2"
        >
          <span class="text-base leading-none">+</span>
          <span>{{ section.label }}</span>
        </Button>
      </template>
    </template>

    <!-- Error -->
    <div v-if="error" class="text-red-400 text-sm mb-3">{{ error }}</div>

    <!-- Submit -->
    <Button
      @click="onSubmit"
      :disabled="saving || loadingId"
      severity="warn"
      fluid
    >
      {{ saving ? 'Creating...' : 'Create Card' }}
    </Button>

    <p class="text-xs text-gray-600 mt-2 text-center">
      Image can be uploaded after creation.
    </p>
  </div>
</template>
