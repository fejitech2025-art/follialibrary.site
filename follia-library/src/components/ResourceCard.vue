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
          <UserRound :size="15" />
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
          <UserRound :size="15" />
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
            <div v-if="commentsLoading" class="comments-state"><LoaderCircle :size="20" class="spin" /> Loading comments...</div>
            <div v-else-if="commentsError" class="comments-state comments-error" role="alert">
              {{ commentsError }} <button type="button" @click="loadComments">Try again</button>
            </div>
            <template v-else-if="comments.length">
              <article v-for="comment in comments" :key="comment.id" class="comment-thread">
                <div class="comment-item">
                  <RouterLink v-if="comment.profiles?.id" :to="{ name: 'publisher-detail', params: { id: comment.profiles.id } }" class="comment-avatar" @click.stop>
                    <img v-if="getCommentAvatarUrl(comment) && !failedCommentAvatars.has(comment.id)" :src="getCommentAvatarUrl(comment)" :alt="comment.profiles.display_name || comment.profiles.username || 'User'" class="comment-avatar-image" @error="markCommentAvatarFailed(comment.id)" />
                    <UserRound v-else :size="16" />
                  </RouterLink>
                  <div v-else class="comment-avatar"><UserRound :size="16" /></div>
                  <div class="comment-body">
                    <div class="comment-meta">
                      <RouterLink v-if="comment.profiles?.id" :to="{ name: 'publisher-detail', params: { id: comment.profiles.id } }" @click.stop>{{ comment.profiles.display_name || comment.profiles.username || 'Follia reader' }}</RouterLink>
                      <span v-else>{{ comment.author || 'Follia reader' }}</span>
                      <span>{{ formatCommentTime(comment.created_at) }}</span>
                    </div>
                    <p>{{ comment.content }}</p>
                    <button class="reply-comment" type="button" @click="replyTo(comment)">Reply</button>
                  </div>
                </div>
                <div v-for="reply in comment.replies || []" :key="reply.id" class="comment-item comment-reply">
                  <div class="comment-avatar"><UserAvatar :src="reply.profiles?.avatar_url || reply.profiles?.avatar" :alt="reply.profiles?.display_name || reply.profiles?.username || 'Profile picture'" :icon-size="15" /></div>
                  <div class="comment-body">
                    <div class="comment-meta"><span>{{ reply.profiles?.display_name || reply.profiles?.username || 'Follia reader' }}</span><span>{{ formatCommentTime(reply.created_at) }}</span></div>
                    <p>{{ reply.content }}</p>
                  </div>
                </div>
              </article>
            </template>
            <div v-else class="comments-empty"><MessageCircle :size="24" /><p>No comments yet.</p><span>Be the first to share your thoughts.</span></div>
          </div>

          <form class="comment-input" @submit.prevent="addComment">
            <div v-if="replyingTo" class="replying-to"><span>Replying to {{ replyingTo.profiles?.display_name || replyingTo.profiles?.username || 'comment' }}</span><button type="button" aria-label="Cancel reply" @click="replyingTo = null"><X :size="14" /></button></div>
            <div class="comment-input-row">
              <input v-model="newComment" type="text" maxlength="2000" :placeholder="replyingTo ? 'Write a reply...' : 'Write a comment...'" :disabled="commentSubmitting" />
              <button type="submit" :disabled="!newComment.trim() || commentSubmitting"><LoaderCircle v-if="commentSubmitting" :size="15" class="spin" /><span v-else>Send</span></button>
            </div>
            <p v-if="commentSubmitError" class="comment-submit-error" role="alert">{{ commentSubmitError }}</p>
          </form>
        </div>
      </div>
    </Teleport>
  </article>
</template>

<script setup>
import { resolveMediaUrl } from '../utils/media'

import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  BookOpen,
  Heart,
  LoaderCircle,
  MessageCircle,
  UserRound,
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
const commentsError = ref('')
const commentSubmitError = ref('')

const showComments = ref(false)
const newComment = ref('')
const replyingTo = ref(null)

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
  commentsError.value = ''

  try {
    comments.value = await getResourceComments(props.resource.id)
    commentCount.value = comments.value.reduce(
      (count, comment) => count + 1 + (comment.replies?.length || 0),
      0,
    )
  } catch (error) {
    console.error('Comments error:', error)
    commentsError.value = error?.message || 'Unable to load comments.'
  } finally {
    commentsLoading.value = false
  }
}

function replyTo(comment) {
  replyingTo.value = comment
  newComment.value = ''
  commentSubmitError.value = ''
}

async function addComment() {
  const content = newComment.value.trim()

  if (!content || commentSubmitting.value) return

  commentSubmitting.value = true
  commentSubmitError.value = ''

  try {
    const comment = await addResourceComment(
      props.resource.id,
      content,
      replyingTo.value?.id,
    )

    if (replyingTo.value) {
      const parent = comments.value.find((item) => item.id === replyingTo.value.id)
      if (parent) parent.replies = [...(parent.replies || []), comment]
    } else {
      comments.value.unshift({ ...comment, replies: comment.replies || [] })
    }
    commentCount.value += 1
    newComment.value = ''
    replyingTo.value = null
  } catch (error) {
    console.error('Add comment error:', error)
    commentSubmitError.value = error?.message || 'Unable to add your comment.'
  } finally {
    commentSubmitting.value = false
  }
}

function closeComments() {
  showComments.value = false
  replyingTo.value = null
  newComment.value = ''
}

function openResource() {
  router.push({
    name: 'resource-detail',
    params: {
      id: props.resource.id,
    },
  })
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

.comment-input { display:block; }
.comment-thread { display:block; }
.comment-reply { margin-left:42px; }
.reply-comment { margin-top:7px; padding:0; background:transparent; color:var(--text-tertiary); font-size:10px; font-weight:700; }
.replying-to { display:flex; align-items:center; justify-content:space-between; margin:0 0 8px; color:var(--text-tertiary); font-size:10px; }
.replying-to button { width:26px; height:26px; display:grid; place-items:center; border-radius:7px; background:var(--icon-bg); color:var(--text-secondary); }
.comment-input-row { display:flex; gap:8px; }
.comment-input-row input { flex:1; min-width:0; }
.comment-submit-error { margin:8px 0 0; color:#a33b30; font-size:11px; }
.comments-state { display:flex; align-items:center; justify-content:center; gap:8px; min-height:140px; color:var(--text-tertiary); font-size:12px; text-align:center; }
.comments-error { flex-direction:column; }
.comments-error button { color:var(--text-main); font-size:11px; font-weight:700; }
</style>
