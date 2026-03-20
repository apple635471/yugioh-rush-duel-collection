<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import type { Card, CardUpdate, ScanResult } from '@/types/card'
import { getCardImageUrl, updateOwnership, updateCard, uploadCardImage, revertCardImage, addVariant, editVariantRarity, deleteVariant, scanCard } from '@/api/cards'
import { RARITIES } from '@/constants/rarities'
import { useUiStore } from '@/stores/ui'
import RarityTabs from '@/components/cards/RarityTabs.vue'
import OwnershipControl from '@/components/cards/OwnershipControl.vue'
import ScanResultPanel from '@/components/detail/ScanResultPanel.vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'

const props = defineProps<{
  card: Card
  activeRarity: string
}>()

const emit = defineEmits<{
  cardUpdated: []
}>()

const ui = useUiStore()

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

const cardTypeOptions = allCardTypes.map(t => ({ label: t, value: t }))
const attributeOptions = [
  { label: '-', value: null },
  ...attributes.map(a => ({ label: a, value: a })),
]

const isMonster = computed(() => {
  const ct = editing.value ? (form.card_type ?? props.card.card_type) : props.card.card_type
  return ct.includes('怪獸')
})

// Track which optional text sections are expanded (for adding when empty)
const expandedSections = reactive<Record<string, boolean>>({
  description: false,
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
    description: c.description,
    summon_condition: c.summon_condition,
    condition: c.condition,
    effect: c.effect,
    continuous_effect: c.continuous_effect,
  })
  // Expand sections that already have content
  expandedSections.description = !!c.description
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
    ui.markImageUpdated(props.card.card_id, currentRarity.value)
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
    ui.markImageUpdated(props.card.card_id, currentRarity.value)
    emit('cardUpdated')
  } catch (e: any) {
    imageError.value = e?.response?.data?.detail ?? 'Revert failed'
  } finally {
    reverting.value = false
  }
}

// ── Card scanner ─────────────────────────────────────────────────────────────
const scanPanelOpen = ref(false)
const scanResult = ref<ScanResult | null>(null)
const scanLoading = ref(false)
const scanError = ref('')

async function triggerScan() {
  scanPanelOpen.value = true
  scanLoading.value = true
  scanError.value = ''
  scanResult.value = null
  try {
    scanResult.value = await scanCard(props.card.card_id, currentRarity.value)
  } catch (e: any) {
    scanError.value = e?.response?.data?.detail ?? 'Scan failed'
  } finally {
    scanLoading.value = false
  }
}

async function onOwnershipUpdate(cardId: string, rarity: string, count: number) {
  await updateOwnership(cardId, rarity, count)
  const v = props.card.variants.find(v => v.card_id === cardId && v.rarity === rarity)
  if (v) v.owned_count = count
}

// Text section definitions for DRY rendering
const textSections = computed(() => [
  { key: 'description' as const, label: 'Description', monsterOnly: false },
  { key: 'summon_condition' as const, label: 'Summon Condition', monsterOnly: true },
  { key: 'condition' as const, label: 'Condition', monsterOnly: false },
  { key: 'effect' as const, label: 'Effect', monsterOnly: false },
  { key: 'continuous_effect' as const, label: 'Continuous Effect', monsterOnly: false },
])

