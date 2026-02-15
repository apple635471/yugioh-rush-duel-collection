<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import type { Card, CardUpdate } from '@/types/card'
import { getCardImageUrl, updateOwnership, updateCard, uploadCardImage, revertCardImage } from '@/api/cards'
import RarityTabs from '@/components/cards/RarityTabs.vue'
import OwnershipControl from '@/components/cards/OwnershipControl.vue'

const props = defineProps<{
  card: Card
  activeRarity: string
}>()

const emit = defineEmits<{
  cardUpdated: []
}>()

const currentRarity = ref(props.activeRarity)
const editing = ref(false)
const saving = ref(false)
const error = ref('')

const form = reactive<CardUpdate>({})

const allCardTypes = [
  '通常怪獸', '效果怪獸', '融合怪獸', '儀式怪獸',
  '儀式/效果怪獸', '融合/效果怪獸', '巨極/效果怪獸',
  '通常魔法', '速攻魔法', '永續魔法', '裝備魔法', '場地魔法', '儀式魔法',
  '通常陷阱', '永續陷阱', '反擊陷阱',
]

const attributes = ['光', '暗', '炎', '水', '風', '地']

const isMonster = computed(() => {
  const ct = editing.value ? (form.card_type ?? props.card.card_type) : props.card.card_type
  return ct.includes('怪獸')
})

// Track which optional text sections are expanded (for adding when empty)
const expandedSections = reactive<Record<string, boolean>>({
  summon_condition: false,
  condition: false,
  effect: false,
  continuous_effect: false,
})

function startEdit() {
  const c = props.card
  Object.assign(form, {
    name_jp: c.name_jp,
    name_zh: c.name_zh,
    card_type: c.card_type,
    attribute: c.attribute,
    monster_type: c.monster_type,
    level: c.level,
    atk: c.atk,
    defense: c.defense,
    summon_condition: c.summon_condition,
    condition: c.condition,
    effect: c.effect,
    continuous_effect: c.continuous_effect,
  })
  // Expand sections that already have content
  expandedSections.summon_condition = !!c.summon_condition
  expandedSections.condition = !!c.condition
  expandedSections.effect = !!c.effect
  expandedSections.continuous_effect = !!c.continuous_effect
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  error.value = ''
}

async function saveEdit() {
  saving.value = true
  error.value = ''
  try {
    // If not monster, clear monster-only fields
    if (!isMonster.value) {
      form.attribute = null
      form.monster_type = null
      form.level = null
      form.atk = null
      form.defense = null
      form.summon_condition = null
    }
    await updateCard(props.card.card_id, form)
    editing.value = false
    emit('cardUpdated')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to save'
  } finally {
    saving.value = false
  }
}

const activeVariant = computed(() =>
  props.card.variants.find(v => v.rarity === currentRarity.value) ?? props.card.variants[0]
)

// Image cache buster — set after upload/revert to force browser reload
const imageCacheBuster = ref(0)

const imageUrl = computed(() => {
  if (!activeVariant.value) return ''
  const base = getCardImageUrl(props.card.card_id, activeVariant.value.rarity)
  // Always bust cache for user uploads (image can change at same URL)
  if (imageCacheBuster.value) return `${base}?t=${imageCacheBuster.value}`
  if (activeVariant.value.image_source === 'user_upload') return `${base}?t=1`
  return base
})

const isUserUpload = computed(() => activeVariant.value?.image_source === 'user_upload')

// Image upload
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const reverting = ref(false)
const imageError = ref('')

function triggerFileSelect() {
  fileInput.value?.click()
}

async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  uploading.value = true
  imageError.value = ''
  try {
    const updated = await uploadCardImage(props.card.card_id, currentRarity.value, file)
    // Update local variant data
    const v = props.card.variants.find(v => v.rarity === currentRarity.value)
    if (v) {
      v.image_source = updated.image_source
      v.image_path = updated.image_path
    }
    imageCacheBuster.value = Date.now()
    emit('cardUpdated')
  } catch (e: any) {
    imageError.value = e?.response?.data?.detail ?? 'Upload failed'
  } finally {
    uploading.value = false
    // Reset input so same file can be re-selected
    input.value = ''
  }
}

async function onRevertImage() {
  reverting.value = true
  imageError.value = ''
  try {
    const updated = await revertCardImage(props.card.card_id, currentRarity.value)
    const v = props.card.variants.find(v => v.rarity === currentRarity.value)
    if (v) {
      v.image_source = updated.image_source
      v.image_path = updated.image_path
    }
    imageCacheBuster.value = Date.now()
    emit('cardUpdated')
  } catch (e: any) {
    imageError.value = e?.response?.data?.detail ?? 'Revert failed'
  } finally {
    reverting.value = false
  }
}

