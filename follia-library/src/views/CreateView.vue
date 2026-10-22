<template>
  <MainLayout>
    <section class="create-page">
      <header class="create-heading">
        <div>
          <p class="page-kicker">MAKE SOMETHING</p>
          <h1>What are you sharing?</h1>
          <p>Bring a thought to the feed or add something useful to the library.</p>
        </div>
        <RouterLink to="/" class="back-link"><ArrowLeft :size="17" /> Feed</RouterLink>
      </header>

      <div class="create-switch" role="tablist" aria-label="Choose what to create">
        <button :class="{ selected: mode === 'post' }" role="tab" :aria-selected="mode === 'post'" @click="mode = 'post'">
          <MessageCircle :size="18" /> <span><strong>Create Post</strong><small>Share a thought, image or video</small></span>
        </button>
        <button :class="{ selected: mode === 'resource' }" role="tab" :aria-selected="mode === 'resource'" @click="mode = 'resource'">
          <BookOpen :size="18" /> <span><strong>Upload Resource</strong><small>Add a book or useful file</small></span>
        </button>
      </div>

      <form v-if="mode === 'post'" class="post-composer" @submit.prevent="publishPost">
        <div class="composer-top">
          <div class="avatar"><UserAvatar :src="profile?.avatar_url || profile?.avatar" :alt="displayName + ' profile picture'" :icon-size="20" /></div>
          <div><strong>{{ displayName }}</strong><span>Sharing with everyone</span></div>
        </div>
        <label class="sr-only" for="post-body">Write a post</label>
        <textarea id="post-body" v-model="body" maxlength="5000" placeholder="What have you discovered lately?" rows="6"></textarea>
        <div v-if="selectedMedia.length" class="media-preview-list">
          <div v-for="(entry, index) in selectedMedia" :key="entry.url" class="media-preview">
            <video v-if="entry.type === 'video'" :src="entry.url" controls playsinline />
            <img v-else :src="entry.url" :alt="'Post image ' + (index + 1)" />
            <button type="button" class="remove-media" :aria-label="'Remove media ' + (index + 1)" @click="removeMedia(index)"><X :size="16" /></button>
          </div>
        </div>
        <section v-if="videoCandidate" class="video-trim-panel">
          <p class="video-limit">Video upload limit: <strong>40 MB per video</strong><span v-if="videoCandidate.size > MAX_VIDEO_SIZE"> This source is over the limit; select a shorter clip to reduce its size.</span></p>
          <video ref="trimVideoElement" :src="candidateUrl" controls playsinline preload="metadata" @loadedmetadata="readVideoDuration" @timeupdate="stopClipPreview" />
          <p class="duration-label">Original duration: {{ formatDuration(videoDuration) }}</p>
          <div class="trim-timeline" :style="trimTimelineStyle" aria-label="Choose the video section to keep">
            <div class="trim-frames" aria-hidden="true">
              <img v-for="(frame, index) in thumbnailFrames" :key="index" :src="frame" alt="" />
              <span v-if="!thumbnailFrames.length">Video timeline</span>
            </div>
            <div class="trim-selection" aria-hidden="true"></div>
            <input class="trim-range trim-start" type="range" min="0" :max="videoDuration" step="0.1" :value="trimStart" :aria-label="'Clip start: ' + formatDuration(trimStart)" :disabled="!videoDuration || videoProcessing" @input="updateTrimStart" />
            <input class="trim-range trim-end" type="range" min="0" :max="videoDuration" step="0.1" :value="trimEnd" :aria-label="'Clip end: ' + formatDuration(trimEnd)" :disabled="!videoDuration || videoProcessing" @input="updateTrimEnd" />
          </div>
          <div class="trim-time-labels"><span>Start <strong>{{ formatDuration(trimStart) }}</strong></span><span>End <strong>{{ formatDuration(trimEnd) }}</strong></span></div>
          <div class="trim-fields">
            <label>Start <input v-model.number="trimStart" type="number" min="0" :max="videoDuration" step="0.1" @change="clampTrimPoints" /> s</label>
            <label>End <input v-model.number="trimEnd" type="number" min="0" :max="videoDuration" step="0.1" @change="clampTrimPoints" /> s</label>
          </div>
          <p class="duration-label selected-duration">Clip to keep: <strong>{{ formatDuration(Math.max(0, trimEnd - trimStart)) }}</strong></p>
          <p v-if="videoError" class="form-message error">{{ videoError }}</p>
          <p v-if="videoProcessing" class="duration-label">Preparing the selected clip…</p>
          <div class="trim-actions">
            <button type="button" @click="previewClip">Preview selection</button>
            <button type="button" :disabled="videoProcessing || !videoDuration || videoCandidate.size > MAX_VIDEO_SIZE" @click="confirmVideo(false)">Use original</button>
            <button type="button" class="trim-confirm" :disabled="videoProcessing || !videoDuration" @click="confirmVideo(true)">{{ videoProcessing ? 'Processing…' : 'Use selected clip' }}</button>
            <button type="button" :disabled="videoProcessing" @click="clearVideoCandidate">Remove video</button>
          </div>
        </section>
        <div v-if="error" class="form-message error">{{ error }}</div>
        <div class="composer-footer">
          <div class="composer-tools">
            <label class="attach-button" for="post-media"><ImagePlus :size="19" /><span>Photos or video</span></label>
            <input id="post-media" ref="mediaInput" type="file" accept="image/*,video/*" multiple @change="chooseMedia" />
            <span class="char-count">{{ body.length }}/5000</span>
          </div>
          <button class="publish-button" type="submit" :disabled="publishing || videoProcessing || !!videoCandidate || (!body.trim() && !selectedMedia.length)">
            {{ publishing ? 'Sharing…' : 'Share post' }} <ArrowUpRight v-if="!publishing" :size="17" />
          </button>
        </div>
      </form>

      <section v-else class="resource-choice">
        <div class="resource-choice-icon"><BookOpen :size="26" /></div>
        <h2>Put something good on the shelf.</h2>
        <p>Books, PDFs, comics and useful materials stay part of Follia’s library. Upload the file, add a cover and tell people what makes it worth opening.</p>
        <RouterLink to="/upload" class="publish-button">Continue to resource upload <ArrowUpRight :size="17" /></RouterLink>
      </section>
    </section>
  </MainLayout>
  <ImageCropper v-if="cropFile" :file="cropFile" :aspect-ratio="4 / 3" @confirm="finishCrop" @skip="finishCrop" @cancel="cancelCrop" />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowUpRight, BookOpen, ImagePlus, MessageCircle, X } from 'lucide-vue-next'
