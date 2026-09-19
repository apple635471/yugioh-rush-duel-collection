<script setup lang="ts">
/**
 * 產品分類規則編輯器。
 *
 * 卡組不存自己的分類——屬於哪一類完全由這裡的規則算出來，所以改一條規則
 * 就等於把所有卡組重新分類一次，沒有東西需要遷移。爬蟲也讀同一份規則。
 */
import { ref, computed } from 'vue'
import { useCardSetsStore } from '@/stores/cardSets'
import {
  createProductType,
  deleteProductType,
  previewRules,
  reorderProductTypes,
  updateProductType,
  type ProductTypeDraft,
} from '@/api/productTypes'
import type { ProductType } from '@/types/cardSet'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import AppButton from '@/components/ui/AppButton.vue'

const emit = defineEmits<{
  /** 規則變了：卡組的分類跟著變，外面要重抓清單 */
  changed: []
}>()

const store = useCardSetsStore()

const visible = ref(false)
const saving = ref(false)
const error = ref('')

/** 正在編輯的代號；'' = 沒有，'__new__' = 新增中 */
const editingCode = ref('')
const draft = ref<ProductTypeDraft>(emptyDraft())
const preview = ref<{ count: number; sample: string[]; elsewhere: string[] } | null>(null)

const types = computed(() => store.productTypes)

function emptyDraft(): ProductTypeDraft {
  return { code: '', name_en: '', name_zh: null, group_label: '其他', color: '#8C90A3', rules: [''] }
}

function open() {
  editingCode.value = ''
  error.value = ''
  visible.value = true
  store.loadProductTypes()
}

function startEdit(pt: ProductType) {
  editingCode.value = pt.code
  error.value = ''
  preview.value = null
  draft.value = {
    code: pt.code,
    name_en: pt.name_en,
    name_zh: pt.name_zh ?? null,
    group_label: pt.group_label,
    color: pt.color,
    rules: pt.rules.length ? [...pt.rules] : [''],
  }
}

function startCreate() {
  editingCode.value = '__new__'
  error.value = ''
  preview.value = null
  draft.value = emptyDraft()
}

function cancelEdit() {
  editingCode.value = ''
  preview.value = null
  error.value = ''
}

const editingType = computed(() => types.value.find(t => t.code === editingCode.value))
const isFallback = computed(() => editingType.value?.is_fallback === true)

function cleanRules(): string[] {
  return draft.value.rules.map(r => r.trim()).filter(Boolean)
}

/** 套用回傳的清單並通知外面重抓卡組 */
function applyResult(list: ProductType[]) {
  store.setProductTypes(list)
  emit('changed')
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = { ...draft.value, rules: isFallback.value ? [] : cleanRules() }
    const list = editingCode.value === '__new__'
      ? await createProductType(payload)
      : await updateProductType(editingCode.value, payload)
    applyResult(list)
    editingCode.value = ''
    preview.value = null
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? '儲存失敗'
  } finally {
    saving.value = false
  }
}

async function remove(pt: ProductType) {
  if (!confirm(`刪除「${pt.name_en}」？它現在的 ${pt.set_count} 個卡組會落到其他規則或 fallback。`)) return
  saving.value = true
  error.value = ''
  try {
    applyResult(await deleteProductType(pt.code))
    if (editingCode.value === pt.code) editingCode.value = ''
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? '刪除失敗'
  } finally {
    saving.value = false
  }
}

async function move(index: number, delta: number) {
  const codes = types.value.map(t => t.code)
  const target = index + delta
  if (target < 0 || target >= codes.length) return
  ;[codes[index], codes[target]] = [codes[target]!, codes[index]!]
  saving.value = true
  try {
    applyResult(await reorderProductTypes(codes))
  } finally {
    saving.value = false
  }
}

/** 試算：這些規則會抓到哪些卡組，其中哪些目前歸在別類 */
async function runPreview() {
  const patterns = cleanRules()
  if (!patterns.length) {
    preview.value = { count: 0, sample: [], elsewhere: [] }
    return
  }
  const result = await previewRules(patterns)
  const elsewhere = result.set_ids.filter(
    id => result.claimed_elsewhere[id] && result.claimed_elsewhere[id] !== editingCode.value,
  )
  preview.value = {
    count: result.set_ids.length,
    sample: result.set_ids.slice(0, 24),
    elsewhere: elsewhere.slice(0, 12),
  }
}