// Rarity color mapping
const RARITY_COLOR: Record<string, { badge: string; text: string }> = {
  N:      { badge: 'bg-[rgba(120,120,140,0.25)]', text: 'text-gray-400' },
  NPR:    { badge: 'bg-[rgba(120,120,140,0.25)]', text: 'text-gray-400' },
  R:      { badge: 'bg-[rgba(74,159,238,0.25)]',  text: 'text-blue-300' },
  SR:     { badge: 'bg-[rgba(201,168,76,0.25)]',  text: 'text-gold-light' },
  SPR:    { badge: 'bg-[rgba(201,168,76,0.25)]',  text: 'text-gold-light' },
  UR:     { badge: 'bg-[rgba(176,64,216,0.25)]',  text: 'text-purple-300' },
  PUR:    { badge: 'bg-[rgba(176,64,216,0.25)]',  text: 'text-purple-300' },
  RUR:    { badge: 'bg-[rgba(212,80,96,0.25)]',   text: 'text-red-300' },
  SER:    { badge: 'bg-[rgba(74,159,238,0.25)]',  text: 'text-blue-300' },
  RR:     { badge: 'bg-[rgba(212,80,96,0.25)]',   text: 'text-red-400' },
  ORR:    { badge: 'bg-[rgba(212,80,96,0.25)]',   text: 'text-red-400' },
  ORRPBV: { badge: 'bg-[rgba(176,64,216,0.3)]',  text: 'text-purple-400' },
  FORR:   { badge: 'bg-[rgba(201,168,76,0.35)]',  text: 'text-gold' },
}

function rarityColors(rarity: string) {
  return RARITY_COLOR[rarity] ?? { badge: 'bg-[rgba(120,120,140,0.2)]', text: 'text-gray-400' }
}

function toggleSection(key: string) {
  expandedSections[key] = !expandedSections[key]
  if (!expandedSections[key]) {
    ;(form as any)[key] = null
  }
}

// ---- Variant management ----
const availableRarities = computed(() =>
  RARITIES.filter(r => !props.card.variants.some(v => v.rarity === r.value))
)

// ---- Add Variant ----
const addingVariant = ref(false)
const newVariantRarity = ref('')
const savingVariant = ref(false)
const variantError = ref('')

function startAddVariant() {
  newVariantRarity.value = availableRarities.value[0]?.value ?? ''
  variantError.value = ''
  addingVariant.value = true
}

function cancelAddVariant() {
  addingVariant.value = false
  variantError.value = ''
}

async function submitAddVariant() {
  if (!newVariantRarity.value) return
  savingVariant.value = true
  variantError.value = ''
  try {
    await addVariant(props.card.card_id, { rarity: newVariantRarity.value })
    addingVariant.value = false
    currentRarity.value = newVariantRarity.value
    emit('cardUpdated')
  } catch (e: any) {
    variantError.value = e?.response?.data?.detail ?? 'Failed to add variant'
  } finally {
    savingVariant.value = false
  }
}

// ---- Edit Variant Rarity ----
const editingRarity = ref(false)
const editRarityTarget = ref('')
const savingRarityEdit = ref(false)
const rarityEditError = ref('')

const editableRarities = computed(() =>
  RARITIES.filter(r => !props.card.variants.some(v => v.rarity === r.value) || r.value === currentRarity.value)
    .filter(r => r.value !== currentRarity.value)
)

function startEditRarity() {
  editRarityTarget.value = editableRarities.value[0]?.value ?? ''
  rarityEditError.value = ''
  editingRarity.value = true
}

function cancelEditRarity() {
  editingRarity.value = false
  rarityEditError.value = ''
}

async function submitEditRarity() {
  if (!editRarityTarget.value || editRarityTarget.value === currentRarity.value) return
  savingRarityEdit.value = true
  rarityEditError.value = ''
  try {
    await editVariantRarity(props.card.card_id, currentRarity.value, editRarityTarget.value)
    currentRarity.value = editRarityTarget.value
    editingRarity.value = false
    emit('cardUpdated')
  } catch (e: any) {
    rarityEditError.value = e?.response?.data?.detail ?? 'Failed to edit rarity'
  } finally {
    savingRarityEdit.value = false
  }
}

// ---- Delete Variant ----
const confirmingDelete = ref(false)
const deletingVariant = ref(false)
const deleteError = ref('')

function startDeleteVariant() {
  deleteError.value = ''
  confirmingDelete.value = true
}

function cancelDeleteVariant() {
  confirmingDelete.value = false
  deleteError.value = ''
}