import MainLayout from '../layouts/MainLayout.vue'
import ImageCropper from '../components/ImageCropper.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useAuth } from '../composables/useAuth'
import { getMyProfile } from '../services/profileService'
import { createPost } from '../services/postService'

const router = useRouter()
const { user, initializeAuth } = useAuth()
const mode = ref('post')
const body = ref('')
const selectedMedia = ref([])
const mediaInput = ref(null)
const cropFile = ref(null)
const cropQueue = ref([])
const videoCandidate = ref(null)
const candidateUrl = ref('')
const thumbnailFrames = ref([])
const trimVideoElement = ref(null)
const videoDuration = ref(0)
const trimStart = ref(0)
const trimEnd = ref(0)
const videoError = ref('')
const videoProcessing = ref(false)
const publishing = ref(false)
const error = ref('')
const profile = ref(null)
const displayName = computed(() => profile.value?.display_name || profile.value?.username || user.value?.email || 'Your profile')
const MAX_VIDEO_SIZE = 40 * 1024 * 1024
const trimTimelineStyle = computed(() => ({
  '--trim-start': `${videoDuration.value ? (trimStart.value / videoDuration.value) * 100 : 0}%`,
  '--trim-end': `${videoDuration.value ? (trimEnd.value / videoDuration.value) * 100 : 100}%`,
}))

