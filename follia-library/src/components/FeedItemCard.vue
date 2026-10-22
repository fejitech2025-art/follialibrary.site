<template>
  <article v-if="!isDeleted" class="feed-card">
    <header class="card-header">
      <RouterLink :to="profileRoute" class="creator-link">
        <div class="avatar">
          <UserAvatar :src="authorAvatarUrl" :alt="author?.display_name || author?.username || 'Profile picture'" :icon-size="20" />
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

          <button v-else @click="openReport(item.kind === 'resource' ? 'resource' : 'post')">
            <Flag :size="15" /> Report
          </button>
          <button v-if="showFollow" @click="openReport('profile')"><Flag :size="15" /> Report profile</button>
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

      <p v-else-if="currentBody" class="post-text"><template v-for="(segment, index) in bodySegments" :key="index"><RouterLink v-if="segment.tag" :to="{ name: 'search', query: { q: '#' + segment.text } }" class="hashtag">#{{ segment.text }}</RouterLink><template v-else>{{ segment.text }}</template></template></p>

      <div v-if="mediaItems.length && !postMediaFailed" class="post-media">
        <video
          v-if="mediaItems[0].media_type === 'video'"
          ref="videoElement"
          :src="postMediaUrl"
          controls
          playsinline
          preload="none"
          @play="handleVideoPlay"
          @pause="handleVideoPause"
          @error="postMediaFailed = true"
        ></video>

        <div v-else-if="mediaItems.length > 1" class="image-carousel">
          <div ref="imageTrack" class="image-track" @scroll.passive="handleImageScroll">
            <img v-for="(media, index) in mediaItems" :key="media.id || index" :src="resolveMediaUrl(media.url)" :alt="'Post image ' + (index + 1)" :aria-label="'Preview image ' + (index + 1)" role="button" tabindex="0" loading="lazy" @click.stop="openImagePreview(index)" @keydown.enter.stop.prevent="openImagePreview(index)" @keydown.space.stop.prevent="openImagePreview(index)" @error="postMediaFailed = true" />
          </div>
          <button v-if="activeImage > 0" class="carousel-arrow previous" type="button" aria-label="Previous image" @click="slideImage(-1)">‹</button>
          <button v-if="activeImage < mediaItems.length - 1" class="carousel-arrow next" type="button" aria-label="Next image" @click="slideImage(1)">›</button>
          <span class="image-count">{{ activeImage + 1 }} / {{ mediaItems.length }}</span>
          <div class="image-dots"><button v-for="(_, index) in mediaItems" :key="index" type="button" :class="{ active: index === activeImage }" :aria-label="'Show image ' + (index + 1)" @click="goToImage(index)"></button></div>
        </div>

        <img v-else :src="postMediaUrl" alt="Post image" role="button" tabindex="0" aria-label="Preview image" loading="lazy" @click.stop="openImagePreview(0)" @keydown.enter.stop.prevent="openImagePreview(0)" @keydown.space.stop.prevent="openImagePreview(0)" @error="postMediaFailed = true" />
        <a v-if="activeMediaDownloadUrl" class="media-download" :href="activeMediaDownloadUrl"><Download :size="14" /> Download {{ mediaItems[0].media_type === 'video' ? 'video' : 'image' }}</a>
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

    <Teleport to="body">
      <div v-if="commentsOpen" class="comments-overlay" :style="commentsViewportStyle" @click.self="closeComments">
        <section class="comments-modal" role="dialog" aria-modal="true" aria-labelledby="comments-title">
          <header class="comments-header">
            <div><p class="comments-kicker">DISCUSSION</p><h2 id="comments-title">Comments</h2></div>
            <button class="comments-close" type="button" aria-label="Close comments" @click="closeComments"><X :size="19" /></button>
          </header>

          <div class="comments-list">
            <div v-if="commentsLoading" class="comments-state">Loading conversation…</div>
            <div v-else-if="commentsError" class="comments-state comments-error" role="alert">
              <span>{{ commentsError }}</span>
              <button type="button" @click="loadComments">Try again</button>
            </div>
            <template v-else-if="comments.length">
              <article v-for="comment in comments" :key="comment.id" class="comment-thread">
                <div class="comment">
                  <div class="comment-avatar"><UserAvatar :src="comment.profiles?.avatar_url || comment.profiles?.avatar" :alt="comment.profiles?.display_name || comment.profiles?.username || 'Profile picture'" :icon-size="16" /></div>
                  <div class="comment-copy">
                    <RouterLink v-if="commentProfileId(comment)" :to="commentProfileRoute(comment)" class="comment-author-link">{{ comment.profiles?.display_name || comment.profiles?.username || 'Follia reader' }}</RouterLink>
                    <strong v-else>{{ comment.profiles?.display_name || comment.profiles?.username || 'Follia reader' }}</strong>
                    <p>{{ comment.content }}</p>
                    <div class="comment-tools"><button class="comment-like" :class="{ liked: comment.liked }" type="button" :disabled="isCommentLikePending(comment)" @click="toggleCommentLike(comment)"><LoaderCircle v-if="isCommentLikePending(comment)" :size="13" class="spin" /><Heart v-else :size="13" :fill="comment.liked ? 'currentColor' : 'none'" /> {{ comment.like_count || 0 }}</button><button class="reply-button" type="button" @click="replyTo(comment)">Reply</button><button class="reply-button" type="button" @click="openReport('comment', comment)">Report</button></div>
                  </div>
                </div>
                <div v-for="reply in comment.replies || []" :key="reply.id" class="comment comment-reply">
                  <div class="comment-avatar"><UserAvatar :src="reply.profiles?.avatar_url || reply.profiles?.avatar" :alt="reply.profiles?.display_name || reply.profiles?.username || 'Profile picture'" :icon-size="15" /></div>
                  <div class="comment-copy">
                    <RouterLink v-if="commentProfileId(reply)" :to="commentProfileRoute(reply)" class="comment-author-link">{{ reply.profiles?.display_name || reply.profiles?.username || 'Follia reader' }}</RouterLink>
                    <strong v-else>{{ reply.profiles?.display_name || reply.profiles?.username || 'Follia reader' }}</strong>
                    <p>{{ reply.content }}</p>
                    <div class="comment-tools"><button class="comment-like" :class="{ liked: reply.liked }" type="button" :disabled="isCommentLikePending(reply)" @click="toggleCommentLike(reply)"><LoaderCircle v-if="isCommentLikePending(reply)" :size="13" class="spin" /><Heart v-else :size="13" :fill="reply.liked ? 'currentColor' : 'none'" /> {{ reply.like_count || 0 }}</button><button class="reply-button" type="button" @click="openReport('comment', reply)">Report</button></div>
                  </div>
                </div>
              </article>
            </template>
            <div v-else class="comments-state">No comments yet. Start the conversation.</div>
          </div>

          <form class="comment-form" @submit.prevent="submitComment">
            <div v-if="replyingTo" class="replying-to">
              <span>Replying to {{ replyingTo.profiles?.display_name || replyingTo.profiles?.username || 'comment' }}</span>
              <button type="button" aria-label="Cancel reply" @click="replyingTo = null"><X :size="14" /></button>
            </div>
            <p v-if="commentSubmitError" class="comment-submit-error" role="alert">{{ commentSubmitError }}</p>
            <div class="comment-input-row">
              <input v-model="commentText" maxlength="2000" :placeholder="replyingTo ? 'Write a reply…' : 'Write a comment…'" aria-label="Write a comment" :disabled="commentSubmitting" />
              <button :disabled="!commentText.trim() || commentSubmitting" aria-label="Send comment">
                <LoaderCircle v-if="commentSubmitting" :size="16" class="spin" />
                <Send v-else :size="16" />
              </button>
            </div>
          </form>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="imagePreviewIndex !== null" class="image-preview-overlay" role="dialog" aria-modal="true" aria-label="Image preview" :style="previewViewportStyle" @click.self="closeImagePreview" @click.stop>
        <button class="image-preview-close" type="button" aria-label="Close image preview" @click.stop="closeImagePreview"><X :size="22" /></button>
        <button v-if="mediaItems.length > 1" class="image-preview-arrow previous" type="button" aria-label="Previous image" @click.stop="stepImagePreview(-1)"><ChevronLeft :size="25" /></button>
        <img class="image-preview-image" :src="previewImageUrl" :alt="'Post image ' + (imagePreviewIndex + 1)" @click.stop />
        <button v-if="mediaItems.length > 1" class="image-preview-arrow next" type="button" aria-label="Next image" @click.stop="stepImagePreview(1)"><ChevronRight :size="25" /></button>
        <div class="image-preview-footer">
          <span v-if="mediaItems.length > 1">{{ imagePreviewIndex + 1 }} / {{ mediaItems.length }}</span>
          <a v-if="previewDownloadUrl" :href="previewDownloadUrl" @click.stop><Download :size="15" /> Download image</a>
        </div>
      </div>
    </Teleport>

    <div v-if="toast" class="toast">{{ toast }}</div>
    <Teleport to="body">
      <div v-if="showReport" class="report-overlay" @click.self="showReport = false">
        <form class="report-dialog" @submit.prevent="submitReport">
          <header><div><p>HELP KEEP FOLLIA SAFE</p><h2>Report {{ reportTarget?.type === 'profile' ? 'this profile' : reportTarget?.type === 'comment' ? 'this comment' : 'this content' }}</h2></div><button type="button" aria-label="Close" @click="showReport = false"><X :size="18" /></button></header>
          <label for="feed-report-reason">Reason</label>
          <select id="feed-report-reason" v-model="reportReason" required><option value="" disabled>Select a reason</option><option value="spam">Spam</option><option value="harassment">Harassment</option><option value="inappropriate">Inappropriate content</option><option value="impersonation">Impersonation</option><option value="other">Other</option></select>
          <label for="feed-report-details">More details <span>Optional</span></label>
          <textarea id="feed-report-details" v-model="reportDescription" rows="3" maxlength="500"></textarea>
          <p v-if="reportError" class="report-error" role="alert">{{ reportError }}</p>
          <footer><button type="button" class="report-cancel" @click="showReport = false">Cancel</button><button class="report-submit" :disabled="reportSubmitting || !reportReason">{{ reportSubmitting ? 'Sending…' : 'Send report' }}</button></footer>
        </form>
      </div>
    </Teleport>
  </article>
