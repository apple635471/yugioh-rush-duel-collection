<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import { fetchSetImages, getSetImageUrl, type CardSetImage, type TimelineSet } from '@/api/cardSets'
import { getCardImageUrl } from '@/api/cards'
import { productTypeTheme } from '@/constants/productTypes'

const props = defineProps<{
  sets: TimelineSet[]
  loading: boolean
}>()

/** 貴罕度標籤最多列幾種，其餘收成 +N（完整清單在卡組頁看得到） */
const RARITY_CHIP_LIMIT = 5
/** 每個卡組固定幾格卡圖——不足時留空位，盒子高度才不會忽高忽低 */
const CARD_SLOTS = 4

interface YearRow { kind: 'year'; key: string; year: string }
interface SetRow {
  kind: 'set'
  key: string
  set: TimelineSet
  side: 'l' | 'r'
  day: string
  color: string
  typeLabel: string
  pct: number
}
type Row = YearRow | SetRow

/** "2026/8/22" → "8/22"；只有年月時就顯示月份 */
function dayLabel(releaseDate: string): string {
  const [, month, day] = releaseDate.split('/')
  if (!month) return ''
  return day ? `${Number(month)}/${Number(day)}` : `${Number(month)}月`
}

const rows = computed<Row[]>(() => {
  const out: Row[] = []
  let lastYear = ''
  // 左右輪替以卡組序號為準，年份標記不打斷輪替
  props.sets.forEach((set, i) => {
    const year = set.release_date.split('/')[0] ?? ''
    if (year !== lastYear) {
      out.push({ kind: 'year', key: `y-${year}-${i}`, year })
      lastYear = year
    }
    const theme = productTypeTheme(set.product_type)
    out.push({
      kind: 'set',
      key: set.set_id,
      set,
      side: i % 2 === 0 ? 'l' : 'r',
      day: dayLabel(set.release_date),
      color: theme.color,
      typeLabel: theme.label,
      pct: set.total_variants
        ? Math.round(set.owned_variants / set.total_variants * 100)
        : 0,
    })
  })
  return out
})

function chips(set: TimelineSet) {
  return set.rarity_distribution.slice(0, RARITY_CHIP_LIMIT)
}

function hiddenRarityCount(set: TimelineSet) {
  return Math.max(0, set.rarity_distribution.length - RARITY_CHIP_LIMIT)
}

/** 卡圖網址；異圖的 rarity key 要帶 -alt */
function cardImage(card: { card_id: string; rarity: string; is_alternate_art: boolean }) {
  return getCardImageUrl(card.card_id, card.is_alternate_art ? `${card.rarity}-alt` : card.rarity)
}

function emptySlots(set: TimelineSet) {
  return Math.max(0, CARD_SLOTS - set.top_cards.length)
}

/* ── 點縮圖放大 ────────────────────────────────────────────
   盒子裡的圖太小，看不出是哪張卡。點任一張就開燈箱，左右鍵在同一個卡組的
   圖片之間移動（卡組圖片在前、卡圖在後，順序與盒子上看到的一致）。 */
interface PreviewItem {
  key: string
  src: string
  label: string
  sub: string
}

const previewSet = ref<TimelineSet | null>(null)
const previewItems = ref<PreviewItem[]>([])
const previewIndex = ref(0)
const previewOpen = computed(() => previewItems.value.length > 0)
const previewCurrent = computed(() => previewItems.value[previewIndex.value] ?? null)

/** 卡組圖片可能不只一張，但時間軸只帶第一張；開燈箱時才去補齊，補完就記住 */
const galleryCache = new Map<string, CardSetImage[]>()

function cardItems(set: TimelineSet): PreviewItem[] {
  return set.top_cards.map(c => ({
    key: `card-${c.card_id}-${c.rarity}-${c.is_alternate_art}`,
    src: cardImage(c),
    label: c.name_zh || c.name_jp || c.card_id,
    sub: `${c.card_id} · ${c.rarity}${c.is_alternate_art ? ' 異圖' : ''}`,
  }))
}

