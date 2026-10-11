<template>
  <article v-if="!isDeleted" class="feed-card">
    <header class="card-header">
      <RouterLink :to="profileRoute" class="creator-link">
        <div class="avatar">
          <img
            v-if="authorAvatarUrl && !authorAvatarFailed"
            :src="authorAvatarUrl"
            alt=""
            @error="authorAvatarFailed = true"
          />
          <span v-else>{{ initial }}</span>
        </div>

        <span class="creator-copy">
          <strong>{{ author?.display_name || author?.username || 'Follia creator' }}</strong>
          <small>
            {{ author?.username ? '@' + author.username : 'Creator' }}
            <span>·</span>
            {{ timeAgo }}
          </small>
        </span>
      </RouterLink>

      <div class="header-actions">
        <button
          v-if="showFollow"
          class="follow-button"
          :class="{ following }"
          @click="toggleFollow"
        >
          {{ following ? 'Following' : 'Follow' }}
        </button>

        <button
          class="more-button"
          aria-label="More post actions"
          @click="showMenu = !showMenu"
        >
          <MoreHorizontal :size="19" />
        </button>

        <div v-if="showMenu" class="action-menu">
          <template v-if="item.kind === 'post' && item.is_owner">
            <button @click="beginEdit"><Pencil :size="15" /> Edit post</button>
            <button @click="removePost"><Trash2 :size="15" /> Delete post</button>
          </template>

          <button v-else @click="reportContent">
            <Flag :size="15" /> Report
          </button>
        </div>
      </div>
    </header>

    <div v-if="item.kind === 'resource'" class="resource-body">
      <div class="resource-copy">
        <span class="resource-label">
          <BookOpen :size="14" />
          {{ item.category || 'Library resource' }}
        </span>

        <RouterLink
          :to="{ name: 'resource-detail', params: { id: item.id } }"
          class="resource-title"
        >
          {{ item.title }}
        </RouterLink>

        <p v-if="item.description">{{ item.description }}</p>

        <RouterLink
          :to="{ name: 'resource-detail', params: { id: item.id } }"
          class="resource-open"
        >
          Explore resource <ArrowUpRight :size="15" />
        </RouterLink>
      </div>

      <RouterLink
        :to="{ name: 'resource-detail', params: { id: item.id } }"
        class="resource-cover"
      >
        <img
          v-if="resourceCoverUrl && !resourceCoverFailed"
          :src="resourceCoverUrl"
          :alt="item.title"
          loading="lazy"
          @error="resourceCoverFailed = true"
        />

        <div v-else>
          <BookOpen :size="29" />
          <span>{{ item.file_type || 'Follia resource' }}</span>
        </div>
      </RouterLink>
    </div>

    <div v-else class="post-body">
      <form v-if="editing" class="post-editor" @submit.prevent="saveEdit">
        <textarea
          v-model="editBody"
          maxlength="5000"
          rows="4"
          aria-label="Edit post text"
        ></textarea>

        <div class="editor-actions">
          <button
            type="button"
            class="cancel-edit"
            @click="editing = false"
          >
            <X :size="15" /> Cancel
          </button>

          <button class="save-edit" :disabled="savingEdit">
            <Check :size="15" />
            {{ savingEdit ? 'Saving…' : 'Save changes' }}
          </button>
        </div>
      </form>

      <p v-else-if="currentBody" class="post-text">{{ currentBody }}</p>

      <div
        v-if="postMediaUrl && !postMediaFailed"
        class="post-media"
      >
        <video
          v-if="item.media_type === 'video'"
          :src="postMediaUrl"
          controls
          playsinline
          preload="metadata"
          @error="postMediaFailed = true"
        ></video>

        <img
          v-else
          :src="postMediaUrl"
          alt="Post media"
          loading="lazy"
          @error="postMediaFailed = true"
        />
      </div>
    </div>

    <div class="card-actions">
      <button
        class="engagement-button"
        :class="{ liked }"
        :aria-label="liked ? 'Unlike' : 'Like'"
        @click="toggleLike"
      >
        <Heart :size="19" :fill="liked ? 'currentColor' : 'none'" />
        <span>{{ likeCount }}</span>
      </button>

      <button
        class="engagement-button"
        :aria-label="'Comments, ' + commentCount"
        @click="toggleComments"
      >
        <MessageCircle :size="19" />
        <span>{{ commentCount }}</span>
      </button>

      <button class="engagement-button" aria-label="Share" @click="share">
        <Share2 :size="18" />
        <span class="action-word">Share</span>
      </button>

      <button
        class="save-button"
        :class="{ saved }"
        :aria-label="saved ? 'Remove saved item' : 'Save item'"
        @click="toggleSave"
      >
        <Bookmark :size="19" :fill="saved ? 'currentColor' : 'none'" />
        <span class="action-word">{{ saved ? 'Saved' : 'Save' }}</span>
      </button>
    </div>

    <section v-if="commentsOpen" class="comments-panel">
      <div v-if="commentsLoading" class="comments-state">
        Loading conversation…
      </div>

      <div v-else-if="comments.length" class="comments-list">
        <div v-for="comment in comments" :key="comment.id" class="comment">
          <div class="comment-avatar">
            {{
              (
                comment.profiles?.display_name ||
                comment.profiles?.username ||
                'F'
              ).charAt(0).toUpperCase()
            }}
          </div>

          <div>
            <strong>
              {{
                comment.profiles?.display_name ||
                comment.profiles?.username ||
                'Follia reader'
              }}
            </strong>
            <p>{{ comment.content }}</p>
          </div>
        </div>
      </div>

      <div v-else class="comments-state">Start the conversation.</div>

      <form class="comment-form" @submit.prevent="submitComment">
        <input
          v-model="commentText"
          maxlength="2000"
          placeholder="Add a thoughtful reply…"
          aria-label="Write a comment"
        />

        <button
          :disabled="!commentText.trim() || commentSubmitting"
          aria-label="Send comment"
        >
          <Send :size="16" />
        </button>
      </form>
    </section>

    <div v-if="toast" class="toast">{{ toast }}</div>
  </article>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  ArrowUpRight,
  BookOpen,
  Bookmark,
  Check,
  Flag,
  Heart,
  MessageCircle,
  MoreHorizontal,
  Pencil,
  Send,
  Share2,
  Trash2,
  X,
} from 'lucide-vue-next'