</template>

<script setup>
import { resolveMediaUrl } from '../utils/media'

import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  ArrowUpRight,
  BookOpen,
  Bookmark,
  Check,
  ChevronLeft,
  ChevronRight,
  Download,
  Flag,
  Heart,
  LoaderCircle,
  MessageCircle,
  MoreHorizontal,
  Pencil,
  Send,
  Share2,
  Trash2,
  X,
} from 'lucide-vue-next'

import { useAuth } from '../composables/useAuth'
import UserAvatar from './UserAvatar.vue'
import { toggleBookmark } from '../services/bookmarkService'
import {
  addResourceComment,
  getResourceComments,
} from '../services/commentService'
import { followUser, unfollowUser } from '../services/followService'
import { reportPost, reportPublisher, reportPostComment, reportResource, reportResourceComment } from '../services/reportService'
import {
  addPostComment,
  deletePost,
  getPostComments,
  togglePostLike,
  togglePostCommentLike,
  togglePostSave,
  updatePost,
} from '../services/postService'
import { toggleResourceLike } from '../services/resourceLikeService'
import { toggleResourceCommentLike } from '../services/commentService'
import { autoplayFeedVideo, handleFeedVideoPause, handleFeedVideoPlay, leaveFeedVideo } from '../utils/feedVideoPlayback'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
})