function galleryItems(set: TimelineSet, images?: CardSetImage[]): PreviewItem[] {
  if (images) {
    return images.map(img => ({
      key: `set-${img.id}`,
      src: getSetImageUrl(img.id),
      label: `${set.set_id} 卡組圖片`,
      sub: img.title,
    }))
  }
  if (set.image_id === null) return []
  return [{
    key: `set-${set.image_id}`,
    src: getSetImageUrl(set.image_id),
    label: `${set.set_id} 卡組圖片`,
    sub: '',
  }]
}

async function openPreview(set: TimelineSet, kind: 'gallery' | 'card', cardIndex = 0) {
  const images = galleryCache.get(set.set_id)
  const shots = galleryItems(set, images)
  previewSet.value = set
  previewItems.value = [...shots, ...cardItems(set)]
  previewIndex.value = kind === 'gallery' ? 0 : shots.length + cardIndex
  if (images || set.image_id === null) return

  // 背景補齊卡組圖片；補完後卡圖會往後挪，索引跟著挪才不會跳到別張
  let fetched: CardSetImage[] = []
  try {
    fetched = await fetchSetImages(set.set_id)
  } catch {
    return
  }
  galleryCache.set(set.set_id, fetched)
  if (previewSet.value !== set || fetched.length <= shots.length) return
  const shift = fetched.length - shots.length
  previewItems.value = [...galleryItems(set, fetched), ...cardItems(set)]
  if (kind === 'card') previewIndex.value += shift
}

function closePreview() {
  previewItems.value = []
  previewSet.value = null
  previewIndex.value = 0
}

function step(delta: number) {
  const n = previewItems.value.length
  if (n < 2) return
  previewIndex.value = (previewIndex.value + delta + n) % n
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowLeft') step(-1)
  else if (e.key === 'ArrowRight') step(1)
}

