<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import type { CardCreate } from '@/types/card'
import { createCard, getNextCardId } from '@/api/cards'
import { RARITIES } from '@/constants/rarities'

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

const form = reactive<CardCreate>({
  card_id: '',
  set_id: props.setId,
  name_jp: '',
  name_zh: '',
  card_type: '',
  rarity: 'N',
})

const isMonster = computed(() => (form.card_type ?? '').includes('怪獸'))

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

const inputClass = 'w-full bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-sm text-gray-100 focus:outline-none focus:border-yellow-500'
const selectClass = 'w-full bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-sm text-gray-100 focus:outline-none focus:border-yellow-500 appearance-none'
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
          <input v-else v-model="form.card_id" :class="inputClass" placeholder="e.g. RD/KP01-JP050" />
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
        <select v-model="form.rarity" :class="selectClass">
          <option v-for="r in allRarities" :key="r.value" :value="r.value">{{ r.label }}</option>
        </select>
      </div>

      <!-- Card Type -->
      <div class="flex items-center px-3 py-2 border-b border-gray-700">
        <span class="w-20 text-xs text-gray-400 shrink-0">Type</span>
        <select v-model="form.card_type" :class="selectClass">
          <option value="">-- Select --</option>
          <option v-for="t in allCardTypes" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>

      <!-- Monster-only fields -->
      <template v-if="isMonster">
        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">Attribute</span>
          <select v-model="form.attribute" :class="selectClass">
            <option :value="null">-</option>
            <option v-for="a in attributes" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>

        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">Race</span>
          <input v-model="form.monster_type" :class="inputClass" placeholder="e.g. 龍族" />
        </div>

        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">Level</span>
          <input v-model.number="form.level" type="number" min="1" max="12" :class="inputClass" />
        </div>

        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">ATK</span>
          <input v-model="form.atk" :class="inputClass" />
        </div>

        <div class="flex items-center px-3 py-2 border-b border-gray-700 last:border-b-0">
          <span class="w-20 text-xs text-gray-400 shrink-0">DEF</span>
          <input v-model="form.defense" :class="inputClass" />
        </div>
      </template>
    </div>

    <!-- Card names -->
    <div class="mb-4">
      <input v-model="form.name_zh" :class="inputClass" placeholder="Chinese Name" />
      <input v-model="form.name_jp" :class="inputClass" class="mt-1.5" placeholder="Japanese Name" />
    </div>

    <!-- Legend toggle -->
    <label class="flex items-center gap-2 mb-4 text-sm text-gray-300 cursor-pointer">
      <input type="checkbox" v-model="form.is_legend" class="rounded bg-gray-700 border-gray-600 text-yellow-500 focus:ring-yellow-500" />
      LEGEND Card
    </label>

    <!-- Text sections -->
    <template v-for="section in textSections" :key="section.key">
      <template v-if="!section.monsterOnly || isMonster">
        <div v-if="expandedSections[section.key]" class="mb-3">
          <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-1">{{ section.label }}</h3>
          <textarea
            v-model="(form as any)[section.key]"
            rows="2"
            :class="inputClass"
            class="resize-y"
          />
          <button
            @click="toggleSection(section.key)"
            class="text-xs text-gray-600 hover:text-gray-400 mt-0.5"
          >
            Remove
          </button>
        </div>
        <button
          v-else
          @click="toggleSection(section.key)"
          class="flex items-center gap-1 text-xs text-gray-600 hover:text-yellow-500 mb-2 transition-colors"
        >
          <span class="text-base leading-none">+</span>
          <span>{{ section.label }}</span>
        </button>
      </template>
    </template>

    <!-- Error -->
    <div v-if="error" class="text-red-400 text-sm mb-3">{{ error }}</div>

    <!-- Submit -->
    <button
      @click="onSubmit"
      :disabled="saving || loadingId"
      class="w-full py-2 bg-yellow-500 hover:bg-yellow-400 text-gray-900 font-medium text-sm rounded-lg transition-colors disabled:opacity-50"
    >
      {{ saving ? 'Creating...' : 'Create Card' }}
    </button>

    <p class="text-xs text-gray-600 mt-2 text-center">
      Image can be uploaded after creation.
    </p>
  </div>
</template>