const { user, initializeAuth } = useAuth()

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
const commentsError = ref('')
const commentSubmitError = ref('')
const commentSubmitting = ref(false)
const commentLikePendingIds = ref(new Set())
const commentText = ref('')
const replyingTo = ref(null)
const showMenu = ref(false)
const showReport = ref(false)
const reportTarget = ref(null)
const reportReason = ref('')
const reportDescription = ref('')
const reportError = ref('')
const reportSubmitting = ref(false)
const videoElement = ref(null)
const imageTrack = ref(null)
const activeImage = ref(0)
const imagePreviewIndex = ref(null)
const previewViewportHeight = ref(null)
const previewViewportTop = ref(0)
const commentsViewportHeight = ref(null)
const commentsViewportTop = ref(0)
const isDeleted = ref(false)
const editing = ref(false)
const savingEdit = ref(false)

const currentBody = ref(props.item.body || '')
const editBody = ref(props.item.body || '')
const toast = ref('')

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

const mediaItems = computed(() => {
  if (props.item.media_items?.length) return props.item.media_items
  const url = props.item.media_url || props.item.media
  return url ? [{ url, media_type: props.item.media_type, download_url: props.item.media_download_url }] : []
})

const postMediaUrl = computed(() =>
  resolveMediaUrl(mediaItems.value[0]?.url || props.item.media_url || props.item.media)
)

const activeMediaDownloadUrl = computed(() =>
  mediaItems.value[activeImage.value]?.download_url || props.item.media_download_url || ''
)

const previewImageUrl = computed(() =>
  resolveMediaUrl(mediaItems.value[imagePreviewIndex.value]?.url)
)
const previewDownloadUrl = computed(() =>
  mediaItems.value[imagePreviewIndex.value]?.download_url || props.item.media_download_url || ''
)
const previewViewportStyle = computed(() => ({
  '--preview-viewport-height': previewViewportHeight.value ? `${previewViewportHeight.value}px` : '100dvh',
  '--preview-viewport-top': `${previewViewportTop.value}px`,
}))
const commentsViewportStyle = computed(() => ({
  '--comments-viewport-height': commentsViewportHeight.value ? `${commentsViewportHeight.value}px` : '100dvh',
  '--comments-viewport-top': `${commentsViewportTop.value}px`,
}))
const mediaIdentity = computed(() => mediaItems.value.map((media) => `${media.id || ''}:${media.url || ''}`).join('\u0000'))

