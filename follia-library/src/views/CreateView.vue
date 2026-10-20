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
        <div v-if="mediaPreview" class="media-preview">
          <video v-if="media?.type.startsWith('video/')" :src="mediaPreview" controls playsinline />
          <img v-else :src="mediaPreview" alt="Post preview" />
          <button type="button" class="remove-media" aria-label="Remove media" @click="clearMedia"><X :size="16" /></button>
        </div>
        <div v-if="error" class="form-message error">{{ error }}</div>
        <div class="composer-footer">
          <div class="composer-tools">
            <label class="attach-button" for="post-media"><ImagePlus :size="19" /><span>Photo or video</span></label>
            <input id="post-media" ref="mediaInput" type="file" accept="image/*,video/*" @change="chooseMedia" />
            <span class="char-count">{{ body.length }}/5000</span>
          </div>
          <button class="publish-button" type="submit" :disabled="publishing || (!body.trim() && !media)">
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
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowUpRight, BookOpen, ImagePlus, MessageCircle, X } from 'lucide-vue-next'
import MainLayout from '../layouts/MainLayout.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useAuth } from '../composables/useAuth'
import { getMyProfile } from '../services/profileService'
import { createPost } from '../services/postService'

const router = useRouter()
const { user, initializeAuth } = useAuth()
const mode = ref('post')
const body = ref('')
const media = ref(null)
const mediaPreview = ref('')
const mediaInput = ref(null)
const publishing = ref(false)
const error = ref('')
const profile = ref(null)
const displayName = computed(() => profile.value?.display_name || profile.value?.username || user.value?.email || 'Your profile')

onMounted(async () => {
  await initializeAuth()
  try { profile.value = await getMyProfile() } catch {}
})

function chooseMedia(event) {
  const file = event.target.files?.[0]
  if (!file) return
  error.value = ''
  if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
    error.value = 'Choose an image or video file.'
    event.target.value = ''
    return
  }
  if (file.size > 50 * 1024 * 1024) {
    error.value = 'Choose a file smaller than 50 MB.'
    event.target.value = ''
    return
  }
  clearMedia()
  media.value = file
  mediaPreview.value = URL.createObjectURL(file)
  error.value = ''
}

function clearMedia() {
  if (mediaPreview.value?.startsWith('blob:')) URL.revokeObjectURL(mediaPreview.value)
  media.value = null
  mediaPreview.value = ''
  if (mediaInput.value) mediaInput.value.value = ''
}

async function publishPost() {
  if (!body.value.trim() && !media.value) return
  publishing.value = true
  error.value = ''
  try {
    await createPost({ body: body.value.trim(), media: media.value })
    clearMedia()
    await router.push({ name: 'home' })
  } catch (err) {
    error.value = err.message || 'Your post could not be shared.'
  } finally {
    publishing.value = false
  }
}

onBeforeUnmount(clearMedia)
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
}
</style>