import { useAuth } from '../composables/useAuth'
import { toggleBookmark } from '../services/bookmarkService'
import {
  addResourceComment,
  getResourceComments,
} from '../services/commentService'
import { followUser, unfollowUser } from '../services/followService'
import { reportPost, reportPublisher } from '../services/reportService'
import {
  addPostComment,
  deletePost,
  getPostComments,
  togglePostLike,
  togglePostSave,
  updatePost,
} from '../services/postService'
import { toggleResourceLike } from '../services/resourceLikeService'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
})

const { user, initializeAuth } = useAuth()

// Read the backend address from the Vue environment configuration.
// Example: VITE_API_URL=http://127.0.0.1:8000/api
const configuredApiUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL

const API_BASE_URL = (
  configuredApiUrl ||
  (import.meta.env.DEV
    ? 'http://127.0.0.1:8000'
    : window.location.origin)
)
  .replace(/\/+$/, '')
  .replace(/\/api$/i, '')

// Convert a relative Django media path into a complete URL.
// Keep complete external URLs and local blob previews unchanged.
function resolveMediaUrl(url) {
  if (!url || typeof url !== 'string') return null

  const value = url.trim()
  if (!value) return null

  if (
    /^https?:\/\//i.test(value) ||
    value.startsWith('blob:') ||
    value.startsWith('data:')
  ) {
    return value
  }

  if (value.startsWith('//')) {
    return `${window.location.protocol}${value}`
  }

  try {
    return new URL(value, `${API_BASE_URL}/`).href
  } catch {
    return null
  }
}

const liked = ref(Boolean(props.item.liked))
const saved = ref(Boolean(props.item.saved))
const likeCount = ref(props.item.like_count || 0)
const commentCount = ref(props.item.comment_count || 0)

const following = ref(
  Boolean(props.item.author?.is_following || props.item.profiles?.is_following)
)

const commentsOpen = ref(false)
const comments = ref([])
const commentsLoading = ref(false)
const commentSubmitting = ref(false)
const commentText = ref('')
const showMenu = ref(false)
const isDeleted = ref(false)
const editing = ref(false)
const savingEdit = ref(false)

const currentBody = ref(props.item.body || '')
const editBody = ref(props.item.body || '')
const toast = ref('')