const bodySegments = computed(() => {
  const text = currentBody.value || ''
  const pattern = /#[\p{L}_][\p{L}\p{N}_]{0,49}/gu
  const segments = []
  let cursor = 0
  for (const match of text.matchAll(pattern)) {
    const start = match.index
    const before = text[start - 1] || ''
    const after = text[start + match[0].length] || ''
    if ((before && !/\s/u.test(before)) || (after && /[\p{L}\p{N}_]/u.test(after))) continue
    if (start > cursor) segments.push({ text: text.slice(cursor, start), tag: false })
    segments.push({ text: match[0].slice(1), tag: true })
    cursor = start + match[0].length
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor), tag: false })
  return segments
})

const profileRoute = computed(() => ({
  name: 'publisher-detail',
  params: {
    id: author.value.user_id || props.item.author_id || author.value.id,
  },
}))

function commentProfileId(comment) {
  return comment?.profiles?.user_id || comment?.profiles?.id || comment?.user_id || null
}

function commentProfileRoute(comment) {
  return { name: 'publisher-detail', params: { id: commentProfileId(comment) } }
}

const showFollow = computed(() =>
  Boolean(
    (props.item.author_id || author.value.user_id || author.value.id) &&
    String(props.item.author_id || author.value.user_id || author.value.id) !== String(user.value?.id)
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

let videoObserver = null
let commentsVisualViewport = null
let previewVisualViewport = null
let previousBodyOverflow = ''

function updateVisualViewport(target) {
  const viewport = window.visualViewport
  target.height.value = viewport?.height || window.innerHeight
  target.top.value = viewport?.offsetTop || 0
}

function updateCommentsViewport() {
  updateVisualViewport({ height: commentsViewportHeight, top: commentsViewportTop })
}

function updatePreviewViewport() {
  updateVisualViewport({ height: previewViewportHeight, top: previewViewportTop })
}

function handlePreviewKeydown(event) {
  if (event.key === 'Escape') closeImagePreview()
  else if (event.key === 'ArrowLeft') stepImagePreview(-1)
  else if (event.key === 'ArrowRight') stepImagePreview(1)
}

watch(commentsOpen, (open) => {
  if (open) {
    previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    commentsVisualViewport = window.visualViewport || null
    updateCommentsViewport()
    commentsVisualViewport?.addEventListener('resize', updateCommentsViewport)
    commentsVisualViewport?.addEventListener('scroll', updateCommentsViewport)
    window.addEventListener('resize', updateCommentsViewport)
  } else {
    document.body.style.overflow = previousBodyOverflow
    commentsVisualViewport?.removeEventListener('resize', updateCommentsViewport)
    commentsVisualViewport?.removeEventListener('scroll', updateCommentsViewport)
    window.removeEventListener('resize', updateCommentsViewport)
    commentsVisualViewport = null
    commentsViewportHeight.value = null
    commentsViewportTop.value = 0
  }
})

watch(imagePreviewIndex, (index) => {
  if (index !== null) {
    previewVisualViewport = window.visualViewport || null
    updatePreviewViewport()
    previewVisualViewport?.addEventListener('resize', updatePreviewViewport)
    previewVisualViewport?.addEventListener('scroll', updatePreviewViewport)
    window.addEventListener('resize', updatePreviewViewport)
    window.addEventListener('keydown', handlePreviewKeydown)
  } else {
    previewVisualViewport?.removeEventListener('resize', updatePreviewViewport)
    previewVisualViewport?.removeEventListener('scroll', updatePreviewViewport)
    window.removeEventListener('resize', updatePreviewViewport)
    window.removeEventListener('keydown', handlePreviewKeydown)
    previewVisualViewport = null
    previewViewportHeight.value = null
    previewViewportTop.value = 0
  }
})

watch(mediaIdentity, async () => {
  activeImage.value = 0
  imagePreviewIndex.value = null
  postMediaFailed.value = false
  await nextTick()
  imageTrack.value?.scrollTo({ left: 0 })
})

onMounted(() => {
  if (!videoElement.value || !('IntersectionObserver' in window)) return
  videoObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.target !== videoElement.value) continue
      if (entry.isIntersecting && entry.intersectionRatio >= 0.6) autoplayFeedVideo(entry.target)
      else leaveFeedVideo(entry.target)
    }
  }, { threshold: [0, 0.6, 1] })
  videoObserver.observe(videoElement.value)
})
onBeforeUnmount(() => {
  videoObserver?.disconnect()
  leaveFeedVideo(videoElement.value)
  document.body.style.overflow = previousBodyOverflow
  commentsVisualViewport?.removeEventListener('resize', updateCommentsViewport)
  commentsVisualViewport?.removeEventListener('scroll', updateCommentsViewport)
  previewVisualViewport?.removeEventListener('resize', updatePreviewViewport)
  previewVisualViewport?.removeEventListener('scroll', updatePreviewViewport)
  window.removeEventListener('resize', updateCommentsViewport)
  window.removeEventListener('resize', updatePreviewViewport)
  window.removeEventListener('keydown', handlePreviewKeydown)
})

