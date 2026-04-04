<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import type { Card, CardUpdate, ScanResult } from '@/types/card'
import { variantKey, parseRarityKey } from '@/types/card'
import { getCardImageUrl, updateOwnership, updateCard, uploadCardImage, revertCardImage, fetchKonamiImage, addVariant, editVariantRarity, deleteVariant, scanCard } from '@/api/cards'
import { RARITIES } from '@/constants/rarities'
import { useUiStore } from '@/stores/ui'
import { useCardSetsStore } from '@/stores/cardSets'
import { useRoute, useRouter } from 'vue-router'
import RarityTabs from '@/components/cards/RarityTabs.vue'
import OwnershipControl from '@/components/cards/OwnershipControl.vue'
import ScanResultPanel from '@/components/detail/ScanResultPanel.vue'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
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
const cardSetsStore = useCardSetsStore()
const route = useRoute()
const router = useRouter()

const isOnCardSet = computed(() => route.params.setId === props.card.set_id)

const currentRarity = ref(props.activeRarity)
// Sidebar → outside: keep ui.sidebarRarity in sync so CardGridItem/CardTable can follow
watch(currentRarity, (r) => { ui.sidebarRarity = r })
// Outside → sidebar: when grid/table changes rarity, prop updates and we follow
watch(() => props.activeRarity, (r) => { currentRarity.value = r })
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
const isMaximum = computed(() => {
  const ct = editing.value ? (form.card_type ?? props.card.card_type) : props.card.card_type
  return ct.includes('巨極')
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
    maximum_atk: c.maximum_atk,
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
      form.maximum_atk = null
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
  props.card.variants.find(v => variantKey(v) === currentRarity.value) ?? props.card.variants[0]
)

// Image cache buster — set after upload/revert to force browser reload
const imageCacheBuster = ref(0)

const imageUrl = computed(() => {
  if (!activeVariant.value) return ''
  const base = getCardImageUrl(props.card.card_id, currentRarity.value)
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
const fetchingKonami = ref(false)
const imageError = ref('')

function triggerFileSelect() {
  fileInput.value?.click()
}

async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!currentRarity.value) {
    imageError.value = '無效的稀有度，請重新開啟側欄'
    input.value = ''
    return
  }

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

async function onFetchKonami() {
  fetchingKonami.value = true
  imageError.value = ''
  try {
    const updated = await fetchKonamiImage(props.card.card_id, currentRarity.value)
    const v = props.card.variants.find(v => v.rarity === currentRarity.value)
    if (v) {
      v.image_source = updated.image_source
      v.image_path = updated.image_path
    }
    imageCacheBuster.value = Date.now()
    ui.markImageUpdated(props.card.card_id, currentRarity.value)
    emit('cardUpdated')
  } catch (e: any) {
    const detail = e?.response?.data?.detail ?? ''
    imageError.value = detail === 'Image not found on Konami CDN'
      ? 'Konami CDN 上找不到此圖片'
      : (detail || 'Fetch failed')
  } finally {
    fetchingKonami.value = false
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

async function onOwnershipUpdate(cardId: string, rarityKey: string, count: number) {
  await updateOwnership(cardId, rarityKey, count)
  const v = props.card.variants.find(v => v.card_id === cardId && variantKey(v) === rarityKey)
  if (v) v.owned_count = count
  cardSetsStore.patchVariantOwnership(cardId, rarityKey, count)
}

// Text section definitions for DRY rendering
const textSections = computed(() => [
  { key: 'description' as const, label: 'Description', monsterOnly: false },
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

// ── Copy card ID ──────────────────────────────────────────────────────────────
const copiedId = ref(false)

function copyCardId() {
  navigator.clipboard.writeText(props.card.card_id)
  copiedId.value = true
  setTimeout(() => { copiedId.value = false }, 1500)
}

// ---- Variant management ----

// Rarities where at least one slot (normal or alt) is still available
const availableRarities = computed(() =>
  RARITIES.filter(r => {
    const hasNormal = props.card.variants.some(v => v.rarity === r.value && !v.is_alternate_art)
    const hasAlt = props.card.variants.some(v => v.rarity === r.value && v.is_alternate_art)
    return !hasNormal || !hasAlt
  })
)

// ---- Add Variant ----
const addingVariant = ref(false)
const newVariantRarity = ref('')
const newVariantIsAlt = ref(false)
const savingVariant = ref(false)
const variantError = ref('')

// Whether the selected rarity forces alt art (normal slot already taken)
const newVariantAltForced = computed(() =>
  props.card.variants.some(v => v.rarity === newVariantRarity.value && !v.is_alternate_art)
)

// Watch: auto-adjust alt flag when user changes the rarity selection
watch(newVariantRarity, (r) => {
  const hasNormal = props.card.variants.some(v => v.rarity === r && !v.is_alternate_art)
  const hasAlt = props.card.variants.some(v => v.rarity === r && v.is_alternate_art)
  if (hasNormal && !hasAlt) {
    // Normal exists, alt doesn't → must be alt
    newVariantIsAlt.value = true
  } else if (!hasNormal) {
    // Normal doesn't exist → default to normal
    newVariantIsAlt.value = false
  }
  // If only alt exists → default to normal (add the missing normal slot)
})

function startAddVariant() {
  const first = availableRarities.value[0]
  if (!first) return
  newVariantRarity.value = first.value
  // Trigger the watch logic for initial selection
  const hasNormal = props.card.variants.some(v => v.rarity === first.value && !v.is_alternate_art)
  newVariantIsAlt.value = hasNormal
  variantError.value = ''
  addingVariant.value = true
  editingRarity.value = false
  confirmingDelete.value = false
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
    await addVariant(props.card.card_id, {
      rarity: newVariantRarity.value,
      is_alternate_art: newVariantIsAlt.value,
    })
    addingVariant.value = false
    currentRarity.value = newVariantIsAlt.value
      ? `${newVariantRarity.value}-alt`
      : newVariantRarity.value
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

const editingIsAlt = computed(() => parseRarityKey(currentRarity.value).isAlt)

const editableRarities = computed(() => {
  const currentBase = parseRarityKey(currentRarity.value).rarity
  return RARITIES.filter(r => {
    if (r.value === currentBase) return false
    // Exclude rarities where the same (rarity, alt flag) slot is already taken
    return !props.card.variants.some(
      v => v.rarity === r.value && v.is_alternate_art === editingIsAlt.value
    )
  })
})

function startEditRarity() {
  editRarityTarget.value = editableRarities.value[0]?.value ?? ''
  rarityEditError.value = ''
  editingRarity.value = true
  addingVariant.value = false
  confirmingDelete.value = false
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
    ui.sidebarRarity = editRarityTarget.value
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
  addingVariant.value = false
  editingRarity.value = false
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
    const remaining = props.card.variants.filter(v => variantKey(v) !== currentRarity.value)
    if (remaining.length > 0 && remaining[0]) currentRarity.value = variantKey(remaining[0])
  } catch (e: any) {
    deleteError.value = e?.response?.data?.detail ?? 'Failed to delete variant'
  } finally {
    deletingVariant.value = false
  }
}
</script>

<template>
  <div class="p-5">
    <!-- Image with upload overlay + corner action buttons -->
    <!-- outer: no overflow-hidden so tooltips can escape; inner div clips the image -->
    <div class="relative group aspect-[59/86] bg-gray-700 rounded-lg mb-3">
      <!-- Image + upload overlay (clipped to rounded corners) -->
      <div class="absolute inset-0 rounded-lg overflow-hidden">
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
      </div>

      <!-- Hidden file input -->
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="onFileSelected"
      />

      <!-- Revert to original — bottom-left corner, tooltip opens upward -->
      <div v-if="isUserUpload" class="absolute bottom-2 left-2 group/tip z-10">
        <button
          @click="onRevertImage"
          :disabled="reverting"
          class="w-7 h-7 rounded-md border border-white/20 bg-black/50 text-white/70 cursor-pointer flex items-center justify-center transition-colors hover:bg-black/70 hover:text-white shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <svg v-if="reverting" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3" />
          </svg>
        </button>
        <div class="absolute bottom-[calc(100%+6px)] left-0 bg-[#2e2e4a] border border-white/20 text-[#e0e0e0] text-[11px] px-2 py-[3px] rounded-[5px] whitespace-nowrap pointer-events-none opacity-0 group-hover/tip:opacity-100 transition-opacity z-20">
          Revert to original
        </div>
      </div>

      <!-- Fetch from Konami — bottom-right, left of Scan -->
      <div class="absolute bottom-2 right-11 group/tip z-10">
        <button
          @click="onFetchKonami"
          :disabled="fetchingKonami"
          class="w-7 h-7 rounded-md border border-white/20 bg-black/50 text-white/70 cursor-pointer flex items-center justify-center transition-colors hover:bg-black/70 hover:text-white shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <svg v-if="fetchingKonami" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
          </svg>
        </button>
        <div class="absolute bottom-[calc(100%+6px)] right-0 bg-[#2e2e4a] border border-white/20 text-[#e0e0e0] text-[11px] px-2 py-[3px] rounded-[5px] whitespace-nowrap pointer-events-none opacity-0 group-hover/tip:opacity-100 transition-opacity z-20">
          Fetch from Konami
        </div>
      </div>

      <!-- Scan — bottom-right corner, tooltip opens upward -->
      <div class="absolute bottom-2 right-2 group/tip z-10">
        <button
          @click="triggerScan"
          :disabled="scanLoading"
          class="w-7 h-7 rounded-md border border-white/20 bg-black/50 text-white/70 cursor-pointer flex items-center justify-center transition-colors hover:bg-black/70 hover:text-white shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <svg v-if="scanLoading" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
          </svg>
        </button>
        <div class="absolute bottom-[calc(100%+6px)] right-0 bg-[#2e2e4a] border border-white/20 text-[#e0e0e0] text-[11px] px-2 py-[3px] rounded-[5px] whitespace-nowrap pointer-events-none opacity-0 group-hover/tip:opacity-100 transition-opacity z-20">
          Scan with AI
        </div>
      </div>
    </div>

    <!-- Image error -->
    <div v-if="imageError" class="text-[11px] text-red-400 mb-2">{{ imageError }}</div>

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

    <!-- ── Rarity row ── -->
    <div class="flex items-center gap-1.5 pb-2.5 border-b border-white/[0.08] mb-3">
      <!-- Rarity tabs: max-w-[40%] caps the area; natural width when fewer tabs fit -->
      <div class="max-w-[40%] min-w-0">
        <RarityTabs
          align="start"
          :variants="card.variants"
          :active-rarity="currentRarity"
          @select="currentRarity = $event"
        />
      </div>

      <!-- Vertical separator -->
      <div class="w-px h-4 bg-white/15 mx-0.5 shrink-0" />

      <!-- Add rarity icon button -->
      <div v-if="availableRarities.length > 0 && !editing" class="relative group/tip">
        <button
          @click="startAddVariant"
          class="w-7 h-7 rounded-md border border-white/20 bg-white/[0.08] text-white/70 cursor-pointer flex items-center justify-center transition-colors hover:bg-white/[0.16] hover:text-white shrink-0"
        >
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <line x1="8" y1="3" x2="8" y2="13"/><line x1="3" y1="8" x2="13" y2="8"/>
          </svg>
        </button>
        <div class="absolute top-[calc(100%+6px)] left-1/2 -translate-x-1/2 bg-[#2e2e4a] border border-white/20 text-[#e0e0e0] text-[11px] px-2 py-[3px] rounded-[5px] whitespace-nowrap pointer-events-none opacity-0 group-hover/tip:opacity-100 transition-opacity z-20">
          Add rarity
        </div>
      </div>

      <!-- Edit rarity icon button -->
      <div v-if="editableRarities.length > 0 && !editing" class="relative group/tip">
        <button
          @click="startEditRarity"
          class="w-7 h-7 rounded-md border border-white/20 bg-white/[0.08] text-white/70 cursor-pointer flex items-center justify-center transition-colors hover:bg-white/[0.16] hover:text-white shrink-0"
        >
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 2l3 3-8 8H3v-3L11 2z"/>
          </svg>
        </button>
        <div class="absolute top-[calc(100%+6px)] left-1/2 -translate-x-1/2 bg-[#2e2e4a] border border-white/20 text-[#e0e0e0] text-[11px] px-2 py-[3px] rounded-[5px] whitespace-nowrap pointer-events-none opacity-0 group-hover/tip:opacity-100 transition-opacity z-20">
          Edit rarity
        </div>
      </div>

      <!-- Delete variant icon button (only when >1 variant) -->
      <div v-if="card.variants.length > 1 && !editing" class="relative group/tip">
        <button
          @click="startDeleteVariant"
          class="w-7 h-7 rounded-md border border-[rgba(248,113,113,0.35)] bg-transparent text-[rgba(248,113,113,0.7)] cursor-pointer flex items-center justify-center transition-colors hover:bg-[rgba(248,113,113,0.12)] hover:text-[#f87171] shrink-0"
        >
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 4 13 4"/><path d="M5 4V3h6v1"/><rect x="4" y="5" width="8" height="9" rx="1"/>
            <line x1="6.5" y1="7.5" x2="6.5" y2="11.5"/><line x1="9.5" y1="7.5" x2="9.5" y2="11.5"/>
          </svg>
        </button>
        <div class="absolute top-[calc(100%+6px)] left-1/2 -translate-x-1/2 bg-[#2e2e4a] border border-white/20 text-[#e0e0e0] text-[11px] px-2 py-[3px] rounded-[5px] whitespace-nowrap pointer-events-none opacity-0 group-hover/tip:opacity-100 transition-opacity z-20">
          Delete
        </div>
      </div>

      <!-- Spacer -->
      <div class="flex-1" />

      <!-- Ownership quantity control -->
      <OwnershipControl
        :card-id="card.card_id"
        :rarity="currentRarity"
        :owned-count="activeVariant?.owned_count ?? 0"
        @update="onOwnershipUpdate"
      />
    </div>

    <!-- Variant management forms (inline, below rarity row) -->
    <div v-if="addingVariant || editingRarity || confirmingDelete" class="mb-3 space-y-1.5">
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
        <!-- Alt-art checkbox row -->
        <div class="flex items-center gap-2 pl-0.5">
          <Checkbox
            v-model="newVariantIsAlt"
            :binary="true"
            :disabled="newVariantAltForced"
            inputId="new-variant-alt"
          />
          <label
            for="new-variant-alt"
            class="text-xs select-none"
            :class="newVariantAltForced ? 'text-gray-500 cursor-default' : 'text-gray-300 cursor-pointer'"
          >
            異圖
            <span v-if="newVariantAltForced" class="text-gray-500">（此貴罕度已有普通版，自動設為異圖）</span>
          </label>
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
          <span class="text-xs text-gray-300">刪除 <strong>{{ activeVariant?.is_alternate_art ? `${activeVariant.rarity} ★` : currentRarity }}</strong>？</span>
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
    </div>

    <!-- ── Card header ── -->
    <template v-if="editing">
      <div class="mb-4 space-y-1.5">
        <InputText v-model="form.name_zh" placeholder="Chinese Name" fluid size="small" />
        <InputText v-model="form.name_jp" placeholder="Japanese Name" fluid size="small" />
      </div>
    </template>
    <template v-else>
      <!-- Card ID row -->
      <div class="flex items-center gap-1.5 mb-1">
        <span class="font-mono text-xs text-white/40 tracking-[0.03em] flex-1">{{ card.card_id }}</span>
        <span v-if="card.is_legend" class="bg-amber-500/90 text-black text-[10px] font-bold px-1.5 py-0.5 rounded">LEGEND</span>
        <Button
          v-if="!isOnCardSet"
          @click="router.push('/set/' + card.set_id)"
          size="small"
          severity="secondary"
          variant="text"
          class="!text-[10px] !px-1.5 !py-0.5 !h-auto font-mono text-gold-dim hover:text-gold-light"
          :title="'前往 ' + card.set_id + ' 卡組頁'"
        >{{ card.set_id }}</Button>
        <Button
          @click="copyCardId"
          variant="text"
          severity="secondary"
          size="small"
          class="shrink-0 p-0"
          :title="copiedId ? '已複製！' : '複製編號'"
        >
          <svg v-if="copiedId" class="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
          </svg>
        </Button>
      </div>

      <!-- Card name -->
      <h2 class="font-cinzel text-lg font-bold text-gray-100 leading-snug mb-0.5">
        {{ card.name_zh || card.name_jp }}
      </h2>
      <p v-if="card.name_zh && card.name_jp" class="text-xs text-gray-500 font-orbitron tracking-wide mb-4">
        {{ card.name_jp }}
      </p>
      <div v-else class="mb-4" />
    </template>

    <!-- ── ATK / DEF stat boxes (view mode, monsters only) ── -->
    <div v-if="!editing && isMonster && (card.atk != null || card.defense != null)" class="grid grid-cols-2 gap-2 mb-2">
      <div class="rounded-lg border border-[rgba(220,50,50,0.3)] bg-[rgba(220,50,50,0.18)] px-3 py-2 flex items-center justify-between">
        <span class="font-orbitron text-[10px] font-bold tracking-[0.08em] text-white/40 uppercase">ATK</span>
        <span class="font-orbitron text-xl font-medium text-[#f87171] leading-none">{{ card.atk ?? '?' }}</span>
      </div>
      <div class="rounded-lg border border-[rgba(50,80,200,0.35)] bg-[rgba(50,80,200,0.20)] px-3 py-2 flex items-center justify-between">
        <span class="font-orbitron text-[10px] font-bold tracking-[0.08em] text-white/40 uppercase">DEF</span>
        <span class="font-orbitron text-xl font-medium text-[#93c5fd] leading-none">{{ card.defense ?? '?' }}</span>
      </div>
    </div>

    <!-- ── MAXIMUM ATK (view mode, 巨極 only) ── -->
    <div v-if="!editing && isMaximum && card.maximum_atk != null" class="rounded-lg border border-[rgba(180,130,0,0.3)] bg-[rgba(160,110,0,0.18)] px-3 py-2 mb-3 flex items-center justify-between">
      <span class="font-orbitron text-[10px] font-bold tracking-[0.08em] text-[rgba(200,150,0,0.7)] uppercase">Maximum ATK</span>
      <span class="font-orbitron text-xl font-medium text-[#fbbf24] leading-none">{{ card.maximum_atk }}</span>
    </div>

    <!-- ── Info grid (view mode) ── -->
    <div v-if="!editing" class="grid grid-cols-3 gap-1.5 mb-3">
      <!-- Type — full width -->
      <div class="col-span-3 bg-white/[0.05] border border-white/[0.07] rounded-[7px] px-2.5 py-1.5">
        <div class="text-[10px] text-white/35 uppercase tracking-[0.04em] mb-[2px]">Type</div>
        <div class="text-[13px] text-[#ddd]">{{ card.card_type }}</div>
      </div>
      <!-- Monster-only: 屬性 / 種族 / Level -->
      <template v-if="isMonster">
        <div class="bg-white/[0.05] border border-white/[0.07] rounded-[7px] px-2.5 py-1.5">
          <div class="text-[10px] text-white/35 uppercase tracking-[0.04em] mb-[2px]">屬性</div>
          <div class="text-[13px] text-[#ddd]">{{ card.attribute || '–' }}</div>
        </div>
        <div class="bg-white/[0.05] border border-white/[0.07] rounded-[7px] px-2.5 py-1.5">
          <div class="text-[10px] text-white/35 uppercase tracking-[0.04em] mb-[2px]">種族</div>
          <div class="text-[13px] text-[#ddd]">{{ card.monster_type || '–' }}</div>
        </div>
        <div class="bg-white/[0.05] border border-white/[0.07] rounded-[7px] px-2.5 py-1.5">
          <div class="text-[10px] text-white/35 uppercase tracking-[0.04em] mb-[2px]">Level</div>
          <div class="text-[13px] text-[#ddd]">{{ card.level ?? '–' }}</div>
        </div>
      </template>
    </div>

    <!-- ── Edit mode: detail table ── -->
    <div v-if="editing" class="rounded-lg overflow-hidden mb-4 border border-[rgba(201,168,76,0.1)]">
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
            v-model="form.card_type"
            :options="cardTypeOptions"
            option-label="label"
            option-value="value"
            size="small"
            class="w-full"
          />
        </div>
      </div>

      <!-- Monster-only fields -->
      <template v-if="isMonster">
        <!-- Attribute -->
        <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
          <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">屬性</span>
          <div class="px-3 py-2 flex-1">
            <Select
              v-model="form.attribute"
              :options="attributeOptions"
              option-label="label"
              option-value="value"
              size="small"
              class="w-full"
            />
          </div>
        </div>

        <!-- Monster Type -->
        <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
          <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">種族</span>
          <div class="px-3 py-2 flex-1">
            <InputText
              v-model="form.monster_type"
              placeholder="e.g. 龍族"
              fluid
              size="small"
            />
          </div>
        </div>

        <!-- Level -->
        <div class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
          <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold-dim bg-[rgba(201,168,76,0.04)]">Level</span>
          <div class="px-3 py-2 flex-1">
            <InputNumber
              v-model="form.level"
              :min="1"
              :max="12"
              :use-grouping="false"
              fluid
              size="small"
            />
          </div>
        </div>

        <!-- ATK / DEF / MAX ATK -->
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
        <div v-if="isMaximum" class="flex items-center border-b border-[rgba(201,168,76,0.08)]">
          <span class="w-20 shrink-0 px-3 py-2 text-[11px] font-orbitron font-bold tracking-wide text-gold bg-[rgba(201,168,76,0.04)]">MAX ATK</span>
          <div class="px-3 py-2 flex-1">
            <InputText v-model="form.maximum_atk" fluid size="small" />
          </div>
        </div>
      </template>
    </div>

    <!-- ── Text sections ── -->
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
