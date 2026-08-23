<script setup lang="ts">
/**
 * 卡表對照：拿 yugipedia 的卡表跟資料庫比對，補上少的、刪掉多的。
 *
 * 比對單位是「一種印刷」＝ 卡號 + 貴罕度 + 是否異圖，因為收藏要收的就是這個：
 * 同一張卡的 SR 跟 SER 是兩件事，異圖是第三件。
 */
import { ref, computed } from 'vue'
import {
  compareSetList,
  applySetListDiff,
  type SetListCompare,
  type MissingPrinting,
  type ExtraPrinting,
  type RemapPrinting,
} from '@/api/cardSets'
import AppButton from '@/components/ui/AppButton.vue'
import Checkbox from 'primevue/checkbox'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'

const props = defineProps<{ setId: string; savedUrl?: string | null }>()
const emit = defineEmits<{ applied: []; urlSaved: [] }>()

const visible = ref(false)
const url = ref('')
const loading = ref(false)
const applying = ref(false)
const errorMsg = ref('')
const result = ref<SetListCompare | null>(null)
const applied = ref('')

/** 勾選狀態用 key 記，key = 卡號|貴罕度|異圖 */
const selectedMissing = ref<string[]>([])
const selectedExtra = ref<string[]>([])
const selectedRemap = ref<string[]>([])

const keyOf = (p: { card_id: string; rarity: string; is_alternate_art: boolean }) =>
  `${p.card_id}|${p.rarity}|${p.is_alternate_art}`
const remapKeyOf = (r: RemapPrinting) =>
  `${r.card_id}|${r.from_rarity}${r.from_is_alternate_art ? '*' : ''}` +
  `>${r.to_rarity}${r.to_is_alternate_art ? '*' : ''}`

function open() {
  visible.value = true
  errorMsg.value = ''
  applied.value = ''
  // 卡組記住網址後就不用每次貼；沒填過的話貼一次，比對成功會存回去
  if (!url.value && props.savedUrl) url.value = props.savedUrl
}

defineExpose({ open })

async function runCompare() {
  if (!url.value.trim() && !props.savedUrl) {
    errorMsg.value = '請先貼上 yugipedia 的卡組頁面網址'
    return
  }
  loading.value = true
  errorMsg.value = ''
  applied.value = ''
  result.value = null
  try {
    const wasSaved = props.savedUrl
    const r = await compareSetList(props.setId, url.value.trim())
    result.value = r
    // 後端會把這次用的網址記在卡組上（並抓卡組圖片）
    if (url.value.trim() && url.value.trim() !== wasSaved) emit('urlSaved')
    // 預設全選，通常兩邊都是要處理的
    selectedMissing.value = r.missing.map(keyOf)
    selectedExtra.value = r.extra.map(keyOf)
    selectedRemap.value = r.remap.map(remapKeyOf)
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ?? String(e)
  } finally {
    loading.value = false
  }
}

const missingChecked = computed(() =>
  (result.value?.missing ?? []).filter(m => selectedMissing.value.includes(keyOf(m))),
)
const extraChecked = computed(() =>
  (result.value?.extra ?? []).filter(e => selectedExtra.value.includes(keyOf(e))),
)
const remapChecked = computed(() =>
  (result.value?.remap ?? []).filter(r => selectedRemap.value.includes(remapKeyOf(r))),
)
const canApply = computed(
  () => missingChecked.value.length + extraChecked.value.length + remapChecked.value.length > 0,
)

function toggleAll(which: 'missing' | 'extra' | 'remap') {
  if (!result.value) return
  if (which === 'missing') {
    const all = result.value.missing.map(keyOf)
    selectedMissing.value = selectedMissing.value.length === all.length ? [] : all
  } else if (which === 'extra') {
    const all = result.value.extra.map(keyOf)
    selectedExtra.value = selectedExtra.value.length === all.length ? [] : all
  } else {
    const all = result.value.remap.map(remapKeyOf)
    selectedRemap.value = selectedRemap.value.length === all.length ? [] : all
  }
}

