<template>
  <Teleport to="body">
    <div class="crop-overlay" @click.self="$emit('cancel')">
      <section class="crop-dialog" role="dialog" aria-modal="true" aria-label="Crop image">
        <header><div><p>IMAGE EDITOR</p><h2>Adjust your crop</h2></div><button type="button" aria-label="Close crop editor" @click="$emit('cancel')">×</button></header>
        <div ref="frame" class="crop-frame" :style="{ aspectRatio: String(aspectRatio), width: `min(100%, ${58 * aspectRatio}vh)` }" @pointerdown="startDrag" @pointermove="drag" @pointerup="endDrag" @pointercancel="endDrag">
          <img :src="previewUrl" :style="imageStyle" alt="Image crop preview" draggable="false" />
        </div>
        <label class="zoom-control">Zoom <input v-model.number="zoom" type="range" min="1" max="3" step="0.01" /></label>
        <p class="crop-hint">Drag the image to reposition it. You can skip cropping.</p>
        <footer><button class="skip" type="button" @click="$emit('skip', file)">Use original</button><button class="confirm" type="button" @click="confirmCrop">Use crop</button></footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({ file: { type: File, required: true }, aspectRatio: { type: Number, default: 4 / 3 } })
const emit = defineEmits(['confirm', 'skip', 'cancel'])
const previewUrl = ref('')
const image = ref(null)
const frame = ref(null)
const zoom = ref(1)
const position = ref({ x: 0, y: 0 })
const dragging = ref(false)
const pointer = ref({ x: 0, y: 0 })

function loadPreview(file) {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = URL.createObjectURL(file)
  const next = new Image()
  next.onload = () => { image.value = next; position.value = { x: 0, y: 0 }; zoom.value = 1 }
  next.src = previewUrl.value
}
watch(() => props.file, loadPreview, { immediate: true })
onBeforeUnmount(() => { if (previewUrl.value) URL.revokeObjectURL(previewUrl.value) })

const imageStyle = computed(() => {
  if (!image.value || !frame.value) return {}
  const rect = frame.value.getBoundingClientRect()
  const scale = Math.max(rect.width / image.value.naturalWidth, rect.height / image.value.naturalHeight) * zoom.value
  const width = image.value.naturalWidth * scale
  const height = image.value.naturalHeight * scale
  const x = Math.min(0, Math.max(rect.width - width, position.value.x))
  const y = Math.min(0, Math.max(rect.height - height, position.value.y))
  return { width: `${width}px`, height: `${height}px`, left: `${x}px`, top: `${y}px` }
})

function startDrag(event) {
  dragging.value = true
  pointer.value = { x: event.clientX - position.value.x, y: event.clientY - position.value.y }
  event.currentTarget.setPointerCapture(event.pointerId)
}
function drag(event) {
  if (!dragging.value) return
  position.value = { x: event.clientX - pointer.value.x, y: event.clientY - pointer.value.y }
}
function endDrag() { dragging.value = false }

async function confirmCrop() {
  if (!image.value || !frame.value) return
  const rect = frame.value.getBoundingClientRect()
  const scale = Math.max(rect.width / image.value.naturalWidth, rect.height / image.value.naturalHeight) * zoom.value
  const left = Math.min(0, Math.max(rect.width - image.value.naturalWidth * scale, position.value.x))
  const top = Math.min(0, Math.max(rect.height - image.value.naturalHeight * scale, position.value.y))
  const sourceX = Math.max(0, -left / scale)
  const sourceY = Math.max(0, -top / scale)
  const sourceWidth = Math.min(image.value.naturalWidth - sourceX, rect.width / scale)
  const sourceHeight = Math.min(image.value.naturalHeight - sourceY, rect.height / scale)
  const outputWidth = Math.min(props.aspectRatio === 1 ? 1024 : 2048, Math.max(512, Math.round(sourceWidth)))
  const canvas = document.createElement('canvas')
  canvas.width = outputWidth
  canvas.height = Math.round(outputWidth / props.aspectRatio)
  const context = canvas.getContext('2d')
  context.drawImage(image.value, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, canvas.width, canvas.height)
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, props.file.type || 'image/jpeg', 0.92))
  if (!blob) return
  const name = props.file.name.replace(/\.[^.]+$/, '') + '-cropped.' + (blob.type.split('/')[1] || 'jpg').replace('jpeg', 'jpg')
  emit('confirm', new File([blob], name, { type: blob.type, lastModified: Date.now() }))
}
</script>

<style scoped>
.crop-overlay { position:fixed; inset:0; z-index:800; display:grid; place-items:center; padding:18px; background:rgba(14,15,17,.68); backdrop-filter:blur(5px); }
.crop-dialog { width:min(520px,100%); padding:20px; border:1px solid var(--border-color); border-radius:20px; background:var(--card-bg); box-shadow:0 24px 80px rgba(0,0,0,.3); }
header,footer { display:flex; align-items:center; justify-content:space-between; gap:12px; }
header p { margin:0 0 4px; color:var(--text-tertiary); font-size:9px; font-weight:750; letter-spacing:.14em; }
header h2 { margin:0; font:750 19px Manrope,sans-serif; }
header button { width:32px; height:32px; border-radius:9px; background:var(--icon-bg); color:var(--text-main); font-size:21px; }
.crop-frame { position:relative; width:100%; margin:18px auto 13px; overflow:hidden; border-radius:13px; background:#15171a; touch-action:none; }
.crop-frame img { position:absolute; max-width:none; object-fit:fill; user-select:none; pointer-events:none; }
.zoom-control { display:flex; align-items:center; gap:12px; color:var(--text-secondary); font-size:11px; }
.zoom-control input { flex:1; accent-color:var(--text-main); }
.crop-hint { margin:9px 0 17px; color:var(--text-tertiary); font-size:11px; }
footer button { min-height:38px; padding:0 13px; border-radius:10px; font-size:11px; font-weight:700; }
.skip { border:1px solid var(--border-color); background:transparent; color:var(--text-secondary); }
.confirm { margin-left:auto; background:var(--primary-bg); color:var(--primary-text); }
</style>