defineExpose({ open })
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="分類規則"
    :style="{ width: '46rem', maxWidth: '94vw' }"
  >
    <p class="text-[11px] leading-relaxed text-gray-400 mb-3">
      卡組屬於哪一類，完全由這裡的規則算出來（卡組本身不存分類），所以改完立刻重新分類，
      爬蟲也讀同一份規則。規則是<b class="text-gray-200">正規表示式</b>，比對卡組編號、不分大小寫；
      沒加 <code class="text-gold/80">^</code> <code class="text-gold/80">$</code> 就是「包含」。
      由上往下比對，<b class="text-gray-200">第一個符合的類型勝出</b>。
    </p>

    <div v-if="error" class="mb-3 rounded border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-300">
      {{ error }}
    </div>

    <div class="flex flex-col divide-y divide-[rgba(201,168,76,0.1)] border border-[rgba(201,168,76,0.14)] rounded-lg overflow-hidden">
      <template v-for="(pt, i) in types" :key="pt.code">
        <!-- 一列：代號、名稱、規則、卡組數 -->
        <div class="flex items-center gap-2 px-3 py-2 text-xs bg-dark-2/40">
          <span class="h-3 w-3 shrink-0 rounded-sm" :style="{ background: pt.color }" />
          <span class="font-orbitron text-[11px] text-gold/90 w-40 shrink-0 truncate">{{ pt.code }}</span>
          <span class="w-44 shrink-0 truncate text-gray-200">
            {{ pt.name_en }}<span v-if="pt.name_zh" class="text-gray-400"> · {{ pt.name_zh }}</span>
          </span>
          <span class="flex-1 min-w-0 flex flex-wrap gap-1">
            <code
              v-for="rule in pt.rules"
              :key="rule"
              class="rounded bg-[rgba(201,168,76,0.1)] px-1 text-[10px] text-gold-light"
            >{{ rule }}</code>
            <span v-if="pt.is_fallback" class="text-[10px] text-gray-400 italic">
              沒被認領的卡組都進這裡
            </span>
          </span>
          <span class="font-orbitron text-[10px] text-gray-400 w-10 text-right shrink-0">{{ pt.set_count }}</span>
          <span class="flex items-center gap-0.5 shrink-0">
            <Button text severity="secondary" size="small" class="!p-1 !text-gray-400" title="上移"
                    :disabled="i === 0" @click="move(i, -1)">▲</Button>
            <Button text severity="secondary" size="small" class="!p-1 !text-gray-400" title="下移"
                    :disabled="i === types.length - 1" @click="move(i, 1)">▼</Button>
            <Button text severity="secondary" size="small" class="!p-1 !text-xs !text-gold/80"
                    @click="startEdit(pt)">編輯</Button>
            <Button v-if="!pt.is_fallback" text severity="danger" size="small" class="!p-1 !text-xs"
                    @click="remove(pt)">刪除</Button>
          </span>
        </div>

        <!-- 展開的編輯表單 -->
        <div v-if="editingCode === pt.code" class="px-3 py-3 bg-dark-1/60 flex flex-col gap-2">
          <div class="flex flex-wrap gap-2">
            <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
              代號 <InputText v-model="draft.code" size="small" class="w-36 text-xs" :disabled="pt.is_fallback" />
            </label>
            <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
              英文名 <InputText v-model="draft.name_en" size="small" class="w-40 text-xs" />
            </label>
            <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
              中文名 <InputText v-model="draft.name_zh as string" size="small" class="w-32 text-xs" />
            </label>
            <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
              分組 <InputText v-model="draft.group_label" size="small" class="w-28 text-xs" />
            </label>
            <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
              顏色 <input v-model="draft.color" type="color" class="h-7 w-10 rounded border border-[rgba(201,168,76,0.2)] bg-transparent">
            </label>
          </div>

          <div v-if="!pt.is_fallback" class="flex flex-col gap-1.5">
            <div class="text-[11px] text-gray-400">規則（由上往下比對）</div>
            <div v-for="(_, ri) in draft.rules" :key="ri" class="flex items-center gap-1.5">
              <InputText v-model="draft.rules[ri]" size="small" class="w-64 font-orbitron !text-xs"
                         placeholder="例：^KP\d" />
              <Button text severity="danger" size="small" class="!p-1 !text-xs"
                      @click="draft.rules.splice(ri, 1)">移除</Button>
            </div>
            <div class="flex items-center gap-2">
              <Button text severity="secondary" size="small" class="!p-1 !text-xs !text-gold/80"
                      @click="draft.rules.push('')">+ 新增規則</Button>
              <Button text severity="secondary" size="small" class="!p-1 !text-xs !text-gray-300"
                      @click="runPreview">試算</Button>
            </div>
            <div v-if="preview" class="text-[11px] text-gray-400 leading-relaxed">
              符合 <b class="text-gray-200">{{ preview.count }}</b> 個卡組：
              <span class="font-orbitron text-[10px] text-gold-light">{{ preview.sample.join(' ') }}</span>
              <span v-if="preview.count > preview.sample.length"> …</span>
              <span v-if="preview.elsewhere.length" class="block text-amber-400/80">
                其中 {{ preview.elsewhere.length }} 個目前被排在前面的類型認領：{{ preview.elsewhere.join(' ') }}
              </span>
            </div>
          </div>

          <div class="flex justify-end gap-2">
            <AppButton label="取消" variant="text" @click="cancelEdit" />
            <AppButton label="儲存" variant="filled" tone="gold" :disabled="saving" @click="save" />
          </div>
        </div>
      </template>

      <!-- 新增分類 -->
      <div v-if="editingCode === '__new__'" class="px-3 py-3 bg-dark-1/60 flex flex-col gap-2">
        <div class="flex flex-wrap gap-2">
          <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
            代號 <InputText v-model="draft.code" size="small" class="w-36 text-xs" placeholder="character_pack" />
          </label>
          <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
            英文名 <InputText v-model="draft.name_en" size="small" class="w-40 text-xs" />
          </label>
          <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
            中文名 <InputText v-model="draft.name_zh as string" size="small" class="w-32 text-xs" />
          </label>
          <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
            分組 <InputText v-model="draft.group_label" size="small" class="w-28 text-xs" />
          </label>
          <label class="flex items-center gap-1.5 text-[11px] text-gray-400">
            顏色 <input v-model="draft.color" type="color" class="h-7 w-10 rounded border border-[rgba(201,168,76,0.2)] bg-transparent">
          </label>
        </div>
        <div class="flex flex-col gap-1.5">
          <div class="text-[11px] text-gray-400">規則（由上往下比對）</div>
          <div v-for="(_, ri) in draft.rules" :key="ri" class="flex items-center gap-1.5">
            <InputText v-model="draft.rules[ri]" size="small" class="w-64 font-orbitron !text-xs" placeholder="例：^CP\d" />
            <Button text severity="danger" size="small" class="!p-1 !text-xs" @click="draft.rules.splice(ri, 1)">移除</Button>
          </div>
          <div class="flex items-center gap-2">
            <Button text severity="secondary" size="small" class="!p-1 !text-xs !text-gold/80" @click="draft.rules.push('')">+ 新增規則</Button>
            <Button text severity="secondary" size="small" class="!p-1 !text-xs !text-gray-300" @click="runPreview">試算</Button>
          </div>
          <div v-if="preview" class="text-[11px] text-gray-400 leading-relaxed">
            符合 <b class="text-gray-200">{{ preview.count }}</b> 個卡組：
            <span class="font-orbitron text-[10px] text-gold-light">{{ preview.sample.join(' ') }}</span>
            <span v-if="preview.elsewhere.length" class="block text-amber-400/80">
              其中 {{ preview.elsewhere.length }} 個目前歸在別類，排序決定誰先拿到
            </span>
          </div>
        </div>
        <div class="flex justify-end gap-2">
          <AppButton label="取消" variant="text" @click="cancelEdit" />
          <AppButton label="建立" variant="filled" tone="gold" :disabled="saving" @click="save" />
        </div>
      </div>
    </div>

    <div class="mt-3 flex justify-between">
      <AppButton label="新增分類" @click="startCreate" />
      <AppButton label="關閉" variant="text" @click="visible = false" />
    </div>
  </Dialog>
</template>