const authorAvatarFailed = ref(false)
const resourceCoverFailed = ref(false)
const postMediaFailed = ref(false)

let toastTimer = null

const author = computed(() => props.item.author || props.item.profiles || {})

const authorAvatarUrl = computed(() =>
  resolveMediaUrl(
    author.value.avatar_url ||
    author.value.avatar ||
    author.value.user?.avatar_url
  )
)

const resourceCoverUrl = computed(() =>
  resolveMediaUrl(props.item.cover_url || props.item.cover)
)

const postMediaUrl = computed(() =>
  resolveMediaUrl(props.item.media_url || props.item.media)
)

const initial = computed(() =>
  (author.value.display_name || author.value.username || 'F')
    .charAt(0)
    .toUpperCase()
)

const profileRoute = computed(() => ({
  name: 'publisher-detail',
  params: {
    id: author.value.id || props.item.author_id,
  },
}))

const showFollow = computed(() =>
  Boolean(
    author.value.id &&
    String(author.value.id) !== String(user.value?.id)
  )
)

const timeAgo = computed(() => {
  const seconds = Math.max(
    0,
    Math.floor((Date.now() - new Date(props.item.created_at).getTime()) / 1000)
  )

  if (seconds < 60) return 'now'
  if (seconds < 3600) return Math.floor(seconds / 60) + 'm'
  if (seconds < 86400) return Math.floor(seconds / 3600) + 'h'

  return Math.floor(seconds / 86400) + 'd'
})

function notify(message) {
  toast.value = message

  window.clearTimeout(toastTimer)

  toastTimer = window.setTimeout(() => {
    toast.value = ''
  }, 2400)
}

async function toggleLike() {
  await initializeAuth()

  const previous = liked.value

  liked.value = !previous
  likeCount.value = Math.max(
    0,
    likeCount.value + (previous ? -1 : 1)
  )

  try {
    const result = props.item.kind === 'resource'
      ? await toggleResourceLike(props.item.id, previous)
      : await togglePostLike(props.item.id, previous)

    if (result?.count !== undefined) {
      likeCount.value = result.count
    }
  } catch (error) {
    liked.value = previous
    likeCount.value = Math.max(
      0,
      likeCount.value + (previous ? 1 : -1)
    )

    notify(error.message || 'Sign in to like this.')
  }
}

async function toggleSave() {
  await initializeAuth()

  const previous = saved.value
  saved.value = !previous

  try {
    if (props.item.kind === 'resource') {
      await toggleBookmark(props.item.id, previous)
    } else {
      await togglePostSave(props.item.id, previous)
    }
  } catch (error) {
    saved.value = previous
    notify(error.message || 'Sign in to save this.')
  }
}

async function toggleFollow() {
  await initializeAuth()

  const previous = following.value
  following.value = !previous

  try {
    await (
      previous
        ? unfollowUser(author.value.id)
        : followUser(author.value.id)
    )
  } catch (error) {
    following.value = previous
    notify(error.message || 'Unable to update following.')
  }
}

async function toggleComments() {
  commentsOpen.value = !commentsOpen.value

  if (!commentsOpen.value || comments.value.length) return

  commentsLoading.value = true

  try {
    comments.value = props.item.kind === 'resource'
      ? await getResourceComments(props.item.id)
      : await getPostComments(props.item.id)
  } catch (error) {
    notify(error.message || 'Unable to load comments.')
  } finally {
    commentsLoading.value = false
  }
}

async function submitComment() {
  const text = commentText.value.trim()

  if (!text || commentSubmitting.value) return

  commentSubmitting.value = true

  try {
    const comment = props.item.kind === 'resource'
      ? await addResourceComment(props.item.id, text)
      : await addPostComment(props.item.id, text)

    comments.value.push(comment)
    commentCount.value += 1
    commentText.value = ''
  } catch (error) {
    notify(error.message || 'Unable to add your reply.')
  } finally {
    commentSubmitting.value = false
  }
}

async function share() {
  const url =
    window.location.origin +
    (props.item.kind === 'resource' ? '/resource/' : '/post/') +
    props.item.id

  try {
    if (navigator.share) {
      await navigator.share({
        title: props.item.title || 'Follia',
        text:
          props.item.body ||
          props.item.description ||
          'Discover this on Follia.',
        url,
      })
    } else {
      await navigator.clipboard.writeText(url)
      notify('Link copied.')
    }
  } catch (error) {
    if (error.name !== 'AbortError') {
      notify('Unable to share this item.')
    }
  }
}