async function apply() {
  if (!result.value) return
  applying.value = true
  errorMsg.value = ''
  try {
    const r = await applySetListDiff(props.setId, {
      remap: remapChecked.value.map((x: RemapPrinting) => ({
        card_id: x.card_id,
        from_rarity: x.from_rarity,
        to_rarity: x.to_rarity,
        from_is_alternate_art: x.from_is_alternate_art,
        to_is_alternate_art: x.to_is_alternate_art,
      })),
      create: missingChecked.value.map((m: MissingPrinting) => ({
        card_id: m.card_id,
        rarity: m.rarity,
        is_alternate_art: m.is_alternate_art,
        name_jp: m.name_jp,
      })),
      delete: extraChecked.value.map((e: ExtraPrinting) => ({
        card_id: e.card_id,
        rarity: e.rarity,
        is_alternate_art: e.is_alternate_art,
      })),
    })
    const parts: string[] = []
    if (r.variants_remapped) parts.push(`修正 ${r.variants_remapped} 個貴罕度`)
    if (r.cards_created) parts.push(`新增 ${r.cards_created} 張卡`)
    if (r.variants_created) parts.push(`新增 ${r.variants_created} 個貴罕度`)
    if (r.variants_deleted) parts.push(`刪除 ${r.variants_deleted} 個貴罕度`)
    if (r.cards_deleted) parts.push(`刪除 ${r.cards_deleted} 張卡`)
    applied.value = parts.join('、') || '沒有變動'
    if (r.errors.length) errorMsg.value = r.errors.join('\n')
    emit('applied')
    await runCompare()
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ?? String(e)
  } finally {
    applying.value = false
  }
}

