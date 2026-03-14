<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { ScanResult, CardRawExtract } from '@/types/card'

const props = defineProps<{
  cardId: string
  rarity: string
  result: ScanResult | null
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  close: []
  refresh: []
}>()

// ── View mode ─────────────────────────────────────────────────────────────────
type ViewMode = 'translated' | 'raw'
const viewMode = ref<ViewMode>('translated')

// ── Dragging ──────────────────────────────────────────────────────────────────
const x = ref(Math.max(8, window.innerWidth - 448 - 372 - 16))
const y = ref(80)
const dragging = ref(false)
const dragOffsetX = ref(0)
const dragOffsetY = ref(0)

function onMouseDown(e: MouseEvent) {
  dragging.value = true
  dragOffsetX.value = e.clientX - x.value
  dragOffsetY.value = e.clientY - y.value
  e.preventDefault()
}
function onMouseMove(e: MouseEvent) {
  if (!dragging.value) return
  x.value = Math.max(0, Math.min(window.innerWidth - 372, e.clientX - dragOffsetX.value))
  y.value = Math.max(0, Math.min(window.innerHeight - 60, e.clientY - dragOffsetY.value))
}
function onMouseUp() { dragging.value = false }

onMounted(() => {
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
})
onUnmounted(() => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
})

// ── Copy helpers ──────────────────────────────────────────────────────────────
const copiedKey = ref<string | null>(null)

async function copyField(key: string, value: string) {
  await navigator.clipboard.writeText(value)
  copiedKey.value = key
  setTimeout(() => { copiedKey.value = null }, 1500)
}

async function copyAll() {
  if (!props.result) return
  const rows = viewMode.value === 'translated' ? translatedFields.value : rawFields.value
  const lines: string[] = []
  for (const f of rows) {
    const val = getValue(f.source, f.key)
    if (val !== null && val !== undefined && String(val) !== '') {
      lines.push(`【${f.label}】${displayValue(f.key, val)}`)
    }
  }
  await navigator.clipboard.writeText(lines.join('\n'))
  copiedKey.value = '__all__'
  setTimeout(() => { copiedKey.value = null }, 1500)
}

// ── Field definitions ─────────────────────────────────────────────────────────

interface FieldDef {
  key: string
  label: string
  source: string   // 'translated' | 'raw'
  show?: boolean
}

const isMonster = computed(() => {
  if (!props.result) return true
  const ct = props.result.card_type ?? props.result.raw?.card_type_jp ?? ''
  return ct.includes('怪獸') || ct.includes('モンスター')
})

const translatedFields = computed((): FieldDef[] => {
  const m = isMonster.value
  return [
    { key: 'name_zh',           label: '卡名（中）',    source: 'translated' },
    { key: 'name_jp',           label: '卡名（日）',    source: 'translated' },
    { key: 'card_type',         label: '卡牌種類',       source: 'translated' },
    { key: 'is_legend',         label: 'LEGEND',         source: 'translated' },
    { key: 'attribute',         label: '屬性',           source: 'translated', show: m },
    { key: 'monster_type',      label: '種族',           source: 'translated', show: m },
    { key: 'level',             label: '等級',           source: 'translated', show: m },
    { key: 'atk',               label: 'ATK',            source: 'translated', show: m },
    { key: 'defense',           label: 'DEF',            source: 'translated', show: m },
    { key: 'description',       label: 'Description',    source: 'translated' },
    { key: 'summon_condition',  label: 'Summon Cond.',   source: 'translated', show: m },
    { key: 'condition',         label: 'Condition',      source: 'translated' },
    { key: 'effect',            label: 'Effect',         source: 'translated' },
    { key: 'continuous_effect', label: 'Cont. Effect',   source: 'translated' },
  ].filter(f => f.show !== false)
})

const rawFields = computed((): FieldDef[] => {
  const m = isMonster.value
  return [
    { key: 'name_jp',               label: 'カード名',      source: 'raw' },
    { key: 'card_type_jp',          label: 'カード種類',    source: 'raw' },
    { key: 'is_legend',             label: 'LEGEND',        source: 'raw' },
    { key: 'attribute_jp',          label: '属性',          source: 'raw', show: m },
    { key: 'monster_type_jp',       label: '種族',          source: 'raw', show: m },
    { key: 'level',                 label: 'レベル',        source: 'raw', show: m },
    { key: 'atk',                   label: 'ATK',           source: 'raw', show: m },
    { key: 'defense',               label: 'DEF',           source: 'raw', show: m },
    { key: 'description_jp',        label: '説明文',        source: 'raw' },
    { key: 'summon_condition_jp',   label: '召喚条件',      source: 'raw', show: m },
    { key: 'condition_jp',          label: '発動条件',      source: 'raw' },
    { key: 'effect_jp',             label: '効果',          source: 'raw' },
    { key: 'continuous_effect_jp',  label: '永続効果',      source: 'raw' },
  ].filter(f => f.show !== false)
})

const activeFields = computed(() =>
  viewMode.value === 'translated' ? translatedFields.value : rawFields.value
)