async function reportContent() {
  showMenu.value = false

  try {
    const reason = window.prompt(
      'What should we know about this content?',
      'other'
    )

    if (!reason) return

    if (props.item.kind === 'resource') {
      await reportPublisher({
        reportedUserId: props.item.author_id,
        reason,
        description: '',
      })
    } else {
      await reportPost(props.item.id, reason, '')
    }

    notify('Thanks. Your report was sent.')
  } catch (error) {
    notify(error.message || 'Unable to send your report.')
  }
}

async function removePost() {
  showMenu.value = false

  if (!window.confirm('Delete this post?')) return

  try {
    await deletePost(props.item.id)
    isDeleted.value = true
    notify('Post deleted.')
  } catch (error) {
    notify(error.message || 'Unable to delete this post.')
  }
}

function beginEdit() {
  editBody.value = currentBody.value
  editing.value = true
  showMenu.value = false
}

async function saveEdit() {
  savingEdit.value = true

  try {
    const updated = await updatePost(
      props.item.id,
      editBody.value.trim()
    )

    currentBody.value = updated.body || ''
    editing.value = false

    notify('Post updated.')
  } catch (error) {
    notify(error.message || 'Unable to update your post.')
  } finally {
    savingEdit.value = false
  }
}
</script>

<style scoped>
.feed-card { position:relative; padding:19px 20px 13px; border:1px solid var(--border-color); border-radius:20px; background:var(--card-bg); box-shadow:0 4px 18px color-mix(in srgb,var(--shadow-color) 45%,transparent); }
.card-header { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.creator-link { display:flex; align-items:center; min-width:0; gap:11px; }
.avatar { width:42px; height:42px; flex:0 0 42px; display:grid; place-items:center; overflow:hidden; border-radius:50%; background:var(--icon-bg); color:var(--text-main); font-size:14px; font-weight:750; }
.avatar img { width:100%; height:100%; object-fit:cover; }
.creator-copy { min-width:0; }
.creator-copy strong,.creator-copy small { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.creator-copy strong { max-width:250px; color:var(--text-main); font-size:13px; font-weight:750; }
.creator-copy small { margin-top:3px; color:var(--text-tertiary); font-size:11px; }
.creator-copy small span { padding:0 3px; }
.header-actions { position:relative; display:flex; align-items:center; gap:8px; }
.follow-button { padding:8px 12px; border:1px solid var(--border-color); border-radius:999px; background:var(--text-main); color:var(--card-bg); font-size:11px; font-weight:700; }
.follow-button.following { background:transparent; color:var(--text-secondary); }
.more-button { width:34px; height:34px; display:grid; place-items:center; border-radius:50%; background:transparent; color:var(--text-tertiary); }
.more-button:hover { background:var(--hover-bg); color:var(--text-main); }
.action-menu { position:absolute; top:38px; right:0; z-index:10; min-width:140px; padding:5px; border:1px solid var(--border-color); border-radius:12px; background:var(--card-bg); box-shadow:0 8px 25px var(--shadow-color); }
.action-menu button { width:100%; display:flex; align-items:center; gap:8px; padding:10px; border-radius:8px; background:transparent; color:var(--text-main); text-align:left; font-size:12px; }
.action-menu button:hover { background:var(--hover-bg); }
.post-body { padding-top:15px; }
.post-text { margin:0; white-space:pre-wrap; overflow-wrap:anywhere; color:var(--text-main); font-size:14px; line-height:1.65; }
.post-editor { display:grid; gap:9px; margin:0 0 13px; }
.post-editor textarea { width:100%; padding:11px; border:1px solid var(--border-color); border-radius:12px; outline:0; background:var(--input-bg); color:var(--text-main); font:13px/1.6 'DM Sans',sans-serif; resize:vertical; }
.editor-actions { display:flex; justify-content:flex-end; gap:8px; }
.editor-actions button { min-height:34px; display:inline-flex; align-items:center; gap:6px; padding:0 10px; border-radius:9px; font-size:10px; font-weight:700; }
.cancel-edit { border:1px solid var(--border-color); background:transparent; color:var(--text-secondary); }
.save-edit { background:var(--primary-bg); color:var(--primary-text); }
.save-edit:disabled { opacity:.5; }
.post-media { overflow:hidden; margin-top:14px; border:1px solid var(--border-soft); border-radius:15px; background:var(--card-soft); }
.post-media img,.post-media video { display:block; width:100%; max-height:600px; object-fit:contain; }
.resource-body { display:flex; align-items:center; justify-content:space-between; gap:18px; margin:16px 0 13px; padding:17px; border:1px solid var(--border-soft); border-radius:16px; background:var(--card-soft); }
.resource-copy { min-width:0; }
.resource-label { display:inline-flex; align-items:center; gap:6px; color:var(--text-tertiary); font-size:10px; font-weight:700; letter-spacing:.07em; text-transform:uppercase; }
.resource-title { display:block; margin:9px 0 5px; font:750 19px/1.27 Manrope,sans-serif; letter-spacing:-.035em; }
.resource-copy p { display:-webkit-box; margin:0; color:var(--text-secondary); font-size:12px; line-height:1.55; overflow:hidden; -webkit-box-orient:vertical; -webkit-line-clamp:2; }
.resource-open { display:inline-flex; align-items:center; gap:5px; margin-top:12px; color:var(--text-main); font-size:11px; font-weight:700; }
.resource-cover { width:100px; height:126px; flex:0 0 100px; overflow:hidden; border-radius:9px; background:var(--icon-bg); }
.resource-cover img { width:100%; height:100%; object-fit:cover; }
.resource-cover div { width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:7px; padding:8px; color:var(--text-tertiary); text-align:center; }
.resource-cover span { font-size:9px; }
.card-actions { display:flex; align-items:center; gap:18px; padding:11px 1px 0; border-top:1px solid var(--border-soft); }
.engagement-button,.save-button { display:inline-flex; align-items:center; gap:7px; padding:5px 2px; background:transparent; color:var(--text-tertiary); font-size:11px; }
.engagement-button:hover,.save-button:hover { color:var(--text-main); }
.engagement-button.liked { color:#9e463a; }
.save-button { margin-left:auto; }
.save-button.saved { color:var(--text-main); }
.comments-panel { margin:11px -2px 0; padding-top:13px; border-top:1px solid var(--border-soft); }
.comments-state { padding:8px 0; color:var(--text-tertiary); font-size:12px; }
.comments-list { display:grid; gap:13px; max-height:240px; overflow:auto; }
.comment { display:flex; align-items:flex-start; gap:9px; }
.comment-avatar { width:28px; height:28px; flex:0 0 28px; display:grid; place-items:center; border-radius:50%; background:var(--icon-bg); font-size:10px; font-weight:700; }
.comment strong { display:block; margin:1px 0 3px; font-size:11px; }
.comment p { margin:0; color:var(--text-secondary); font-size:12px; line-height:1.5; white-space:pre-wrap; }
.comment-form { display:flex; gap:9px; margin-top:13px; }
.comment-form input { flex:1; min-width:0; height:40px; padding:0 12px; border:1px solid var(--border-color); border-radius:12px; outline:0; background:var(--input-bg); color:var(--text-main); font-size:12px; }
.comment-form input:focus { border-color:var(--text-tertiary); }
.comment-form button { width:40px; flex:0 0 40px; display:grid; place-items:center; border-radius:12px; background:var(--primary-bg); color:var(--primary-text); }
.comment-form button:disabled { opacity:.5; }
.toast { position:absolute; right:14px; bottom:64px; padding:10px 13px; border-radius:10px; background:var(--text-main); color:var(--card-bg); font-size:11px; box-shadow:0 5px 16px var(--shadow-color); }
@media(max-width:480px) {
  .feed-card { padding:15px 14px 11px; border-radius:17px; }
  .avatar { width:38px; height:38px; flex-basis:38px; }
  .creator-copy strong { max-width:165px; font-size:12px; }
  .creator-copy small { font-size:10px; }
  .follow-button { padding:7px 10px; font-size:10px; }
  .header-actions { gap:3px; }
  .resource-body { gap:10px; padding:13px; }
  .resource-title { font-size:16px; }
  .resource-cover { width:80px; height:106px; flex-basis:80px; }
  .post-text { font-size:13px; }
  .card-actions { gap:14px; }
  .action-word { display:none; }
}
</style>
