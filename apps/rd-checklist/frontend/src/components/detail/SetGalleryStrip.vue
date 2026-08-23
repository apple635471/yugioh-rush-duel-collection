<script setup lang="ts">
/**
 * 卡組的代表圖（yugipedia gallery 的日文版包裝與海報）。
 *
 * 排版限制：這是一個**固定長寬**的瀏覽窗，用絕對定位掛在按鈕列左側，
 * 所以不論有幾張圖都不會把標題、中日文名或卡片列表推開。圖多就橫向捲動。
 */
import { ref, watch } from 'vue'
import { fetchSetImages, getSetImageUrl, type CardSetImage } from '@/api/cardSets'
import Dialog from 'primevue/dialog'

const props = defineProps<{ setId: string }>()

const images = ref<CardSetImage[]>([])
const preview = ref<CardSetImage | null>(null)

async function load() {
  try {
    images.value = await fetchSetImages(props.setId)
  } catch {
    images.value = []
  }
}

watch(() => props.setId, load, { immediate: true })
defineExpose({ reload: load })
</script>

<template>
  <div
    v-if="images.length"
    class="absolute right-full top-0 mr-3 hidden lg:flex h-[82px] w-[240px] gap-2
           overflow-x-auto overflow-y-hidden rounded border border-[rgba(201,168,76,0.16)]
           bg-dark-2/60 px-2 py-1.5"
    :title="`${images.length} 張卡組圖片`"
  >
    <button
      v-for="img in images"
      :key="img.id"
      type="button"
      class="h-full shrink-0 cursor-pointer rounded overflow-hidden border border-transparent
             hover:border-gold/50 transition-colors"
      :title="img.title"
      @click="preview = img"
    >
      <img :src="getSetImageUrl(img.id)" :alt="img.title" class="h-full w-auto object-contain" />
    </button>
  </div>

  <Dialog
    :visible="!!preview"
    modal
    :header="preview?.title"
    :style="{ width: 'auto', maxWidth: '92vw' }"
    @update:visible="preview = null"
  >
    <img
      v-if="preview"
      :src="getSetImageUrl(preview.id)"
      :alt="preview.title"
      class="max-h-[78vh] w-auto"
    />
  </Dialog>
</template>
