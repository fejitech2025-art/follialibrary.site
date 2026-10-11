<template>
  <article
    class="resource-card"
    role="link"
    tabindex="0"
    @click="openResource"
    @keydown.enter="openResource"
    @keydown.space.prevent="openResource"
  >
    <!-- Resource cover -->
    <div class="resource-cover">
      <img
        v-if="resourceCoverUrl && !resourceCoverFailed"
        :src="resourceCoverUrl"
        :alt="resource.title"
        @error="resourceCoverFailed = true"
      />

      <div v-else class="cover-placeholder">
        <BookOpen :size="30" />
      </div>

      <span class="resource-price">
        {{ (resource.is_free ?? resource.free) ? 'FREE' : resource.price }}
      </span>
    </div>

    <!-- Resource information -->
    <div class="resource-info">
      <p class="resource-category">
        {{ resource.category }}
      </p>

      <h3>{{ resource.title }}</h3>

      <!-- Author profile -->
      <RouterLink
        v-if="resource.profiles?.id"
        :to="{
          name: 'publisher-detail',
          params: {
            id: resource.profiles.id,
          },
        }"
        class="resource-author"
        @click.stop
      >
        <img
          v-if="authorAvatarUrl && !authorAvatarFailed"
          :src="authorAvatarUrl"
          :alt="`${resource.profiles?.username || resource.author || 'Author'}'s profile picture`"
          class="resource-author-avatar"
          @error="authorAvatarFailed = true"
        />

        <span
          v-else
          class="resource-author-avatar resource-author-initial"
        >
          {{ getInitial(resource.profiles?.username || resource.author) }}
        </span>

        <span class="resource-author-name">
          {{
            resource.profiles?.username ||
            resource.profiles?.display_name ||
            resource.author ||
            'Unknown author'
          }}
        </span>
      </RouterLink>

      <div v-else class="resource-author">
        <img
          v-if="fallbackAuthorAvatarUrl && !fallbackAuthorAvatarFailed"
          :src="fallbackAuthorAvatarUrl"
          alt="Author profile picture"
          class="resource-author-avatar"
          @error="fallbackAuthorAvatarFailed = true"
        />

        <span
          v-else
          class="resource-author-avatar resource-author-initial"
        >
          {{ getInitial(resource.author) }}
        </span>

        <span class="resource-author-name">
          {{ resource.author || 'Unknown author' }}
        </span>
      </div>

      <!-- Resource actions -->
      <div class="resource-actions">
        <button
          class="resource-action"
          :class="{ liked }"
          :disabled="likeLoading"
          aria-label="Like resource"
          @click.stop="toggleLike"
        >
          <LoaderCircle v-if="likeLoading" :size="16" class="spin" />
          <Heart v-else :size="16" :fill="liked ? 'currentColor' : 'none'" />
          <span>{{ likeCount }}</span>
        </button>

        <button
          class="resource-action"
          :disabled="commentsLoading"
          aria-label="View comments"
          @click.stop="openComments"
        >
          <LoaderCircle v-if="commentsLoading" :size="16" class="spin" />
          <MessageCircle v-else :size="16" />
          <span>{{ commentCount }}</span>
        </button>
      </div>
    </div>

    <!-- Comments modal -->
    <Teleport to="body">
      <div
        v-if="showComments"
        class="comments-overlay"
        @click.self="closeComments"
      >
        <div class="comments-modal">
          <div class="comments-header">
            <div>
              <p class="comments-kicker">DISCUSSION</p>
              <h2>Comments</h2>
            </div>

            <button
              class="comments-close"
              aria-label="Close comments"
              @click="closeComments"
            >
              <X :size="20" />
            </button>
          </div>

          <div class="comments-list">
            <div
              v-for="comment in comments"
              :key="comment.id"
              class="comment-item"
            >
              <!-- Comment avatar -->
              <RouterLink
                v-if="comment.profiles?.id"
                :to="{
                  name: 'publisher-detail',
                  params: { id: comment.profiles.id },
                }"
                class="comment-avatar"
                @click.stop
              >
                <img
                  v-if="getCommentAvatarUrl(comment) && !failedCommentAvatars.has(comment.id)"
                  :src="getCommentAvatarUrl(comment)"
                  :alt="comment.profiles.display_name || comment.profiles.username || 'User'"
                  class="comment-avatar-image"
                  @error="markCommentAvatarFailed(comment.id)"
                />

                <span v-else>
                  {{
                    getInitial(
                      comment.profiles.display_name ||
                      comment.profiles.username
                    )
                  }}
                </span>
              </RouterLink>

              <div v-else class="comment-avatar">
                {{ getInitial(comment.author) }}
              </div>

              <div class="comment-body">
                <div class="comment-meta">
                  <RouterLink
                    v-if="comment.profiles?.id"
                    :to="{
                      name: 'publisher-detail',
                      params: { id: comment.profiles.id },
                    }"
                    @click.stop
                  >
                    {{
                      comment.profiles.display_name ||
                      comment.profiles.username ||
                      'Unknown user'
                    }}
                  </RouterLink>

                  <span v-else>
                    {{ comment.author || 'Unknown user' }}
                  </span>

                  <span>{{ formatCommentTime(comment.created_at) }}</span>
                </div>

                <p>{{ comment.content || comment.text }}</p>
              </div>
            </div>

            <div
              v-if="comments.length === 0 && !commentsLoading"
              class="comments-empty"
            >
              <MessageCircle :size="24" />
              <p>No comments yet.</p>
              <span>Be the first to share your thoughts.</span>
            </div>

            <div v-if="commentsLoading" class="comments-loading">
              <LoaderCircle :size="22" class="spin" />
              <span>Loading comments...</span>
            </div>
          </div>

          <div class="comment-input">
            <input
              v-model="newComment"
              type="text"
              maxlength="2000"
              placeholder="Write a comment..."
              :disabled="commentSubmitting"
              @keyup.enter="addComment"
            />

            <button
              :disabled="!newComment.trim() || commentSubmitting"
              @click="addComment"
            >
              <LoaderCircle
                v-if="commentSubmitting"
                :size="15"
                class="spin"
              />
              <span v-else>Send</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </article>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  BookOpen,
  Heart,
  LoaderCircle,
  MessageCircle,
  X,
} from 'lucide-vue-next'