function handleVideoPlay(event) { handleFeedVideoPlay(event.currentTarget) }
function handleVideoPause(event) { handleFeedVideoPause(event.currentTarget) }
function handleImageScroll() {
  if (!imageTrack.value?.clientWidth) return
  activeImage.value = Math.max(0, Math.min(mediaItems.value.length - 1, Math.round(imageTrack.value.scrollLeft / imageTrack.value.clientWidth)))
}
function slideImage(direction) {
  if (!imageTrack.value) return
  goToImage(activeImage.value + direction)
}
function goToImage(index) {
  if (!imageTrack.value) return
  const safeIndex = Math.max(0, Math.min(mediaItems.value.length - 1, index))
  imageTrack.value.scrollTo({ left: imageTrack.value.clientWidth * safeIndex, behavior: 'smooth' })
}

function openImagePreview(index) {
  if (!mediaItems.value[index]) return
  activeImage.value = index
  imagePreviewIndex.value = index
  if (mediaItems.value.length > 1) goToImage(index)
}

function closeImagePreview() {
  imagePreviewIndex.value = null
}

function stepImagePreview(direction) {
  if (imagePreviewIndex.value === null || mediaItems.value.length < 2) return
  const nextIndex = (imagePreviewIndex.value + direction + mediaItems.value.length) % mediaItems.value.length
  imagePreviewIndex.value = nextIndex
  activeImage.value = nextIndex
  goToImage(nextIndex)
}

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
        ? unfollowUser(props.item.author_id || author.value.user_id || author.value.id)
        : followUser(props.item.author_id || author.value.user_id || author.value.id)
    )
  } catch (error) {
    following.value = previous
    notify(error.message || 'Unable to update following.')
  }
}

async function toggleComments() {
  if (commentsOpen.value) {
    closeComments()
    return
  }
  commentsOpen.value = true
  await loadComments()
}

function closeComments() {
  commentsOpen.value = false
  replyingTo.value = null
  commentText.value = ''
}

async function loadComments() {
  commentsLoading.value = true
  commentsError.value = ''
  try {
    comments.value = props.item.kind === 'resource'
      ? await getResourceComments(props.item.id)
      : await getPostComments(props.item.id)
    commentCount.value = comments.value.reduce(
      (count, comment) => count + 1 + (comment.replies?.length || 0),
      0,
    )
  } catch (error) {
    commentsError.value = error.message || 'Unable to load comments.'
  } finally {
    commentsLoading.value = false
  }
}

function replyTo(comment) {
  replyingTo.value = comment
  commentText.value = ''
}

async function submitComment() {
  const text = commentText.value.trim()

  if (!text || commentSubmitting.value) return

  commentSubmitting.value = true
  commentSubmitError.value = ''

  try {
    const comment = props.item.kind === 'resource'
      ? await addResourceComment(props.item.id, text, replyingTo.value?.id)
      : await addPostComment(props.item.id, text, replyingTo.value?.id)

    if (replyingTo.value) {
      const parent = comments.value.find((item) => item.id === replyingTo.value.id)
      if (parent) parent.replies = [...(parent.replies || []), comment]
    } else {
      comments.value.unshift({ ...comment, replies: comment.replies || [] })
    }
    commentCount.value += 1
    commentText.value = ''
    replyingTo.value = null
  } catch (error) {
    commentSubmitError.value = error.message || 'Unable to add your comment.'
  } finally {
    commentSubmitting.value = false
  }
}

async function toggleCommentLike(comment) {
  if (isCommentLikePending(comment)) return
  const previous = Boolean(comment.liked)
  commentLikePendingIds.value = new Set([...commentLikePendingIds.value, comment.id])
  comment.liked = !previous
  comment.like_count = Math.max(0, Number(comment.like_count || 0) + (previous ? -1 : 1))
  try {
    await initializeAuth()
    const result = props.item.kind === 'resource'
      ? await toggleResourceCommentLike(props.item.id, comment.id, previous)
      : await togglePostCommentLike(props.item.id, comment.id, previous)
    comment.liked = result.liked
    comment.like_count = result.count
  } catch (error) {
    comment.liked = previous
    comment.like_count = Math.max(0, Number(comment.like_count || 0) + (previous ? 1 : -1))
    notify(error.message || 'Sign in to like this comment.')
  } finally {
    const pendingIds = new Set(commentLikePendingIds.value)
    pendingIds.delete(comment.id)
    commentLikePendingIds.value = pendingIds
  }
}

