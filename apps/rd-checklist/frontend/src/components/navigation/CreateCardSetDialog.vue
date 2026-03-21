<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { createCardSet } from '@/api/cardSets'
import { useCardSetsStore } from '@/stores/cardSets'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'

const emit = defineEmits<{
  created: []
}>()

const router = useRouter()
const store = useCardSetsStore()

const visible = ref(false)
const saving = ref(false)
const errorMsg = ref('')

const PRODUCT_TYPE_OPTIONS = [
  { label: '其他 / Promo', value: 'other' },
  { label: '補充包 Booster Pack', value: 'booster' },
  { label: '預組', value: 'structure_deck' },
  { label: '角色包 Character Pack', value: 'character_pack' },
  { label: 'Go Rush 角色包', value: 'go_rush_character' },
  { label: '戰鬥包 Battle Pack', value: 'battle_pack' },
  { label: 'Maximum 包', value: 'maximum_pack' },
  { label: 'Extra 包', value: 'extra_pack' },
  { label: '傳說包 Legend Pack', value: 'legend_pack' },
  { label: 'VS 包', value: 'vs_pack' },
  { label: '大會包 Tournament Pack', value: 'tournament_pack' },
  { label: '進階包 Advanced Pack', value: 'advanced_pack' },
  { label: 'Over Rush 包', value: 'over_rush_pack' },
]

const form = reactive({
  set_id: '',
  set_name_zh: '',
  set_name_jp: '',
  product_type: 'other',
  release_date: '',
})

function open() {
  form.set_id = ''
  form.set_name_zh = ''
  form.set_name_jp = ''
  form.product_type = 'other'
  form.release_date = ''
  errorMsg.value = ''
  visible.value = true
}

async function submit() {
  if (!form.set_id.trim()) {
    errorMsg.value = 'Set ID 不可為空'
    return
  }
  saving.value = true
  errorMsg.value = ''
  try {
    const created = await createCardSet({
      set_id: form.set_id.trim(),
      set_name_zh: form.set_name_zh.trim(),
      set_name_jp: form.set_name_jp.trim(),
      product_type: form.product_type,
      release_date: form.release_date.trim() || null,
    })
    visible.value = false
    await store.loadProductTypes()
    await store.loadSets()
    emit('created')
    router.push(`/set/${created.set_id}`)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    errorMsg.value = detail ?? '建立失敗，請稍後再試'
  } finally {
    saving.value = false
  }
}

defineExpose({ open })
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :style="{ width: '26rem' }"
    header="新增卡組"
    :pt="{
      root: { class: 'bg-dark-2 border border-[rgba(201,168,76,0.2)] rounded-xl' },
      header: { class: 'bg-dark-2 border-b border-[rgba(201,168,76,0.1)] px-5 py-4' },
      title: { class: 'font-cinzel text-base font-semibold text-gold-light' },
      content: { class: 'bg-dark-2 px-5 py-4' },
      footer: { class: 'bg-dark-2 border-t border-[rgba(201,168,76,0.1)] px-5 py-3' },
      closeButton: { class: 'text-gray-500 hover:text-gray-200' },
    }"
  >
    <div class="flex flex-col gap-4">
      <!-- Set ID -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-400 font-medium">
          Set ID <span class="text-red-400">*</span>
        </label>
        <InputText
          v-model="form.set_id"
          placeholder="例：PROMO"
          class="w-full text-sm"
          :class="errorMsg && !form.set_id.trim() ? 'p-invalid' : ''"
          @keydown.enter="submit"
        />
        <p class="text-[11px] text-gray-600">唯一識別碼，建立後不可更改</p>
      </div>

      <!-- 中文名 -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-400 font-medium">中文名稱</label>
        <InputText
          v-model="form.set_name_zh"
          placeholder="例：Promo / 書卡"
          class="w-full text-sm"
          @keydown.enter="submit"
        />
      </div>

      <!-- 日文名 -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-400 font-medium">日文名稱</label>
        <InputText
          v-model="form.set_name_jp"
          placeholder="例：プロモーション"
          class="w-full text-sm"
          @keydown.enter="submit"
        />
      </div>

      <!-- 類型 -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-400 font-medium">產品類型</label>
        <Select
          v-model="form.product_type"
          :options="PRODUCT_TYPE_OPTIONS"
          option-label="label"
          option-value="value"
          class="w-full text-sm"
        />
      </div>

      <!-- 發售日 -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-400 font-medium">發售日期（選填）</label>
        <InputText
          v-model="form.release_date"
          placeholder="例：2024/1/1"
          class="w-full text-sm"
          @keydown.enter="submit"
        />
      </div>

      <!-- 錯誤訊息 -->
      <p v-if="errorMsg" class="text-xs text-red-400">{{ errorMsg }}</p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <Button
          label="取消"
          severity="secondary"
          variant="outlined"
          size="small"
          @click="visible = false"
        />
        <Button
          label="建立"
          severity="warn"
          size="small"
          :loading="saving"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>