import {
  getResourceLikeCount,
  isResourceLiked,
  toggleResourceLike,
} from '../services/resourceLikeService'

import {
  addResourceComment,
  getResourceCommentCount,
  getResourceComments,
} from '../services/commentService'

const props = defineProps({
  resource: {
    type: Object,
    required: true,
  },
})

const router = useRouter()

// Read the Django backend address from the Vue environment.
const configuredApiUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL

const API_BASE_URL = (
  configuredApiUrl ||
  (import.meta.env.DEV
    ? 'http://127.0.0.1:8000'
    : window.location.origin)
)
  .replace(/\/+$/, '')
  .replace(/\/api$/i, '')

// Resolve relative Django media paths into complete image URLs.
function resolveMediaUrl(url) {
  if (!url || typeof url !== 'string') return null

  const value = url.trim()
  if (!value) return null

  // Preserve complete URLs and temporary local previews.
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

const resourceCoverUrl = computed(() =>
  resolveMediaUrl(props.resource.cover_url || props.resource.cover)
)

const authorAvatarUrl = computed(() =>
  resolveMediaUrl(
    props.resource.profiles?.avatar_url ||
    props.resource.profiles?.avatar ||
    props.resource.authorAvatar
  )
)

const fallbackAuthorAvatarUrl = computed(() =>
  resolveMediaUrl(props.resource.authorAvatar)
)

const resourceCoverFailed = ref(false)
const authorAvatarFailed = ref(false)
const fallbackAuthorAvatarFailed = ref(false)

const failedCommentAvatars = ref(new Set())

function getCommentAvatarUrl(comment) {
  return resolveMediaUrl(
    comment.profiles?.avatar_url ||
    comment.profiles?.avatar
  )
}

function markCommentAvatarFailed(commentId) {
  failedCommentAvatars.value = new Set([
    ...failedCommentAvatars.value,
    commentId,
  ])
}

const liked = ref(false)
const likeCount = ref(0)
const likeLoading = ref(false)

const comments = ref([])
const commentCount = ref(0)
const commentsLoading = ref(false)
const commentSubmitting = ref(false)

const showComments = ref(false)
const newComment = ref('')

onMounted(() => {
  loadLikeData()
  loadCommentCount()
})

async function loadLikeData() {
  if (!props.resource?.id) return

  try {
    const [likedResult, countResult] = await Promise.all([
      isResourceLiked(props.resource.id),
      getResourceLikeCount(props.resource.id),
    ])

    liked.value = likedResult
    likeCount.value = countResult
  } catch (error) {
    console.error('Resource like data error:', error)
    liked.value = false
    likeCount.value = 0
  }
}

async function loadCommentCount() {
  if (!props.resource?.id) return

  try {
    commentCount.value = await getResourceCommentCount(props.resource.id)
  } catch (error) {
    console.error('Comment count error:', error)
    commentCount.value = 0
  }
}

async function toggleLike() {
  if (!props.resource?.id || likeLoading.value) return

  likeLoading.value = true

  const previousLiked = liked.value
  const previousCount = likeCount.value

  liked.value = !previousLiked
  likeCount.value = previousLiked
    ? Math.max(0, previousCount - 1)
    : previousCount + 1

  try {
    const result = await toggleResourceLike(
      props.resource.id,
      previousLiked
    )

    liked.value = result.liked
    likeCount.value = await getResourceLikeCount(props.resource.id)
  } catch (error) {
    console.error('Like error:', error)
    liked.value = previousLiked
    likeCount.value = previousCount
  } finally {
    likeLoading.value = false
  }
}

async function openComments() {
  showComments.value = true
  await loadComments()
}

async function loadComments() {
  if (!props.resource?.id) return

  commentsLoading.value = true

  try {
    comments.value = await getResourceComments(props.resource.id)
    commentCount.value = comments.value.length
  } catch (error) {
    console.error('Comments error:', error)
  } finally {
    commentsLoading.value = false
  }
}

async function addComment() {
  const content = newComment.value.trim()

  if (!content || commentSubmitting.value) return

  commentSubmitting.value = true

  try {
    const comment = await addResourceComment(
      props.resource.id,
      content
    )

    comments.value.unshift(comment)
    commentCount.value = comments.value.length
    newComment.value = ''
  } catch (error) {
    console.error('Add comment error:', error)
    window.alert(error?.message || 'Unable to add your comment.')
  } finally {
    commentSubmitting.value = false
  }
}

function closeComments() {
  showComments.value = false
}

function openResource() {
  router.push({
    name: 'resource-detail',
    params: {
      id: props.resource.id,
    },
  })
}

function getInitial(name) {
  if (!name) return '?'
  return name.trim().charAt(0).toUpperCase()
}

function formatCommentTime(dateString) {
  if (!dateString) return ''

  const date = new Date(dateString)
  const now = new Date()

  const difference = Math.floor(
    (now.getTime() - date.getTime()) / 1000
  )

  if (difference < 60) return 'Just now'

  const minutes = Math.floor(difference / 60)
  if (minutes < 60) return `${minutes}m ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`

  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`

  return date.toLocaleDateString('en-NG', {
    day: 'numeric',
    month: 'short',
  })
}
</script>

<style scoped>
.resource-author-avatar {
  width: 26px;
  height: 26px;
  min-width: 26px;
  max-width: 26px;
  min-height: 26px;
  max-height: 26px;
  object-fit: cover;
  border-radius: 50%;
  flex: 0 0 26px;
  display: block;
}

.resource-author-initial {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.comment-avatar-image {
  width: 36px;
  height: 36px;
  min-width: 36px;
  max-width: 36px;
  min-height: 36px;
  max-height: 36px;
  object-fit: cover;
  border-radius: 50%;
  flex: 0 0 36px;
  display: block;
}
</style>