watch(previewOpen, (open) => {
  if (open) window.addEventListener('keydown', onKey)
  else window.removeEventListener('keydown', onKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <!-- Loading skeleton -->
  <div v-if="loading" class="flex flex-col gap-3">
    <div
      v-for="i in 5"
      :key="i"
      class="h-32 bg-surface rounded-lg animate-pulse border border-[rgba(201,168,76,0.08)]"
    />
  </div>

  <!-- Empty state -->
  <div v-else-if="sets.length === 0" class="text-center py-12 text-gray-400">
    沒有帶發行日的卡組——時間軸只放得下有日期的卡組。
  </div>

  <div v-else class="tl">
    <template v-for="row in rows" :key="row.key">
      <!-- 年份分隔 -->
      <div v-if="row.kind === 'year'" class="tl-year">
        <span>{{ row.year }}</span>
      </div>

      <!-- 一個卡組 -->
      <div v-else class="tl-row" :class="row.side" :style="{ '--c': row.color }">
        <div class="tl-box">
          <!-- 整個盒子可點：連結鋪滿盒子墊在底下，圖片再疊上去自己吃點擊 -->
          <router-link
            :to="`/set/${row.set.set_id}`"
            class="tl-link"
            :aria-label="`${row.set.set_id} ${row.set.set_name_zh || row.set.set_name_jp}`"
          />
          <div class="tl-edge" />

          <div class="tl-main">
            <div class="tl-top">
              <span class="tl-id">{{ row.set.set_id }}</span>
              <span class="tl-type">{{ row.typeLabel }}</span>
              <span class="tl-date">{{ row.day }}</span>
            </div>

            <h3 class="tl-name">{{ row.set.set_name_zh || row.set.set_name_jp }}</h3>

            <!-- 貴罕度分布：最稀有在前 -->
            <div class="tl-rars">
              <span v-for="r in chips(row.set)" :key="r.rarity" class="tl-rar">
                {{ r.rarity }}<i>×{{ r.count }}</i>
              </span>
              <span v-if="hiddenRarityCount(row.set)" class="tl-rar more">
                +{{ hiddenRarityCount(row.set) }}
              </span>
            </div>

            <!-- 該卡組最稀有的幾張卡（同一張卡只取它最稀有的版本） -->
            <div class="tl-cards">
              <button
                v-for="(c, i) in row.set.top_cards"
                :key="c.card_id + c.rarity"
                type="button"
                class="tl-card"
                :title="`${c.name_zh || c.name_jp}（${c.rarity}）— 點擊放大`"
                @click="openPreview(row.set, 'card', i)"
              >
                <img :src="cardImage(c)" :alt="c.name_zh || c.name_jp" loading="lazy">
                <span class="tl-card-rar">{{ c.rarity }}</span>
              </button>
              <div v-for="n in emptySlots(row.set)" :key="`empty-${n}`" class="tl-card empty" />
            </div>

            <div class="tl-foot">
              <span class="tl-num">
                {{ row.set.owned_variants }}<i>/{{ row.set.total_variants }}</i>
              </span>
              <span class="tl-pct" :class="{ done: row.pct === 100 }">{{ row.pct }}%</span>
            </div>
            <div class="tl-bar">
              <div class="tl-bar-fill" :class="{ done: row.pct === 100 }" :style="{ width: `${row.pct}%` }" />
            </div>
          </div>

          <!-- 卡組包裝圖 -->
          <button
            v-if="row.set.image_id"
            type="button"
            class="tl-shot"
            :title="`${row.set.set_id} 卡組圖片 — 點擊放大`"
            @click="openPreview(row.set, 'gallery')"
          >
            <img :src="getSetImageUrl(row.set.image_id)" :alt="`${row.set.set_id} 包裝`" loading="lazy">
          </button>
          <div v-else class="tl-shot empty"><span>{{ row.set.set_id }}</span></div>
        </div>

        <div class="tl-stem" />
        <div class="tl-node" />
      </div>
    </template>
  </div>

  <!-- 放大檢視：左右鍵或兩側箭頭在同一個卡組的圖片之間移動 -->
  <Dialog
    :visible="previewOpen"
    modal
    dismissable-mask
    :style="{ width: 'auto', maxWidth: '94vw' }"
    @update:visible="closePreview"
  >
    <template #header>
      <div class="min-w-0">
        <div class="text-sm text-gray-100 truncate">{{ previewCurrent?.label }}</div>
        <div v-if="previewCurrent?.sub" class="font-orbitron text-[11px] text-gray-400 truncate">
          {{ previewCurrent.sub }}
        </div>
      </div>
    </template>

    <div v-if="previewCurrent" class="flex items-center gap-3">
      <button
        v-if="previewItems.length > 1"
        type="button"
        class="tl-nav"
        aria-label="上一張"
        @click="step(-1)"
      >‹</button>

      <img
        :key="previewCurrent.key"
        :src="previewCurrent.src"
        :alt="previewCurrent.label"
        class="max-h-[78vh] w-auto max-w-full rounded"
      >

      <button
        v-if="previewItems.length > 1"
        type="button"
        class="tl-nav"
        aria-label="下一張"
        @click="step(1)"
      >›</button>
    </div>

    <div v-if="previewItems.length > 1" class="mt-2 text-center font-orbitron text-[11px] text-gray-400">
      {{ previewIndex + 1 }} / {{ previewItems.length }}
    </div>
  </Dialog>
</template>

<style scoped>
/* 時間軸：中央一條線，卡組左右交錯掛在線上，盒子用箭頭指回軸線。
   交錯本來就空出垂直空間，所以盒高固定 228px、列距 130px（margin-top:-98px）：
   相鄰兩列（異側）緊密咬合，同側（相隔一列）仍留 32px 淨空。 */
.tl {
  position: relative;
  padding: 0.5rem 0 1rem;
}
.tl::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 2px;
  transform: translateX(-50%);
  background: linear-gradient(
    180deg,
    transparent,
    rgba(201, 168, 76, 0.16) 6%,
    rgba(201, 168, 76, 0.16) 94%,
    transparent
  );
}

.tl-year {
  position: relative;
  z-index: 2;
  text-align: center;
  margin: 1.1rem 0 0.7rem;
}
.tl-year span {
  font-family: var(--font-orbitron);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: var(--color-gold);
  background: var(--color-dark-bg);
  padding: 0.2rem 0.7rem;
  border: 1px solid rgba(201, 168, 76, 0.16);
  border-radius: 999px;
}

.tl-row {
  position: relative;
  display: flex;
  /* 列與列上下重疊，而每一列都橫跨整個寬度：不關掉指標事件的話，後面那一列
     的空白區會蓋住前一列盒子的下半部，讓那裡點不到 */
  pointer-events: none;
}
.tl-box, .tl-node, .tl-stem { pointer-events: auto; }
.tl-row + .tl-row { margin-top: -98px; }
.tl-year + .tl-row { margin-top: 0.4rem; }
.tl-row.l { justify-content: flex-start; padding-right: calc(50% + 2.2rem); }
.tl-row.r { justify-content: flex-end;  padding-left:  calc(50% + 2.2rem); }
/* 後面的列疊在前面的列之上，hover 時再抬到最上層 */
.tl-row:hover { z-index: 3; }

.tl-node {
  position: absolute;
  left: 50%;
  top: 1.5rem;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--c);
  transform: translateX(-50%);
  box-shadow: 0 0 0 3px var(--color-dark-bg), 0 0 12px -2px var(--c);
}
.tl-stem {
  position: absolute;
  top: calc(1.5rem + 6px);
  width: 2rem;
  height: 2px;
  background: var(--c);
  opacity: 0.45;
}
.tl-row.l .tl-stem { right: calc(50% + 6px); }
.tl-row.r .tl-stem { left:  calc(50% + 6px); }

/* overflow 必須 visible，否則指向軸線的箭頭會被裁掉——圓角改由各子元素自己處理 */
.tl-box {
  position: relative;
  display: flex;
  width: 100%;
  height: 228px;
  background: var(--color-dark-4);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 8px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.tl-box:hover {
  border-color: color-mix(in srgb, var(--c) 55%, transparent);
  box-shadow: 0 8px 24px -12px rgba(0, 0, 0, 0.8);
}
.tl-box::after {
  content: '';
  position: absolute;
  top: 1.15rem;
  border: 9px solid transparent;
}
.tl-row.l .tl-box::after { right: -17px; border-left-color:  var(--c); }
.tl-row.r .tl-box::after { left:  -17px; border-right-color: var(--c); }
.tl-row.l .tl-box { flex-direction: row-reverse; }

/* 整盒可點的連結墊在底層；圖片是 position:relative，DOM 在後面所以疊在它上面，
   點圖不會順便觸發跳轉 */
.tl-link {
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: 8px;
}
.tl-link:focus-visible { outline: 2px solid var(--c); outline-offset: 2px; }

.tl-edge { width: 5px; background: var(--c); flex-shrink: 0; }
.tl-row.r .tl-edge { border-radius: 7px 0 0 7px; }
.tl-row.l .tl-edge { border-radius: 0 7px 7px 0; }

.tl-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.6rem 0.75rem;
}
/* 盒高固定，所以文字列一律不壓縮，剩下的高度全給卡圖列 */
.tl-main > * { flex-shrink: 0; }

.tl-top { display: flex; align-items: center; gap: 0.45rem; }
.tl-id {
  font-family: var(--font-orbitron);
  font-size: 0.62rem;
  color: var(--c);
  background: color-mix(in srgb, var(--c) 14%, transparent);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}
.tl-type { font-size: 0.68rem; color: var(--color-gray-400); }
.tl-date {
  font-family: var(--font-orbitron);
  font-size: 0.64rem;
  color: var(--color-gray-400);
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}

.tl-name {
  font-family: var(--font-cinzel);
  font-size: 0.95rem;
  margin: 0;
  color: var(--color-gray-100);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.tl-box:hover .tl-name { color: var(--color-gold-light); }

.tl-rars { display: flex; flex-wrap: wrap; gap: 0.25rem; }
.tl-rar {
  font-family: var(--font-orbitron);
  font-size: 0.58rem;
  color: var(--color-gray-400);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 3px;
  padding: 0.05rem 0.28rem;
}
.tl-rar i { font-style: normal; opacity: 0.7; }
.tl-rar.more { border-style: dashed; }

.tl-cards {
  display: flex;
  gap: 0.35rem;
  flex: 1 1 auto;
  min-height: 0;
  align-items: stretch;
}
.tl-card {
  margin: 0;
  padding: 0;
  border: 0;
  background: none;
  position: relative;
  height: 100%;
  aspect-ratio: 59 / 86;
  cursor: zoom-in;
}
.tl-card img {
  height: 100%;
  width: 100%;
  object-fit: cover;
  border-radius: 3px;
  display: block;
  border: 1px solid rgba(255, 255, 255, 0.07);
  transition: border-color 0.15s, transform 0.15s;
}
.tl-card:hover img {
  border-color: var(--c);
  transform: scale(1.04);
}
.tl-card:focus-visible { outline: 2px solid var(--c); outline-offset: 2px; }
.tl-card-rar {
  position: absolute;
  left: 3px;
  bottom: 3px;
  font-family: var(--font-orbitron);
  font-size: 0.55rem;
  background: rgba(9, 9, 15, 0.82);
  color: var(--c);
  padding: 0 0.2rem;
  border-radius: 2px;
}
.tl-card.empty { border: 1px dashed rgba(255, 255, 255, 0.07); border-radius: 3px; cursor: default; }

.tl-foot { display: flex; align-items: baseline; gap: 0.5rem; margin-top: auto; }
.tl-num {
  font-family: var(--font-orbitron);
  font-size: 0.68rem;
  color: var(--color-gray-100);
  font-variant-numeric: tabular-nums;
}
.tl-num i { color: var(--color-gray-400); font-style: normal; }
.tl-pct {
  font-family: var(--font-orbitron);
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--c);
  font-variant-numeric: tabular-nums;
  margin-left: auto;
}
.tl-pct.done { color: var(--color-emerald-400); }
.tl-bar {
  height: 3px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.07);
  overflow: hidden;
}
.tl-bar-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--c) 35%, transparent), var(--c));
  transition: width 0.5s;
}
.tl-bar-fill.done { background: var(--color-emerald-500); }