async function onOwnershipUpdate(cardId: string, rarity: string, count: number) {
  await updateOwnership(cardId, rarity, count)
  const v = props.card.variants.find(v => v.card_id === cardId && v.rarity === rarity)
  if (v) v.owned_count = count
}

// Text section definitions for DRY rendering
const textSections = computed(() => [
  { key: 'summon_condition' as const, label: 'Summon Condition', monsterOnly: true },
  { key: 'condition' as const, label: 'Condition', monsterOnly: false },
  { key: 'effect' as const, label: 'Effect', monsterOnly: false },
  { key: 'continuous_effect' as const, label: 'Continuous Effect', monsterOnly: false },
])

function toggleSection(key: string) {
  expandedSections[key] = !expandedSections[key]
  if (!expandedSections[key]) {
    ;(form as any)[key] = null
  }
}

const inputClass = 'w-full bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-sm text-gray-100 focus:outline-none focus:border-yellow-500'
const selectClass = 'w-full bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-sm text-gray-100 focus:outline-none focus:border-yellow-500 appearance-none'
</script>

<template>
  <div class="p-5">
    <!-- Image with upload overlay -->
    <div class="relative group aspect-[59/86] bg-gray-700 rounded-lg overflow-hidden mb-2">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="card.name_zh || card.name_jp"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-gray-500">
        No Image
      </div>

      <!-- Upload overlay (hover) -->
      <div
        @click="triggerFileSelect"
        class="absolute inset-0 bg-black/50 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
        :class="{ '!opacity-100': uploading }"
      >
        <!-- Spinner while uploading -->
        <div v-if="uploading" class="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
        <template v-else>
          <!-- Camera icon -->
          <svg class="w-8 h-8 text-white/80 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6.827 6.175A2.31 2.31 0 0 1 5.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 0 0-1.134-.175 2.31 2.31 0 0 1-1.64-1.055l-.822-1.316a2.192 2.192 0 0 0-1.736-1.039 48.774 48.774 0 0 0-5.232 0 2.192 2.192 0 0 0-1.736 1.039l-.821 1.316Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 12.75a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0Z" />
          </svg>
          <span class="text-white/80 text-xs font-medium">Upload Image</span>
        </template>
      </div>

      <!-- Hidden file input -->
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="onFileSelected"
      />
    </div>

    <!-- Revert button (only for user uploads) -->
    <div class="mb-2 flex items-center justify-between min-h-[1.5rem]">
      <button
        v-if="isUserUpload"
        @click="onRevertImage"
        :disabled="reverting"
        class="text-xs text-gray-400 hover:text-yellow-400 transition-colors flex items-center gap-1"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3" />
        </svg>
        {{ reverting ? 'Reverting...' : 'Revert to original' }}
      </button>
      <span v-if="imageError" class="text-xs text-red-400">{{ imageError }}</span>
    </div>

    <!-- Rarity tabs -->
    <div class="flex items-center justify-between mb-3">
      <RarityTabs
        :variants="card.variants"
        :active-rarity="currentRarity"
        @select="currentRarity = $event"
      />
      <OwnershipControl
        :card-id="card.card_id"
        :rarity="currentRarity"
        :owned-count="activeVariant?.owned_count ?? 0"
        @update="onOwnershipUpdate"
      />
    </div>

    <!-- Card names -->
    <div class="mb-4">
      <template v-if="editing">
        <input v-model="form.name_zh" :class="inputClass" placeholder="Chinese Name" />
        <input v-model="form.name_jp" :class="inputClass" class="mt-1.5" placeholder="Japanese Name" />
      </template>
      <template v-else>
        <h2 class="text-lg font-bold text-gray-100 leading-snug">
          {{ card.name_zh || card.name_jp }}
        </h2>
        <p v-if="card.name_zh && card.name_jp" class="text-sm text-gray-400 mt-0.5">
          {{ card.name_jp }}
        </p>
      </template>
      <div v-if="card.is_legend" class="mt-1">
        <span class="bg-amber-500/90 text-black text-xs font-bold px-1.5 py-0.5 rounded">LEGEND</span>
      </div>
    </div>

    <!-- Detail table (inline editable) -->
    <div class="bg-gray-700/50 rounded-lg overflow-hidden mb-4">
      <!-- Card ID (always read-only) -->
      <div class="flex items-center px-3 py-2 border-b border-gray-700">
        <span class="w-20 text-xs text-gray-400 shrink-0">Card ID</span>
        <span class="text-sm text-gray-200 font-mono">{{ card.card_id }}</span>
      </div>

      <!-- Card Type -->
      <div class="flex items-center px-3 py-2 border-b border-gray-700">
        <span class="w-20 text-xs text-gray-400 shrink-0">Type</span>
        <select v-if="editing" v-model="form.card_type" :class="selectClass">
          <option v-for="t in allCardTypes" :key="t" :value="t">{{ t }}</option>
        </select>
        <span v-else class="text-sm text-gray-200 font-mono">{{ card.card_type }}</span>
      </div>

      <!-- Monster-only fields -->
      <template v-if="isMonster">
        <!-- Attribute -->
        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">Attribute</span>
          <select v-if="editing" v-model="form.attribute" :class="selectClass">
            <option :value="null">-</option>
            <option v-for="a in attributes" :key="a" :value="a">{{ a }}</option>
          </select>
          <span v-else-if="card.attribute" class="text-sm text-gray-200 font-mono">{{ card.attribute }}</span>
          <span v-else class="text-sm text-gray-600">-</span>
        </div>

        <!-- Monster Type -->
        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">Race</span>
          <input v-if="editing" v-model="form.monster_type" :class="inputClass" placeholder="e.g. 龍族" />
          <span v-else-if="card.monster_type" class="text-sm text-gray-200 font-mono">{{ card.monster_type }}</span>
          <span v-else class="text-sm text-gray-600">-</span>
        </div>

        <!-- Level -->
        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">Level</span>
          <input v-if="editing" v-model.number="form.level" type="number" min="1" max="12" :class="inputClass" />
          <span v-else-if="card.level != null" class="text-sm text-gray-200 font-mono">{{ card.level }}</span>
          <span v-else class="text-sm text-gray-600">-</span>
        </div>

        <!-- ATK -->
        <div class="flex items-center px-3 py-2 border-b border-gray-700">
          <span class="w-20 text-xs text-gray-400 shrink-0">ATK</span>
          <input v-if="editing" v-model="form.atk" :class="inputClass" />
          <span v-else-if="card.atk != null" class="text-sm text-gray-200 font-mono">{{ card.atk }}</span>
          <span v-else class="text-sm text-gray-600">-</span>
        </div>

        <!-- DEF -->
        <div class="flex items-center px-3 py-2 border-b border-gray-700 last:border-b-0">
          <span class="w-20 text-xs text-gray-400 shrink-0">DEF</span>
          <input v-if="editing" v-model="form.defense" :class="inputClass" />
          <span v-else-if="card.defense != null" class="text-sm text-gray-200 font-mono">{{ card.defense }}</span>
          <span v-else class="text-sm text-gray-600">-</span>
        </div>
      </template>
    </div>

    <!-- Text sections: summon_condition, condition, effect, continuous_effect -->
    <template v-for="section in textSections" :key="section.key">
      <!-- Skip monster-only sections for non-monsters -->
      <template v-if="!section.monsterOnly || isMonster">
        <!-- View mode: only show if value exists -->
        <div v-if="!editing && (card as any)[section.key]" class="mb-3">
          <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-1">{{ section.label }}</h3>
          <p class="text-sm text-gray-300 leading-relaxed whitespace-pre-line">{{ (card as any)[section.key] }}</p>
        </div>

        <!-- Edit mode: show expanded or show + button -->
        <template v-if="editing">
          <div v-if="expandedSections[section.key]" class="mb-3">
            <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-1">{{ section.label }}</h3>
            <textarea
              v-model="(form as any)[section.key]"
              rows="2"
              :class="inputClass"
              class="resize-y"
            />
            <button
              v-if="!(card as any)[section.key]"
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
    </template>

    <!-- Error message -->
    <div v-if="error" class="text-red-400 text-sm mb-3">{{ error }}</div>

    <!-- Action buttons -->
    <div v-if="editing" class="flex gap-2">
      <button
        @click="saveEdit"
        :disabled="saving"
        class="flex-1 py-2 bg-yellow-500 hover:bg-yellow-400 text-gray-900 font-medium text-sm rounded-lg transition-colors disabled:opacity-50"
      >
        {{ saving ? 'Saving...' : 'Save' }}
      </button>
      <button
        @click="cancelEdit"
        class="flex-1 py-2 text-sm text-gray-300 hover:text-gray-100 border border-gray-600 rounded-lg hover:border-gray-400 transition-colors"
      >
        Cancel
      </button>
    </div>
    <button
      v-else
      @click="startEdit"
      class="w-full py-2 text-sm text-gray-300 hover:text-yellow-400 border border-gray-600 rounded-lg hover:border-yellow-500/50 transition-colors"
    >
      Edit Card Info
    </button>
  </div>
</template>