function isCommentLikePending(comment) {
  return commentLikePendingIds.value.has(comment.id)
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

function openReport(type, comment = null) {
  showMenu.value = false
  reportTarget.value = { type, comment }
  reportReason.value = ''
  reportDescription.value = ''
  reportError.value = ''
  showReport.value = true
}

async function submitReport() {
  if (!reportTarget.value || reportSubmitting.value) return
  reportSubmitting.value = true
  reportError.value = ''
  try {
    const { type, comment } = reportTarget.value
    const description = reportDescription.value.trim()
    let result
    if (type === 'profile') {
      result = await reportPublisher({ reportedUserId: props.item.author_id, reason: reportReason.value, description })
    } else if (type === 'comment' && props.item.kind === 'resource') {
      result = await reportResourceComment(props.item.id, comment.id, reportReason.value, description)
    } else if (type === 'comment') {
      result = await reportPostComment(props.item.id, comment.id, reportReason.value, description)
    } else if (type === 'resource') {
      result = await reportResource(props.item.id, reportReason.value, description)
    } else {
      result = await reportPost(props.item.id, reportReason.value, description)
    }
    showReport.value = false
    notify(result?.duplicate ? 'You have already reported this item.' : 'Thanks. Your report was sent.')
  } catch (error) {
    reportError.value = error.message || 'Unable to send your report.'
  } finally {
    reportSubmitting.value = false
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
.hashtag { color:var(--text-main); font-weight:700; text-decoration:underline; text-decoration-color:var(--border-color); text-underline-offset:3px; }
.post-editor { display:grid; gap:9px; margin:0 0 13px; }
.post-editor textarea { width:100%; padding:11px; border:1px solid var(--border-color); border-radius:12px; outline:0; background:var(--input-bg); color:var(--text-main); font:13px/1.6 'DM Sans',sans-serif; resize:vertical; }
.editor-actions { display:flex; justify-content:flex-end; gap:8px; }
.editor-actions button { min-height:34px; display:inline-flex; align-items:center; gap:6px; padding:0 10px; border-radius:9px; font-size:10px; font-weight:700; }
.cancel-edit { border:1px solid var(--border-color); background:transparent; color:var(--text-secondary); }
.save-edit { background:var(--primary-bg); color:var(--primary-text); }
.save-edit:disabled { opacity:.5; }
.post-media { position:relative; overflow:hidden; margin-top:14px; border:1px solid var(--border-soft); border-radius:15px; background:var(--card-soft); }
.post-media > img,.post-media video { display:block; width:100%; max-height:600px; object-fit:contain; }
.post-media > img { cursor:zoom-in; }
.image-carousel { position:relative; width:100%; }
.image-track { width:100%; height:clamp(220px,min(72dvh,600px),600px); display:flex; overflow-x:auto; overflow-y:hidden; scroll-snap-type:x mandatory; scroll-behavior:smooth; overscroll-behavior-x:contain; scrollbar-width:none; touch-action:auto; }
.image-track::-webkit-scrollbar { display:none; }
.image-track img { display:block; flex:0 0 100%; width:100%; min-width:100%; height:100%; max-height:none; object-fit:contain; scroll-snap-align:start; scroll-snap-stop:always; cursor:zoom-in; }
.carousel-arrow { position:absolute; top:50%; z-index:1; width:42px; height:42px; display:grid; place-items:center; transform:translateY(-50%); border-radius:50%; background:rgba(15,17,20,.72); color:white; font-size:25px; line-height:1; }
.carousel-arrow.previous { left:10px; }
.carousel-arrow.next { right:10px; }
.image-count { position:absolute; top:10px; right:10px; padding:5px 8px; border-radius:999px; background:rgba(15,17,20,.68); color:white; font-size:10px; }
.image-dots { position:absolute; left:0; right:0; bottom:11px; display:flex; justify-content:center; gap:5px; pointer-events:none; }
.image-dots button { width:30px; height:30px; display:grid; place-items:center; padding:0; background:transparent; pointer-events:auto; }
.image-dots button::before { content:''; width:7px; height:7px; border-radius:50%; background:rgba(255,255,255,.62); transition:transform .16s ease,background .16s ease; }
.image-dots button.active::before { background:white; transform:scale(1.25); }
.media-download { display:flex; align-items:center; justify-content:flex-end; gap:6px; padding:8px 11px; color:var(--text-secondary); font-size:10px; font-weight:700; }
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
.comments-overlay { position:fixed; left:0; right:0; top:var(--comments-viewport-top,0px); height:var(--comments-viewport-height,100dvh); z-index:400; display:grid; place-items:center; padding:max(18px,env(safe-area-inset-top)) max(18px,env(safe-area-inset-right)) max(18px,env(safe-area-inset-bottom)) max(18px,env(safe-area-inset-left)); box-sizing:border-box; background:rgba(14,15,17,.58); backdrop-filter:blur(6px); }
.comments-modal { width:min(620px,100%); height:min(720px,calc(var(--comments-viewport-height,100dvh) - 48px)); max-height:calc(var(--comments-viewport-height,100dvh) - 48px); min-height:min(340px,calc(var(--comments-viewport-height,100dvh) - 48px)); display:grid; grid-template-rows:auto minmax(0,1fr) auto; overflow:hidden; border:1px solid var(--border-color); border-radius:24px; background:var(--card-bg); box-shadow:0 24px 80px rgba(0,0,0,.24); }
.comments-header { display:flex; align-items:center; justify-content:space-between; gap:14px; padding:20px 24px; border-bottom:1px solid var(--border-soft); }
.comments-header h2 { margin:0; color:var(--text-main); font:750 21px/1.2 Manrope,sans-serif; letter-spacing:-.02em; }
.comments-kicker { margin:0 0 4px; color:var(--text-tertiary); font-size:9px; font-weight:750; letter-spacing:.14em; }
.comments-close { width:42px; height:42px; flex:0 0 42px; display:grid; place-items:center; border-radius:12px; background:var(--icon-bg); color:var(--text-main); }
.comments-list { min-height:0; display:grid; align-content:start; gap:20px; overflow-y:auto; overflow-x:hidden; padding:22px 24px; overscroll-behavior:contain; -webkit-overflow-scrolling:touch; }
.comments-state { padding:28px 12px; color:var(--text-tertiary); font-size:13px; line-height:1.5; text-align:center; }
.comments-error button,.reply-button { min-height:34px; margin-top:5px; padding:0 4px; background:transparent; color:var(--text-secondary); font-size:11px; font-weight:700; }
.comments-error button:hover,.reply-button:hover { color:var(--text-main); }
.comment-thread { display:grid; gap:15px; min-width:0; }
.comment { display:flex; align-items:flex-start; gap:12px; min-width:0; }
.comment-avatar { width:40px; height:40px; flex:0 0 40px; display:grid; place-items:center; overflow:hidden; border-radius:50%; background:var(--icon-bg); color:var(--text-secondary); }
.comment-copy { min-width:0; flex:1; overflow-wrap:anywhere; }
.comment strong,.comment-author-link { display:block; max-width:100%; margin:1px 0 5px; color:var(--text-main); font-size:13px; line-height:1.4; font-weight:750; overflow-wrap:anywhere; }
.comment-author-link { width:fit-content; text-decoration:underline; text-decoration-color:transparent; text-underline-offset:3px; transition:color .15s ease,text-decoration-color .15s ease; }
.comment-author-link:hover { color:var(--text-secondary); text-decoration-color:currentColor; }
.comment-author-link:focus-visible { border-radius:3px; outline:2px solid var(--primary-bg); outline-offset:3px; text-decoration-color:currentColor; }
.comment p { margin:0; color:var(--text-secondary); font-size:13px; line-height:1.6; white-space:pre-wrap; overflow-wrap:anywhere; word-break:break-word; }
.comment-tools { display:flex; align-items:center; flex-wrap:wrap; gap:8px 13px; margin-top:7px; }
.comment-like { min-height:34px; display:inline-flex; align-items:center; gap:5px; padding:0 3px; background:transparent; color:var(--text-tertiary); font-size:11px; }
.comment-like.liked { color:#9e463b; }
.comment-reply { margin-left:48px; }
.comment-form { padding:14px 20px max(16px,env(safe-area-inset-bottom)); border-top:1px solid var(--border-soft); background:var(--card-bg); }
.replying-to { display:flex; align-items:center; justify-content:space-between; gap:10px; margin:0 0 9px; color:var(--text-tertiary); font-size:11px; overflow-wrap:anywhere; }
.replying-to button { width:34px; height:34px; flex:0 0 34px; display:grid; place-items:center; border-radius:9px; background:var(--icon-bg); color:var(--text-secondary); }
.comment-input-row { display:flex; gap:10px; }
.comment-input-row input { flex:1; min-width:0; height:48px; padding:0 15px; border:1px solid var(--border-color); border-radius:13px; outline:0; background:var(--input-bg); color:var(--text-main); font-size:14px; }
.comment-input-row input:focus { border-color:var(--text-tertiary); }
.comment-input-row button { width:48px; height:48px; flex:0 0 48px; display:grid; place-items:center; border-radius:13px; background:var(--primary-bg); color:var(--primary-text); }
.comment-input-row button:disabled { opacity:.5; }
.image-preview-overlay { position:fixed; left:0; right:0; top:var(--preview-viewport-top,0px); height:var(--preview-viewport-height,100dvh); z-index:550; display:grid; grid-template-rows:minmax(0,1fr) auto; align-items:center; gap:10px; padding:max(22px,env(safe-area-inset-top)) max(22px,env(safe-area-inset-right)) max(20px,env(safe-area-inset-bottom)) max(22px,env(safe-area-inset-left)); box-sizing:border-box; background:rgba(9,10,12,.94); backdrop-filter:blur(8px); }
.image-preview-image { grid-row:1; display:block; width:100%; height:100%; min-height:0; object-fit:contain; }
.image-preview-close,.image-preview-arrow { z-index:1; width:48px; height:48px; display:grid; place-items:center; border:1px solid rgba(255,255,255,.2); border-radius:50%; background:rgba(30,31,34,.78); color:white; }
.image-preview-close { position:absolute; top:max(18px,env(safe-area-inset-top)); right:max(18px,env(safe-area-inset-right)); }
.image-preview-arrow.previous,.image-preview-arrow.next { position:absolute; top:50%; transform:translateY(-50%); }
.image-preview-arrow.previous { left:max(20px,env(safe-area-inset-left)); }
.image-preview-arrow.next { right:max(20px,env(safe-area-inset-right)); }
.image-preview-footer { grid-row:2; display:flex; align-items:center; justify-content:center; gap:18px; color:rgba(255,255,255,.82); font-size:12px; }
.image-preview-footer a { min-height:42px; display:inline-flex; align-items:center; justify-content:center; gap:7px; padding:0 14px; border:1px solid rgba(255,255,255,.2); border-radius:11px; color:white; font-size:12px; font-weight:700; }
.toast { position:absolute; right:14px; bottom:64px; padding:10px 13px; border-radius:10px; background:var(--text-main); color:var(--card-bg); font-size:11px; box-shadow:0 5px 16px var(--shadow-color); }
.report-overlay { position:fixed; inset:0; z-index:600; display:grid; place-items:center; padding:18px; background:rgba(14,15,17,.62); backdrop-filter:blur(5px); }
.report-dialog { width:min(430px,100%); display:grid; gap:9px; padding:21px; border:1px solid var(--border-color); border-radius:19px; background:var(--card-bg); box-shadow:0 24px 80px rgba(0,0,0,.25); }
.report-dialog header,.report-dialog footer { display:flex; align-items:center; justify-content:space-between; gap:10px; }
.report-dialog header { margin-bottom:6px; }
.report-dialog header p { margin:0 0 4px; color:var(--text-tertiary); font-size:9px; font-weight:750; letter-spacing:.13em; }
.report-dialog h2 { margin:0; font:750 19px Manrope,sans-serif; }
.report-dialog header > button { width:32px; height:32px; display:grid; place-items:center; border-radius:9px; background:var(--icon-bg); color:var(--text-main); }
.report-dialog label { margin-top:5px; color:var(--text-secondary); font-size:11px; font-weight:700; }
.report-dialog label span { color:var(--text-tertiary); font-weight:400; }
.report-dialog select,.report-dialog textarea { width:100%; padding:10px 11px; border:1px solid var(--border-color); border-radius:10px; outline:0; background:var(--input-bg); color:var(--text-main); font:inherit; font-size:12px; }
.report-dialog textarea { resize:vertical; }
.report-dialog footer { justify-content:flex-end; margin-top:8px; }
.report-cancel,.report-submit { min-height:36px; padding:0 12px; border-radius:10px; font-size:11px; font-weight:700; }
.report-cancel { border:1px solid var(--border-color); background:transparent; color:var(--text-secondary); }
.report-submit { background:var(--primary-bg); color:var(--primary-text); }
.report-submit:disabled { opacity:.5; }
.report-error { margin:0; color:#a33b30; font-size:11px; }
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
  .image-track { height:clamp(220px,min(66dvh,600px),600px); }
  .carousel-arrow { width:40px; height:40px; }
  .comments-overlay { align-items:end; padding:env(safe-area-inset-top) 0 0; }
  .comments-modal { width:100%; height:100%; max-height:100%; min-height:0; border-right:0; border-bottom:0; border-left:0; border-radius:24px 24px 0 0; }
  .comments-header { padding:16px 18px; }
  .comments-list { padding:18px; gap:18px; }
  .comment-avatar { width:38px; height:38px; flex-basis:38px; }
  .comment-reply { margin-left:32px; }
  .comment-form { padding:12px 14px max(16px,env(safe-area-inset-bottom)); }
  .image-preview-overlay { gap:6px; padding-right:max(10px,env(safe-area-inset-right)); padding-left:max(10px,env(safe-area-inset-left)); }
  .image-preview-arrow { width:40px; height:40px; }
}
</style>