.tl-shot {
  position: relative;
  flex-shrink: 0;
  width: 104px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
  padding: 0.5rem;
  border: 0;
  cursor: zoom-in;
  /* hover 放大 5%，不讓它溢出盒子邊界 */
  overflow: hidden;
}
.tl-shot img {
  max-height: 210px;
  max-width: 100%;
  width: auto;
  border-radius: 3px;
  transition: transform 0.15s;
}
.tl-shot:hover img { transform: scale(1.05); }
.tl-shot:focus-visible { outline: 2px solid var(--c); outline-offset: -2px; }
.tl-row.r .tl-shot { border-radius: 0 7px 7px 0; }
.tl-row.l .tl-shot { border-radius: 7px 0 0 7px; }
.tl-shot.empty {
  cursor: default;
  background: transparent;
  border-left: 1px dashed color-mix(in srgb, var(--c) 28%, transparent);
  font-family: var(--font-orbitron);
  font-size: 0.55rem;
  color: color-mix(in srgb, var(--c) 65%, transparent);
}
.tl-row.l .tl-shot.empty { border-left: 0; border-right: 1px dashed color-mix(in srgb, var(--c) 28%, transparent); }

/* 燈箱左右鈕 */
.tl-nav {
  flex-shrink: 0;
  width: 2rem;
  height: 3.5rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-gray-300);
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.tl-nav:hover { border-color: var(--color-gold); color: var(--color-gold-light); }

/* 版面不夠寬時放棄交錯：軸線靠左，卡組一律排右邊、高度改為自動 */
@media (max-width: 1100px) {
  .tl::before { left: 1.25rem; }
  .tl-row.l, .tl-row.r { justify-content: flex-end; padding-left: 3.75rem; padding-right: 0; }
  .tl-row + .tl-row { margin-top: 0.75rem; }
  .tl-year { text-align: left; padding-left: 0.4rem; }
  .tl-node { left: 1.25rem; }
  .tl-stem { left: calc(1.25rem + 6px); right: auto; width: 1.4rem; }
  .tl-box { height: auto; min-height: 190px; }
  .tl-row.l .tl-box { flex-direction: row; }
  .tl-row.l .tl-box::after { right: auto; left: -17px; border-left-color: transparent; border-right-color: var(--c); }
  .tl-row.l .tl-edge { border-radius: 7px 0 0 7px; }
  .tl-row.l .tl-shot { border-radius: 0 7px 7px 0; }
  .tl-row.l .tl-shot.empty { border-left: 1px dashed color-mix(in srgb, var(--c) 28%, transparent); border-right: 0; }
  .tl-cards { min-height: 96px; }
}
</style>