const ROW = 'flex items-center gap-2 px-2 py-1 rounded text-xs hover:bg-[rgba(201,168,76,0.06)]'
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="對照 yugipedia 卡表"
    :style="{ width: '52rem', maxWidth: '95vw' }"
  >
    <div class="flex flex-col gap-4">
      <!-- 網址輸入 -->
      <div class="flex items-end gap-2">
        <div class="flex-1 min-w-0">
          <label class="block text-[10px] font-orbitron tracking-wider uppercase text-gold mb-1">
            yugipedia 卡組頁面
          </label>
          <InputText
            v-model="url"
            placeholder="https://yugipedia.com/wiki/High-Grade_Collection"
            class="w-full"
            size="small"
            @keyup.enter="runCompare"
          />
        </div>
        <AppButton
          :disabled="loading"
          variant="filled"
          severity="warn"
          @click="runCompare"
        >{{ loading ? '比對中…' : '比對' }}</AppButton>
      </div>
      <p class="text-[11px] text-gray-400 -mt-2">
        貼上該卡組在 yugipedia 的頁面網址，會讀它的卡表子頁，逐一比對「卡號 + 貴罕度 + 異圖」。
        比對成功後會記在這個卡組上，下次就不用再貼，並順便抓卡組圖片。
      </p>

      <Message v-if="errorMsg" severity="error" :closable="false" class="text-xs whitespace-pre-line">
        {{ errorMsg }}
      </Message>
      <Message v-if="applied" severity="success" :closable="false" class="text-xs">
        {{ applied }}
      </Message>

      <template v-if="result">
        <div class="text-xs text-gray-400 border-t border-[rgba(201,168,76,0.14)] pt-3">
          卡表 <span class="text-gray-200">{{ result.expected_count }}</span> 種印刷 ·
          資料庫 <span class="text-gray-200">{{ result.actual_count }}</span> 種 ·
          <span class="font-mono text-[10px] text-gray-500">{{ result.list_page }}</span>
        </div>

        <Message
          v-if="result.unknown_rarities.length"
          severity="warn"
          :closable="false"
          class="text-xs"
        >
          有無法對應的貴罕度，這些印刷沒有列入比對：{{ result.unknown_rarities.join('、') }}
        </Message>

        <!-- 貴罕度記錯：改名，保住持有數與上傳圖 -->
        <section v-if="result.remap.length" class="flex flex-col gap-1">
          <header class="flex items-center justify-between">
            <h3 class="text-xs font-medium text-gray-200">
              貴罕度不符 <span class="text-emerald-400">{{ result.remap.length }}</span> 筆
              <span class="text-[10px] text-gray-500 font-normal ml-1">改名即可，持有數與上傳圖保留</span>
            </h3>
            <AppButton size="sm" variant="text" @click="toggleAll('remap')">全選 / 全不選</AppButton>
          </header>
          <div class="max-h-56 overflow-y-auto rounded border border-[rgba(110,231,183,0.22)] p-1">
            <label v-for="r in result.remap" :key="remapKeyOf(r)" :class="ROW">
              <Checkbox v-model="selectedRemap" :value="remapKeyOf(r)" multiple />
              <span class="font-mono text-gray-300 shrink-0">{{ r.card_id }}</span>
              <span class="shrink-0">
                <span class="text-red-300">{{ r.from_rarity }}</span>
                <span v-if="r.from_is_alternate_art" class="text-[10px] text-purple-300">異圖</span>
                <span class="text-gray-500 mx-1">→</span>
                <span class="text-emerald-300">{{ r.to_rarity }}</span>
                <span v-if="r.to_is_alternate_art" class="text-[10px] text-purple-300">異圖</span>
              </span>
              <span class="text-gray-300 truncate">{{ r.name_zh || r.name_jp }}</span>
              <span v-if="r.owned_count" class="ml-auto text-[10px] text-emerald-400 shrink-0">
                持有 {{ r.owned_count }}
              </span>
            </label>
          </div>
        </section>

        <div
          v-if="!result.missing.length && !result.extra.length && !result.remap.length"
          class="text-sm text-emerald-400 py-4 text-center"
        >
          完全一致，沒有缺漏也沒有多餘。
        </div>

        <!-- 少列：卡表有、資料庫沒有 -->
        <section v-if="result.missing.length" class="flex flex-col gap-1">
          <header class="flex items-center justify-between">
            <h3 class="text-xs font-medium text-gray-200">
              缺少 <span class="text-gold">{{ result.missing.length }}</span> 種印刷
            </h3>
            <AppButton size="sm" variant="text" @click="toggleAll('missing')">全選 / 全不選</AppButton>
          </header>
          <div class="max-h-56 overflow-y-auto rounded border border-[rgba(201,168,76,0.14)] p-1">
            <label v-for="m in result.missing" :key="keyOf(m)" :class="ROW">
              <Checkbox v-model="selectedMissing" :value="keyOf(m)" multiple />
              <span class="font-mono text-gray-300 shrink-0">{{ m.card_id }}</span>
              <span class="text-gold shrink-0">{{ m.rarity }}</span>
              <span v-if="m.is_alternate_art" class="text-[10px] text-purple-300 shrink-0">異圖</span>
              <span class="text-gray-300 truncate">{{ m.name_jp || m.name_en }}</span>
              <span v-if="!m.card_exists" class="ml-auto text-[10px] text-gray-500 shrink-0">新卡</span>
            </label>
          </div>
        </section>

        <!-- 多列：資料庫有、卡表沒有 -->
        <section v-if="result.extra.length" class="flex flex-col gap-1">
          <header class="flex items-center justify-between">
            <h3 class="text-xs font-medium text-gray-200">
              多出 <span class="text-red-400">{{ result.extra.length }}</span> 種印刷
            </h3>
            <AppButton size="sm" variant="text" @click="toggleAll('extra')">全選 / 全不選</AppButton>
          </header>
          <div class="max-h-56 overflow-y-auto rounded border border-[rgba(248,113,113,0.2)] p-1">
            <label v-for="e in result.extra" :key="keyOf(e)" :class="ROW">
              <Checkbox v-model="selectedExtra" :value="keyOf(e)" multiple />
              <span class="font-mono text-gray-300 shrink-0">{{ e.card_id }}</span>
              <span class="text-gold shrink-0">{{ e.rarity }}</span>
              <span v-if="e.is_alternate_art" class="text-[10px] text-purple-300 shrink-0">異圖</span>
              <span class="text-gray-300 truncate">{{ e.name_zh || e.name_jp }}</span>
              <span class="ml-auto flex items-center gap-2 shrink-0">
                <span v-if="e.owned_count" class="text-[10px] text-emerald-400">持有 {{ e.owned_count }}</span>
                <span v-if="e.is_only_variant" class="text-[10px] text-red-400">刪掉整張卡</span>
              </span>
            </label>
          </div>
        </section>
      </template>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-3 w-full">
        <span v-if="result && canApply" class="text-[11px] text-gray-400">
          將修正 {{ remapChecked.length }} 種、新增 {{ missingChecked.length }} 種、刪除 {{ extraChecked.length }} 種
        </span>
        <span v-else />
        <div class="flex gap-2">
          <AppButton variant="text" @click="visible = false">關閉</AppButton>
          <AppButton
            v-if="result"
            :disabled="!canApply || applying"
            variant="filled"
            severity="warn"
            @click="apply"
          >{{ applying ? '套用中…' : '套用勾選項目' }}</AppButton>
        </div>
      </div>
    </template>
  </Dialog>
</template>