function getValue(source: string, key: string): any {
  if (!props.result) return null
  if (source === 'raw') return (props.result.raw as any)?.[key] ?? null
  return (props.result as any)[key] ?? null
}

function displayValue(key: string, value: any): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? '✔ YES' : 'NO'
  return String(value)
}

function hasValue(value: any): boolean {
  return value !== null && value !== undefined && value !== ''
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed z-[90] w-[372px] bg-gray-800 border border-gray-600 rounded-xl shadow-2xl flex flex-col select-none"
      :style="{ left: `${x}px`, top: `${y}px` }"
    >
      <!-- Header (drag handle) -->
      <div
        class="flex items-center justify-between px-4 py-2.5 bg-gray-700/80 rounded-t-xl cursor-grab active:cursor-grabbing border-b border-gray-600"
        @mousedown="onMouseDown"
      >
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 text-yellow-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
          </svg>
          <span class="text-sm font-semibold text-gray-100">AI 掃描結果</span>
          <span class="text-xs text-gray-400 font-mono">{{ rarity }}</span>
        </div>
        <div class="flex items-center gap-1">
          <!-- Refresh -->
          <button
            @click.stop="emit('refresh')"
            :disabled="loading"
            title="重新掃描"
            class="p-1.5 rounded text-gray-400 hover:text-yellow-400 hover:bg-gray-600 transition-colors disabled:opacity-40"
          >
            <svg class="w-4 h-4" :class="{ 'animate-spin': loading }"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
          </button>
          <!-- Close -->
          <button
            @click.stop="emit('close')"
            title="關閉"
            class="p-1.5 rounded text-gray-400 hover:text-gray-100 hover:bg-gray-600 transition-colors"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- View mode tabs (only when result exists) -->
      <div v-if="result && !loading" class="flex border-b border-gray-700">
        <button
          @click="viewMode = 'translated'"
          class="flex-1 py-1.5 text-xs font-medium transition-colors"
          :class="viewMode === 'translated'
            ? 'text-yellow-400 border-b-2 border-yellow-400 -mb-px bg-gray-750'
            : 'text-gray-500 hover:text-gray-300'"
        >
          繁體中文
        </button>
        <button
          @click="viewMode = 'raw'"
          class="flex-1 py-1.5 text-xs font-medium transition-colors"
          :class="viewMode === 'raw'
            ? 'text-blue-400 border-b-2 border-blue-400 -mb-px'
            : 'text-gray-500 hover:text-gray-300'"
        >
          原始日文
        </button>
      </div>

      <!-- Body -->
      <div class="overflow-y-auto max-h-[68vh] px-4 py-3 space-y-1">

        <!-- Loading -->
        <div v-if="loading" class="flex flex-col items-center justify-center py-10 gap-3">
          <div class="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
          <div class="text-center">
            <p class="text-sm text-gray-400">呼叫 OpenAI 中…</p>
            <p class="text-xs text-gray-600 mt-1">Phase 1: OCR → Phase 2: 翻譯</p>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="error" class="py-6 text-center">
          <p class="text-red-400 text-sm whitespace-pre-wrap">{{ error }}</p>
        </div>

        <!-- Results -->
        <template v-else-if="result">
          <div
            v-for="field in activeFields"
            :key="`${viewMode}-${field.key}`"
            class="group flex items-start gap-2 rounded-lg px-2 py-1.5 hover:bg-gray-700/50 transition-colors"
          >
            <!-- Label -->
            <span class="w-24 shrink-0 text-xs text-gray-500 pt-0.5 leading-tight">{{ field.label }}</span>

            <!-- Value -->
            <span
              class="flex-1 text-sm leading-relaxed whitespace-pre-line break-words"
              :class="hasValue(getValue(field.source, field.key)) ? 'text-gray-200' : 'text-gray-600'"
            >
              {{ displayValue(field.key, getValue(field.source, field.key)) }}
            </span>

            <!-- Copy button -->
            <button
              v-if="hasValue(getValue(field.source, field.key))"
              @click="copyField(`${viewMode}-${field.key}`, displayValue(field.key, getValue(field.source, field.key)))"
              class="shrink-0 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity text-gray-500 hover:text-yellow-400"
              title="複製"
            >
              <svg v-if="copiedKey === `${viewMode}-${field.key}`"
                   class="w-3.5 h-3.5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
              <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184" />
              </svg>
            </button>
          </div>
        </template>

        <!-- Empty -->
        <div v-else class="py-8 text-center text-gray-600 text-sm">
          點擊 Scan 按鈕開始掃描
        </div>
      </div>

      <!-- Footer: Copy All -->
      <div v-if="result && !loading" class="px-4 py-2.5 border-t border-gray-700">
        <button
          @click="copyAll"
          class="w-full py-1.5 text-xs font-medium rounded-lg transition-colors"
          :class="copiedKey === '__all__'
            ? 'bg-green-600/80 text-white'
            : 'bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-gray-100'"
        >
          <span v-if="copiedKey === '__all__'">✔ 已複製全部</span>
          <span v-else>複製目前頁面所有欄位</span>
        </button>
      </div>
    </div>
  </Teleport>
</template>