onMounted(async () => {
  await initializeAuth()
  try { profile.value = await getMyProfile() } catch {}
})

function chooseMedia(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  error.value = ''
  const videoFiles = files.filter((file) => file.type.startsWith('video/'))
  const imageFiles = files.filter((file) => file.type.startsWith('image/'))
  if (videoFiles.length + imageFiles.length !== files.length) { error.value = 'Choose image or video files.'; event.target.value = ''; return }
  if (videoFiles.length && (videoFiles.length > 1 || imageFiles.length || selectedMedia.value.length)) { error.value = 'A post can include one video or multiple images.'; event.target.value = ''; return }
  if (videoFiles.length) {
    const file = videoFiles[0]
    clearVideoCandidate()
    videoCandidate.value = file
    candidateUrl.value = URL.createObjectURL(file)
    videoDuration.value = 0
    trimStart.value = 0
    trimEnd.value = 0
    thumbnailFrames.value = []
    videoError.value = ''
  } else {
    if (videoCandidate.value) { error.value = 'Confirm or remove the selected video before adding images.'; event.target.value = ''; return }
    const invalid = imageFiles.find((file) => file.size > 50 * 1024 * 1024)
    if (invalid) { error.value = 'Images must be 50 MB or smaller.'; event.target.value = ''; return }
    if (selectedMedia.value.some((entry) => entry.type === 'video')) { error.value = 'Remove the video before adding images.'; event.target.value = ''; return }
    cropQueue.value.push(...imageFiles)
    showNextCrop()
  }
  event.target.value = ''
}

function clearMedia() {
  for (const entry of selectedMedia.value) URL.revokeObjectURL(entry.url)
  selectedMedia.value = []
  if (mediaInput.value) mediaInput.value.value = ''
}

function showNextCrop() {
  cropFile.value = cropQueue.value.shift() || null
}
function finishCrop(file) {
  selectedMedia.value.push({ file, url: URL.createObjectURL(file), type: 'image' })
  showNextCrop()
}
function cancelCrop() { cropQueue.value = []; cropFile.value = null }
function removeMedia(index) {
  const [removed] = selectedMedia.value.splice(index, 1)
  if (removed) URL.revokeObjectURL(removed.url)
}