async function submitDeleteVariant() {
  deletingVariant.value = true
  deleteError.value = ''
  try {
    await deleteVariant(props.card.card_id, currentRarity.value)
    confirmingDelete.value = false
    emit('cardUpdated')
    const remaining = props.card.variants.filter(v => v.rarity !== currentRarity.value)
    if (remaining.length > 0 && remaining[0]) currentRarity.value = remaining[0].rarity
  } catch (e: any) {
    deleteError.value = e?.response?.data?.detail ?? 'Failed to delete variant'
  } finally {
    deletingVariant.value = false
  }
}
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
        <div v-if="uploading" class="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
        <template v-else>
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

    <!-- Revert button + Scan button row -->
    <div class="mb-2 flex items-center justify-between min-h-[1.5rem]">
      <Button
        v-if="isUserUpload"
        @click="onRevertImage"
        :disabled="reverting"
        variant="text"
        severity="secondary"
        size="small"
        class="gap-1 text-xs"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3" />
        </svg>
        {{ reverting ? 'Reverting...' : 'Revert to original' }}
      </Button>
      <span v-if="imageError" class="text-xs text-red-400">{{ imageError }}</span>

      <Button
        @click="triggerScan"
        :disabled="scanLoading"
        variant="text"
        severity="secondary"
        size="small"
        title="用 AI 掃描卡牌資訊"
        class="ml-auto gap-1 text-xs"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
        </svg>
        <span>{{ scanLoading ? 'Scanning…' : 'Scan' }}</span>
      </Button>
    </div>

    <!-- Scan result panel (floating, draggable) -->
    <ScanResultPanel
      v-if="scanPanelOpen"
      :card-id="card.card_id"
      :rarity="currentRarity"
      :result="scanResult"
      :loading="scanLoading"
      :error="scanError"
      @close="scanPanelOpen = false"
      @refresh="triggerScan"
    />

    <!-- Rarity tabs -->
    <div class="flex items-center justify-between mb-1">
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

    <!-- Variant management (Add / Edit Rarity / Delete) -->
    <div class="mb-3 space-y-1.5">
      <!-- Add Variant form -->
      <template v-if="addingVariant">
        <div class="flex items-center gap-1.5">
          <Select
            v-model="newVariantRarity"
            :options="availableRarities"
            option-label="label"
            option-value="value"
            size="small"
            class="flex-1"
          />
          <Button
            @click="submitAddVariant"
            :disabled="savingVariant || !newVariantRarity"
            severity="warn"
            size="small"
          >
            {{ savingVariant ? '...' : 'Add' }}
          </Button>
          <Button @click="cancelAddVariant" variant="text" severity="secondary" size="small">
            Cancel
          </Button>
        </div>
        <div v-if="variantError" class="text-red-400 text-xs">{{ variantError }}</div>
      </template>

      <!-- Edit Rarity form -->
      <template v-else-if="editingRarity">
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400 shrink-0">改為</span>
          <Select
            v-model="editRarityTarget"
            :options="editableRarities"
            option-label="label"
            option-value="value"
            size="small"
            class="flex-1"
          />
          <Button
            @click="submitEditRarity"
            :disabled="savingRarityEdit || !editRarityTarget"
            severity="warn"
            size="small"
          >
            {{ savingRarityEdit ? '...' : 'Save' }}
          </Button>
          <Button @click="cancelEditRarity" variant="text" severity="secondary" size="small">
            Cancel
          </Button>
        </div>
        <div v-if="rarityEditError" class="text-red-400 text-xs">{{ rarityEditError }}</div>
      </template>

      <!-- Delete confirm -->
      <template v-else-if="confirmingDelete">
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-300">刪除 <strong>{{ currentRarity }}</strong>？</span>
          <Button
            @click="submitDeleteVariant"
            :disabled="deletingVariant"
            severity="danger"
            size="small"
          >
            {{ deletingVariant ? '...' : '確認刪除' }}
          </Button>
          <Button @click="cancelDeleteVariant" variant="text" severity="secondary" size="small">
            Cancel
          </Button>
        </div>
        <div v-if="deleteError" class="text-red-400 text-xs">{{ deleteError }}</div>
      </template>

      <!-- Default: action buttons row -->
      <div v-else-if="!editing" class="flex items-center gap-3">
        <Button
          v-if="availableRarities.length > 0"
          @click="startAddVariant"
          variant="text"
          severity="secondary"
          size="small"
          class="gap-1 text-xs"
        >
          <span class="text-base leading-none">+</span>
          <span>Add Variant</span>
        </Button>
        <Button
          v-if="editableRarities.length > 0"
          @click="startEditRarity"
          variant="text"
          severity="secondary"
          size="small"
          class="gap-1 text-xs"
        >
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Z" />
          </svg>
          <span>Edit Rarity</span>
        </Button>
        <Button
          v-if="card.variants.length > 1"
          @click="startDeleteVariant"
          variant="text"
          severity="danger"
          size="small"
          class="gap-1 text-xs"
        >
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
          </svg>
          <span>Delete</span>
        </Button>
      </div>
    </div>

    <!-- Card header (name + rarity badge) -->
    <div class="mb-4">
      <template v-if="editing">
        <InputText v-model="form.name_zh" placeholder="Chinese Name" fluid size="small" />
        <InputText v-model="form.name_jp" placeholder="Japanese Name" fluid size="small" class="mt-1.5" />
      </template>
      <template v-else>
        <!-- Rarity badge + legend -->
        <div class="flex items-center gap-2 mb-1.5">
          <span
            class="font-orbitron text-[10px] font-bold px-1.5 py-0.5 rounded tracking-wider"
            :class="[rarityColors(currentRarity).badge, rarityColors(currentRarity).text]"
          >
            {{ currentRarity }}
          </span>
          <span v-if="card.is_legend" class="bg-amber-500/90 text-black text-[10px] font-bold px-1.5 py-0.5 rounded">LEGEND</span>
        </div>
        <!-- Card name in Cinzel -->
        <h2 class="font-cinzel text-lg font-bold text-gray-100 leading-snug">
          {{ card.name_zh || card.name_jp }}
        </h2>
        <p v-if="card.name_zh && card.name_jp" class="text-xs text-gray-500 mt-0.5 font-orbitron tracking-wide">
          {{ card.name_jp }}
        </p>
      </template>
    </div>

    <!-- ATK / DEF stat boxes (view mode, monsters only) -->
    <div v-if="!editing && isMonster && (card.atk != null || card.defense != null)" class="grid grid-cols-2 gap-2 mb-4">
      <div class="rounded-lg border border-[rgba(239,68,68,0.25)] bg-[rgba(239,68,68,0.06)] px-3 py-2 text-center">
        <div class="font-orbitron text-[9px] font-bold tracking-[0.2em] text-red-400/70 uppercase mb-1">ATK</div>
        <div class="font-orbitron text-2xl font-bold text-red-300 leading-none">
          {{ card.atk ?? '?' }}
        </div>
      </div>
      <div class="rounded-lg border border-[rgba(96,165,250,0.25)] bg-[rgba(96,165,250,0.06)] px-3 py-2 text-center">
        <div class="font-orbitron text-[9px] font-bold tracking-[0.2em] text-blue-400/70 uppercase mb-1">DEF</div>
        <div class="font-orbitron text-2xl font-bold text-blue-300 leading-none">
          {{ card.defense ?? '?' }}
        </div>
      </div>
    </div>

    <!-- Detail table (inline editable) -->
    <div class="rounded-lg overflow-hidden mb-4 border border-[rgba(201,168,76,0.1)]">
      <!-- Card ID (always read-only) -->
      <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
        <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">Card ID</span>
        <span class="px-3 py-2 text-sm text-gray-200 font-mono">{{ card.card_id }}</span>
      </div>

      <!-- Card Type -->
      <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
        <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">Type</span>
        <div class="px-3 py-2 flex-1">
          <Select
            v-if="editing"
            v-model="form.card_type"
            :options="cardTypeOptions"
            option-label="label"
            option-value="value"
            size="small"
            class="w-full"
          />
          <span v-else class="text-sm text-gray-200">{{ card.card_type }}</span>
        </div>
      </div>

      <!-- Monster-only fields -->
      <template v-if="isMonster">
        <!-- Attribute -->
        <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
          <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">屬性</span>
          <div class="px-3 py-2 flex-1">
            <Select
              v-if="editing"
              v-model="form.attribute"
              :options="attributeOptions"
              option-label="label"
              option-value="value"
              size="small"
              class="w-full"
            />
            <span v-else-if="card.attribute" class="text-sm text-gray-200">{{ card.attribute }}</span>
            <span v-else class="text-sm text-gray-600">-</span>
          </div>
        </div>

        <!-- Monster Type -->
        <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
          <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">種族</span>
          <div class="px-3 py-2 flex-1">
            <InputText
              v-if="editing"
              v-model="form.monster_type"
              placeholder="e.g. 龍族"
              fluid
              size="small"
            />
            <span v-else-if="card.monster_type" class="text-sm text-gray-200">{{ card.monster_type }}</span>
            <span v-else class="text-sm text-gray-600">-</span>
          </div>
        </div>

        <!-- Level -->
        <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
          <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">Level</span>
          <div class="px-3 py-2 flex-1">
            <InputNumber
              v-if="editing"
              v-model="form.level"
              :min="1"
              :max="12"
              :use-grouping="false"
              fluid
              size="small"
            />
            <span v-else-if="card.level != null" class="font-orbitron text-sm text-gray-200">{{ card.level }}</span>
            <span v-else class="text-sm text-gray-600">-</span>
          </div>
        </div>

        <!-- ATK / DEF (edit mode only — view mode has stat boxes above) -->
        <template v-if="editing">
          <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
            <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">ATK</span>
            <div class="px-3 py-2 flex-1">
              <InputText v-model="form.atk" fluid size="small" />
            </div>
          </div>
          <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
            <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">DEF</span>
            <div class="px-3 py-2 flex-1">
              <InputText v-model="form.defense" fluid size="small" />
            </div>
          </div>
        </template>
      </template>
    </div>

    <!-- Text sections -->
    <template v-for="section in textSections" :key="section.key">
      <template v-if="!section.monsterOnly || isMonster">
        <!-- View mode: only show if value exists -->
        <div v-if="!editing && (card as any)[section.key]" class="mb-3">
          <div class="font-orbitron text-[9px] font-bold tracking-[0.2em] text-gold-dim uppercase mb-1.5">{{ section.label }}</div>
          <p class="text-sm text-gray-300 leading-relaxed whitespace-pre-line bg-[rgba(201,168,76,0.03)] border border-[rgba(201,168,76,0.08)] rounded-md px-3 py-2">{{ (card as any)[section.key] }}</p>
        </div>

        <!-- Edit mode: show expanded or show + button -->
        <template v-if="editing">
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
              v-if="!(card as any)[section.key]"
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
    </template>

    <!-- Error message -->
    <div v-if="error" class="text-red-400 text-sm mb-3">{{ error }}</div>

    <!-- Action buttons -->
    <div v-if="editing" class="flex gap-2">
      <Button @click="saveEdit" :disabled="saving" severity="warn" fluid>
        {{ saving ? 'Saving...' : 'Save' }}
      </Button>
      <Button @click="cancelEdit" variant="outlined" severity="secondary" fluid>
        Cancel
      </Button>
    </div>
    <Button v-else @click="startEdit" variant="outlined" severity="secondary" fluid>
      Edit Card Info
    </Button>
  </div>
</template>