function readVideoDuration() {
  const duration = Number(trimVideoElement.value?.duration || 0)
  if (!Number.isFinite(duration) || duration <= 0) { videoError.value = 'The selected video duration could not be read.'; return }
  videoDuration.value = duration
  trimEnd.value = duration
  generateVideoThumbnails(candidateUrl.value, duration)
}
function clampTrimPoints() {
  trimStart.value = Math.max(0, Math.min(Number(trimStart.value || 0), Math.max(0, videoDuration.value - 0.1)))
  trimEnd.value = Math.max(trimStart.value + 0.1, Math.min(Number(trimEnd.value || 0), videoDuration.value))
}
function updateTrimStart(event) {
  trimStart.value = Math.min(Number(event.target.value), Math.max(0, trimEnd.value - 0.1))
}
function updateTrimEnd(event) {
  trimEnd.value = Math.max(Number(event.target.value), Math.min(videoDuration.value, trimStart.value + 0.1))
}
async function generateVideoThumbnails(url, duration) {
  thumbnailFrames.value = []
  const decoder = document.createElement('video')
  decoder.muted = true
  decoder.playsInline = true
  decoder.preload = 'auto'
  decoder.src = url

  try {
    await new Promise((resolve, reject) => {
      decoder.onloadedmetadata = resolve
      decoder.onerror = () => reject(new Error('Thumbnails are unavailable for this video.'))
    })
    if (decoder.readyState < 2) {
      await new Promise((resolve, reject) => {
        decoder.onloadeddata = resolve
        decoder.onerror = () => reject(new Error('Thumbnails are unavailable for this video.'))
      })
    }
    const canvas = document.createElement('canvas')
    canvas.width = 160
    canvas.height = 90
    const context = canvas.getContext('2d')
    if (!context) return
    const frames = []
    const count = Math.min(8, Math.max(3, Math.ceil(duration / 5)))
    for (let index = 0; index < count; index += 1) {
      if (url !== candidateUrl.value) return
      const time = duration * (index / count)
      if (Math.abs(decoder.currentTime - time) > 0.05) {
        await new Promise((resolve) => {
          decoder.onseeked = resolve
          decoder.currentTime = time
        })
      }
      context.clearRect(0, 0, canvas.width, canvas.height)
      const scale = Math.min(canvas.width / decoder.videoWidth, canvas.height / decoder.videoHeight)
      const width = decoder.videoWidth * scale
      const height = decoder.videoHeight * scale
      context.fillStyle = '#141414'
      context.fillRect(0, 0, canvas.width, canvas.height)
      context.drawImage(decoder, (canvas.width - width) / 2, (canvas.height - height) / 2, width, height)
      frames.push(canvas.toDataURL('image/jpeg', 0.68))
    }
    if (url === candidateUrl.value) thumbnailFrames.value = frames
  } catch {
    // The trim controls remain usable when a codec cannot provide frame previews.
  } finally {
    decoder.pause()
    decoder.removeAttribute('src')
    decoder.load()
  }
}
function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00'
  const whole = Math.floor(seconds)
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, '0')}${Math.floor((seconds % 1) * 10) ? '.' + Math.floor((seconds % 1) * 10) : ''}`
}
function previewClip() {
  clampTrimPoints()
  const video = trimVideoElement.value
  if (!video) return
  video.currentTime = trimStart.value
  video.play().catch(() => { videoError.value = 'Use the video controls to preview this selection.' })
}
function stopClipPreview() {
  if (trimVideoElement.value && trimVideoElement.value.currentTime >= trimEnd.value) trimVideoElement.value.pause()
}
function clearVideoCandidate() {
  if (candidateUrl.value) URL.revokeObjectURL(candidateUrl.value)
  candidateUrl.value = ''
  videoCandidate.value = null
  videoDuration.value = 0
  trimStart.value = 0
  trimEnd.value = 0
  thumbnailFrames.value = []
}
async function confirmVideo(trim) {
  if (!videoCandidate.value || videoProcessing.value) return
  videoError.value = ''
  if (!trim || (trimStart.value <= 0 && trimEnd.value >= videoDuration.value - 0.05)) {
    if (videoCandidate.value.size > MAX_VIDEO_SIZE) { videoError.value = 'The original video is larger than 40 MB. Shorten the selected duration and trim the clip.'; return }
    selectedMedia.value.push({ file: videoCandidate.value, url: candidateUrl.value, type: 'video' })
    candidateUrl.value = ''
    videoCandidate.value = null
    return
  }
  clampTrimPoints()
  if (trimEnd.value <= trimStart.value) { videoError.value = 'Choose an end point after the start point.'; return }
  if (typeof MediaRecorder === 'undefined') { videoError.value = 'This browser cannot trim video here. Choose the original video or use a browser with video recording support.'; return }
  const captureStream = HTMLMediaElement.prototype.captureStream || HTMLMediaElement.prototype.mozCaptureStream
  if (!captureStream) { videoError.value = 'This browser cannot trim video here. Choose the original video or use a browser with video capture support.'; return }
  const mimeType = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'].find((type) => MediaRecorder.isTypeSupported(type))
  if (!mimeType) { videoError.value = 'This browser cannot create a trimmed video file. Choose the original video.'; return }
  videoProcessing.value = true
  const player = document.createElement('video')
  player.src = candidateUrl.value
  player.playsInline = true
  player.preload = 'auto'
  let recordingStream = null
  let recordingRecorder = null
  try {
    await new Promise((resolve, reject) => { player.onloadedmetadata = resolve; player.onerror = () => reject(new Error('This video format cannot be decoded in the browser.')) })
    player.currentTime = trimStart.value
    await new Promise((resolve) => { if (Math.abs(player.currentTime - trimStart.value) < 0.05) resolve(); else player.onseeked = resolve })
    recordingStream = captureStream.call(player)
    const clipSeconds = trimEnd.value - trimStart.value
    const targetAverage = (36 * 1024 * 1024 * 8) / clipSeconds
    const videoBitrate = Math.min(2200000, Math.max(100000, Math.floor(targetAverage - 128000)))
    recordingRecorder = new MediaRecorder(recordingStream, { mimeType, videoBitsPerSecond: videoBitrate, audioBitsPerSecond: 128000 })
    const chunks = []
    const output = new Promise((resolve, reject) => {
      recordingRecorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data) }
      recordingRecorder.onerror = () => reject(new Error('The selected video could not be trimmed.'))
      recordingRecorder.onstop = () => resolve(new Blob(chunks, { type: mimeType.split(';')[0] }))
    })
    recordingRecorder.start(200)
    const endWhenReady = () => {
      if (player.currentTime >= trimEnd.value && recordingRecorder.state === 'recording') { player.pause(); recordingRecorder.stop() }
      else if (recordingRecorder.state === 'recording') requestAnimationFrame(endWhenReady)
    }
    player.ontimeupdate = endWhenReady
    await player.play()
    const blob = await Promise.race([output, new Promise((_, reject) => setTimeout(() => reject(new Error('Video processing took too long.')), Math.max(30000, (trimEnd.value - trimStart.value) * 2500)))])
    if (!blob.size) throw new Error('The selected video clip is empty.')
    if (blob.size > MAX_VIDEO_SIZE) throw new Error('The trimmed video is larger than 40 MB. Shorten the clip and try again.')
    const file = new File([blob], videoCandidate.value.name.replace(/\.[^.]+$/, '') + '-trimmed.webm', { type: blob.type, lastModified: Date.now() })
    selectedMedia.value.push({ file, url: URL.createObjectURL(file), type: 'video' })
    clearVideoCandidate()
  } catch (err) {
    videoError.value = err.message || 'Video processing failed. Choose the original video or try another format.'
  } finally {
    if (recordingRecorder?.state === 'recording') recordingRecorder.stop()
    for (const track of recordingStream?.getTracks?.() || []) track.stop()
    player.pause()
    player.removeAttribute('src')
    videoProcessing.value = false
  }
}

async function publishPost() {
  if (!body.value.trim() && !selectedMedia.value.length) return
  publishing.value = true
  error.value = ''
  try {
    await createPost({ body: body.value.trim(), media: selectedMedia.value.map((entry) => entry.file) })
    clearMedia()
    await router.push({ name: 'home' })
  } catch (err) {
    error.value = err.message || 'Your post could not be shared.'
  } finally {
    publishing.value = false
  }
}

onBeforeUnmount(() => { clearMedia(); clearVideoCandidate() })
</script>

<style scoped>
.create-page { width:min(760px,100%); margin:0 auto; padding-bottom:30px; }
.create-heading { display:flex; align-items:flex-end; justify-content:space-between; gap:20px; margin:2px 0 28px; }
.page-kicker { margin:0 0 10px; color:var(--text-tertiary); font-size:10px; font-weight:750; letter-spacing:.15em; }
.create-heading h1 { margin:0; font:800 clamp(32px,5vw,49px)/1.08 Manrope,sans-serif; letter-spacing:-.055em; }
.create-heading p:not(.page-kicker) { margin:10px 0 0; color:var(--text-secondary); line-height:1.6; }
.back-link { flex-shrink:0; display:flex; align-items:center; gap:7px; color:var(--text-secondary); font-size:13px; font-weight:650; }
.create-switch { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px; }
.create-switch button { display:flex; align-items:center; gap:13px; min-height:78px; padding:15px; border:1px solid var(--border-color); border-radius:17px; background:var(--card-bg); color:var(--text-secondary); text-align:left; transition:border .18s, background .18s; }
.create-switch button.selected { border-color:var(--text-main); background:var(--card-soft); color:var(--text-main); }
.create-switch button > span { display:grid; gap:4px; }
.create-switch strong { color:var(--text-main); font-size:13px; }
.create-switch small { color:var(--text-secondary); font-size:11px; }
.post-composer,.resource-choice { border:1px solid var(--border-color); border-radius:22px; background:var(--card-bg); box-shadow:0 8px 28px var(--shadow-color); }
.post-composer { padding:22px; }
.composer-top { display:flex; align-items:center; gap:12px; padding-bottom:18px; border-bottom:1px solid var(--border-soft); }
.avatar { width:42px; height:42px; display:grid; place-items:center; border-radius:50%; background:var(--icon-bg); color:var(--text-main); font-weight:750; }
.composer-top strong,.composer-top span { display:block; }
.composer-top strong { font-size:13px; }
.composer-top span { margin-top:3px; color:var(--text-tertiary); font-size:11px; }
textarea { width:100%; resize:vertical; min-height:155px; padding:20px 0; border:0; outline:0; background:transparent; color:var(--text-main); font:500 18px/1.6 'DM Sans',sans-serif; }
textarea::placeholder { color:var(--text-tertiary); }
.composer-footer { display:flex; align-items:center; justify-content:space-between; gap:16px; padding-top:16px; border-top:1px solid var(--border-soft); }
.composer-tools { display:flex; align-items:center; gap:16px; }
#post-media { display:none; }
.attach-button { display:inline-flex; align-items:center; gap:7px; color:var(--text-secondary); font-size:12px; font-weight:650; cursor:pointer; }
.char-count { color:var(--text-tertiary); font-size:11px; }
.publish-button { display:inline-flex; align-items:center; justify-content:center; gap:9px; min-height:45px; padding:0 17px; border-radius:13px; background:var(--primary-bg); color:var(--primary-text); font-size:12px; font-weight:700; }
.publish-button:disabled { cursor:not-allowed; opacity:.5; }
.media-preview { position:relative; overflow:hidden; margin:0 0 16px; border-radius:15px; background:var(--icon-bg); }
.media-preview img,.media-preview video { display:block; width:100%; max-height:480px; object-fit:contain; }
.media-preview-list { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:9px; margin:0 0 16px; }
.media-preview-list .media-preview { margin:0; }
.video-trim-panel { display:grid; gap:10px; margin:0 0 17px; padding:13px; border:1px solid var(--border-color); border-radius:14px; background:var(--card-soft); }
.video-trim-panel video { display:block; width:100%; max-height:350px; border-radius:9px; background:#111; }
.video-limit,.duration-label { margin:0; color:var(--text-secondary); font-size:11px; }
.video-limit span { color:#a33b30; }
.trim-timeline { position:relative; height:54px; overflow:hidden; border:1px solid var(--border-color); border-radius:10px; background:var(--icon-bg); }
.trim-frames { position:absolute; inset:0; display:flex; align-items:stretch; overflow:hidden; color:var(--text-tertiary); font-size:11px; }
.trim-frames img { flex:1 1 0; min-width:0; height:100%; object-fit:cover; }
.trim-frames span { width:100%; display:grid; place-items:center; background:linear-gradient(90deg,var(--card-soft),var(--icon-bg)); }
.trim-selection { position:absolute; top:0; bottom:0; left:var(--trim-start); width:calc(var(--trim-end) - var(--trim-start)); border:2px solid var(--primary-bg); border-radius:5px; box-shadow:0 0 0 100vw rgba(0,0,0,.4); pointer-events:none; }
.trim-range { position:absolute; inset:0; width:100%; height:100%; margin:0; appearance:none; background:transparent; pointer-events:none; touch-action:none; }
.trim-range.trim-start { z-index:2; }
.trim-range.trim-end { z-index:3; }
.trim-range::-webkit-slider-runnable-track { height:100%; background:transparent; }
.trim-range::-moz-range-track { height:100%; background:transparent; }
.trim-range::-webkit-slider-thumb { width:21px; height:46px; appearance:none; border:3px solid var(--card-bg); border-radius:7px; background:var(--primary-bg); box-shadow:0 1px 7px rgba(0,0,0,.35); cursor:ew-resize; pointer-events:auto; }
.trim-range::-moz-range-thumb { width:15px; height:40px; border:3px solid var(--card-bg); border-radius:7px; background:var(--primary-bg); box-shadow:0 1px 7px rgba(0,0,0,.35); cursor:ew-resize; pointer-events:auto; }
.trim-range:focus-visible::-webkit-slider-thumb { outline:2px solid var(--text-main); outline-offset:2px; }
.trim-range:focus-visible::-moz-range-thumb { outline:2px solid var(--text-main); outline-offset:2px; }
.trim-time-labels { display:flex; justify-content:space-between; gap:12px; color:var(--text-tertiary); font-size:10px; }
.trim-time-labels strong,.selected-duration strong { color:var(--text-main); font-weight:750; }
.selected-duration { font-size:12px; }
.trim-fields { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.trim-fields label { display:flex; align-items:center; gap:7px; color:var(--text-secondary); font-size:11px; }
.trim-fields input { width:100%; min-width:0; padding:8px; border:1px solid var(--border-color); border-radius:8px; background:var(--input-bg); color:var(--text-main); }
.trim-actions { display:flex; flex-wrap:wrap; gap:7px; }
.trim-actions button { min-height:34px; padding:0 10px; border:1px solid var(--border-color); border-radius:9px; background:var(--card-bg); color:var(--text-secondary); font-size:10px; font-weight:700; }
.trim-actions .trim-confirm { border-color:var(--primary-bg); background:var(--primary-bg); color:var(--primary-text); }
.trim-actions button:disabled { opacity:.5; }
.remove-media { position:absolute; top:10px; right:10px; width:34px; height:34px; display:grid; place-items:center; border-radius:50%; background:rgba(20,20,20,.76); color:white; }
.form-message { margin:0 0 12px; font-size:12px; }
.form-message.error { color:#a33b30; }
.resource-choice { display:flex; flex-direction:column; align-items:flex-start; padding:30px; }
.resource-choice-icon { width:54px; height:54px; display:grid; place-items:center; border-radius:17px; background:var(--icon-bg); }
.resource-choice h2 { margin:22px 0 0; font:750 25px Manrope,sans-serif; letter-spacing:-.035em; }
.resource-choice p { max-width:560px; margin:10px 0 22px; color:var(--text-secondary); font-size:14px; line-height:1.7; }
.sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }
@media(max-width:560px) {
  .create-heading { align-items:flex-start; }
  .back-link { margin-top:3px; }
  .create-switch { grid-template-columns:1fr; gap:8px; }
  .create-switch button { min-height:66px; }
  .post-composer { padding:16px; border-radius:18px; }
  textarea { min-height:130px; font-size:16px; }
  .composer-footer { align-items:flex-end; }
  .composer-tools { gap:9px; }
  .attach-button span { display:none; }
  .publish-button { padding:0 13px; }
  .resource-choice { padding:23px; }
  .trim-timeline { height:60px; }
  .trim-range::-webkit-slider-thumb { width:25px; height:52px; }
  .trim-range::-moz-range-thumb { width:19px; height:46px; }
}
</style>
