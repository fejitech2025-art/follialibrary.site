<template>
  <MainLayout>
    <section class="resource-detail-page">
      <!-- Loading -->
      <div v-if="loading" class="resource-detail-state">
        <div class="state-icon">
          <LoaderCircle :size="28" class="spin" />
        </div>

        <h2>Loading resource...</h2>
        <p>We're getting the resource ready for you.</p>
      </div>

      <!-- Error -->
      <div v-else-if="errorMessage" class="resource-detail-state">
        <div class="state-icon error">
          <AlertCircle :size="28" />
        </div>

        <h2>Resource unavailable</h2>
        <p>{{ errorMessage }}</p>

        <RouterLink to="/" class="detail-back-button"> Back to Library </RouterLink>
      </div>

      <!-- Resource -->
      <div v-else-if="resource" class="resource-detail-content">
        <!-- Top navigation -->
        <div class="detail-topbar">
          <button type="button" class="back-button" @click="goBack">
            <ArrowLeft :size="18" />
            <span>Back</span>
          </button>

          <div class="detail-top-actions">
            <button
              type="button"
              class="bookmark-button"
              :class="{ bookmarked }"
              :disabled="bookmarkLoading"
              @click="handleBookmark"
            >
              <LoaderCircle v-if="bookmarkLoading" :size="18" class="spin" />

              <Bookmark v-else :size="18" :fill="bookmarked ? 'currentColor' : 'none'" />

              <span>{{ bookmarked ? 'Saved' : 'Save' }}</span>
            </button>

            <button type="button" class="share-button" @click="shareResource">
              <Share2 :size="18" />
              <span>Share</span>
            </button>
            <button type="button" class="share-button" :disabled="!resource.file_url" @click="showPreview = true"><Eye :size="17" /><span>Preview</span></button>
            <button type="button" class="share-button" @click="openResourceReport('resource')"><Flag :size="17" /><span>Report</span></button>
          </div>
        </div>

        <!-- Hero -->
        <section class="resource-detail-hero">
          <!-- Cover -->
          <div class="detail-cover">
            <img v-if="resource.cover_url || resource.cover" :src="resolveMediaUrl(resource.cover_url || resource.cover)" :alt="resource.title" />

            <div v-else class="detail-cover-placeholder">
              <BookOpen :size="64" />
              <span>{{ resource.category }}</span>
            </div>
          </div>

          <!-- Main information -->
          <div class="detail-main-info">
            <div class="detail-meta">
              <span>{{ resource.category }}</span>

              <span class="meta-dot">•</span>

              <span>{{ resource.language }}</span>
            </div>

            <h1>{{ resource.title }}</h1>

            <p v-if="resource.description" class="detail-description">
              {{ resource.description }}
            </p>

            <!-- Author -->
            <RouterLink
              v-if="resource.profiles?.id"
              :to="{
                name: 'publisher-detail',
                params: {
                id: resource.profiles.user_id || resource.author_id || resource.profiles.id,
                },
              }"
              class="detail-author"
            >
              <div class="author-avatar">
                <UserAvatar :src="resource.profiles.avatar_url || resource.profiles.avatar" :alt="resource.profiles.display_name || resource.profiles.username || 'Profile picture'" :icon-size="19" />
              </div>

              <div>
                <span class="author-label"> Published by </span>

                <strong>
                  {{
                    resource.profiles.display_name || resource.profiles.username || 'Unknown author'
                  }}
                </strong>
              </div>
            </RouterLink>

            <!-- Author without profile -->
            <div v-else class="detail-author">
              <div class="author-avatar">
                <UserAvatar :src="resource.profiles?.avatar_url || resource.profiles?.avatar" :alt="resource.profiles?.display_name || resource.profiles?.username || 'Profile picture'" :icon-size="19" />
              </div>

              <div>
                <span class="author-label"> Published by </span>

                <strong>
                  {{
                    resource.profiles?.display_name ||
                    resource.profiles?.username ||
                    'Unknown author'
                  }}
                </strong>
              </div>
            </div>

            <!-- Price / action -->
            <div class="detail-action-area">
              <div class="detail-price">
                <span class="price-label">
                  {{ resource.is_free ? 'ACCESS' : 'PRICE' }}
                </span>

                <strong>
                  {{ resource.is_free ? 'Free' : `₦${formatPrice(resource.price)}` }}
                </strong>
              </div>

              <button
                type="button"
                class="get-resource-button"
                :disabled="openingResource"
                @click="openResourceFile"
              >
                <LoaderCircle v-if="openingResource" :size="18" class="spin" />

                <Download v-else :size="18" />

                <span>
                  {{
                    openingResource
                      ? 'Preparing...'
                      : resource.is_free
                        ? 'Get Resource'
                        : 'Purchase Resource'
                  }}
                </span>
              </button>
            </div>

            <!-- Social actions -->
            <div class="resource-social-actions">
              <button
                type="button"
                class="social-action"
                :class="{ liked: liked }"
                :disabled="likeLoading"
                @click="toggleLike"
              >
                <LoaderCircle v-if="likeLoading" :size="18" class="spin" />

                <Heart v-else :size="18" :fill="liked ? 'currentColor' : 'none'" />

                <span>
                  {{ likeCount }}
                  {{ likeCount === 1 ? 'Like' : 'Likes' }}
                </span>
              </button>

              <button type="button" class="social-action" @click="openComments">
                <MessageCircle :size="18" />

                <span>
                  {{ commentCount }}
                  {{ commentCount === 1 ? 'Comment' : 'Comments' }}
                </span>
              </button>
            </div>
          </div>
        </section>

        <!-- Lower content -->
        <div class="detail-grid">
          <!-- Main -->
          <main class="detail-body">
            <!-- About -->
            <section class="detail-section">
              <div class="detail-section-heading">
                <div>
                  <span class="section-kicker"> ABOUT THIS RESOURCE </span>

                  <h2>What you'll find</h2>
                </div>
              </div>

              <p v-if="resource.description">
                {{ resource.description }}
              </p>

              <p v-else class="muted-text">No description was provided for this resource.</p>
            </section>

            <!-- Tags -->
            <section v-if="resource.tags?.length" class="detail-section">
              <div class="detail-section-heading">
                <div>
                  <span class="section-kicker"> DISCOVERY </span>

                  <h2>Tags</h2>
                </div>
              </div>

              <div class="detail-tags">
                <span v-for="tag in resource.tags" :key="tag"> #{{ tag }} </span>
              </div>
            </section>

            <!-- Resource information -->
            <section class="detail-section">
              <div class="detail-section-heading">
                <div>
                  <span class="section-kicker"> RESOURCE INFO </span>

                  <h2>Details</h2>
                </div>
              </div>

              <div class="info-grid">
                <div>
                  <span>Category</span>
                  <strong>{{ resource.category }}</strong>
                </div>

                <div>
                  <span>Language</span>
                  <strong>{{ resource.language }}</strong>
                </div>

                <div>
                  <span>File</span>

                  <strong>
                    {{ resource.file_name || 'Resource file' }}
                  </strong>
                </div>

                <div>
                  <span>Access</span>

                  <strong>
                    {{ resource.is_free ? 'Free' : 'Paid' }}
                  </strong>
                </div>
              </div>
            </section>
          </main>

          <!-- Sidebar -->
          <aside class="detail-sidebar">
            <section class="detail-side-card">
              <div class="side-card-icon">
                <ShieldCheck :size="20" />
              </div>

              <h3>Ready when you are</h3>

              <p>Get this resource directly from Follia Library.</p>

              <button
                type="button"
                class="side-get-button"
                :disabled="openingResource"
                @click="openResourceFile"
              >
                <LoaderCircle v-if="openingResource" :size="17" class="spin" />

                <Download v-else :size="17" />

                {{ resource.is_free ? 'Get Resource' : 'Purchase' }}
              </button>
            </section>

            <section class="detail-side-card muted-card">
              <div class="side-card-icon">
                <FileText :size="20" />
              </div>

              <h3>File information</h3>

              <div class="file-info">
                <span>Filename</span>
                <strong>
                  {{ resource.file_name || '—' }}
                </strong>
              </div>

              <div class="file-info">
                <span>Type</span>

                <strong>
                  {{ resource.file_type || 'Document' }}
                </strong>
              </div>
            </section>
          </aside>
        </div>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="showPreview" class="preview-overlay" @click.self="showPreview = false">
        <section class="preview-dialog" role="dialog" aria-modal="true" aria-labelledby="preview-title">
          <header><div><p>RESOURCE PREVIEW</p><h2 id="preview-title">{{ resource?.title }}</h2></div><button type="button" aria-label="Close preview" @click="showPreview = false"><X :size="19" /></button></header>
          <iframe v-if="previewKind === 'pdf'" :src="previewUrl" :title="resource?.title + ' PDF preview'" class="pdf-preview"></iframe>
          <div v-else-if="previewKind === 'image'" class="image-preview"><img :src="previewUrl" :alt="resource?.title || 'Resource preview'" /></div>
          <div v-else class="unsupported-preview"><FileText :size="28" /><strong>{{ resource?.file_type || 'Document' }}</strong><span>This file type cannot be previewed in the browser.</span></div>
          <footer><span>{{ resource?.file_name || 'Resource file' }}</span><a :href="resource?.file_url" class="preview-download"><Download :size="16" /> Download</a></footer>
        </section>
      </div>
      <div v-if="showResourceReport" class="report-overlay" @click.self="showResourceReport = false">
        <form class="report-dialog" @submit.prevent="submitResourceReport">
          <header><div><p>HELP KEEP FOLLIA SAFE</p><h2>Report {{ reportTarget?.type === 'comment' ? 'this comment' : 'this resource' }}</h2></div><button type="button" aria-label="Close" @click="showResourceReport = false"><X :size="18" /></button></header>
          <label for="resource-report-reason">Reason</label>
          <select id="resource-report-reason" v-model="reportReason" required><option value="" disabled>Select a reason</option><option value="spam">Spam</option><option value="harassment">Harassment</option><option value="inappropriate">Inappropriate content</option><option value="impersonation">Impersonation</option><option value="other">Other</option></select>
          <label for="resource-report-details">More details <span>Optional</span></label><textarea id="resource-report-details" v-model="reportDescription" maxlength="500" rows="3"></textarea>
          <p v-if="reportError" class="report-error" role="alert">{{ reportError }}</p>
          <footer><button type="button" class="report-cancel" @click="showResourceReport = false">Cancel</button><button class="report-submit" :disabled="reportLoading || !reportReason">{{ reportLoading ? 'Sending…' : 'Send report' }}</button></footer>
        </form>
      </div>
    </Teleport>

    <!-- Comments modal -->
    <Teleport to="body">
      <div v-if="showComments" class="comments-overlay" @click.self="closeComments">
        <div class="comments-modal">
          <div class="comments-header">
            <div>
              <p class="comments-kicker">DISCUSSION</p>

              <h2>Comments</h2>
            </div>

            <button class="comments-close" @click="closeComments" aria-label="Close comments">
              <X :size="20" />
            </button>
          </div>

          <div class="comments-list">
            <div v-if="commentsLoading" class="comments-loading">
              <LoaderCircle :size="22" class="spin" />
              <span>Loading comments...</span>
            </div>
            <div v-else-if="commentsError" class="comments-error" role="alert">
              <span>{{ commentsError }}</span>
              <button type="button" @click="loadComments">Try again</button>
            </div>
            <template v-else>
            <article v-for="comment in comments" :key="comment.id" class="comment-thread">
            <div class="comment-item">
              <RouterLink
                v-if="comment.profiles?.id"
                :to="{
                  name: 'publisher-detail',
                  params: {
                    id: comment.profiles.user_id || comment.profiles.id,
                  },
                }"
                class="comment-avatar"
                @click.stop
              >
                <UserAvatar :src="comment.profiles.avatar_url || comment.profiles.avatar" :alt="comment.profiles.display_name || comment.profiles.username || 'Profile picture'" :icon-size="15" />
              </RouterLink>

              <div v-else class="comment-avatar"><UserAvatar :icon-size="15" /></div>

              <div class="comment-body">
                <div class="comment-meta">
                  <RouterLink
                    v-if="comment.profiles?.id"
                    :to="{
                      name: 'publisher-detail',
                      params: {
                        id: comment.profiles.user_id || comment.profiles.id,
                      },
                    }"
                    @click.stop
                  >
                    {{
                      comment.profiles.display_name || comment.profiles.username || 'Unknown user'
                    }}
                  </RouterLink>

                  <span>
                    {{ formatCommentTime(comment.created_at) }}
                  </span>
                </div>

                <p>{{ comment.content }}</p>
                <div class="comment-tools"><button type="button" class="comment-like" :class="{ liked: comment.liked }" :disabled="isCommentLikePending(comment)" @click="toggleCommentLike(comment)"><LoaderCircle v-if="isCommentLikePending(comment)" :size="13" class="spin" /><Heart v-else :size="13" :fill="comment.liked ? 'currentColor' : 'none'" /> {{ comment.like_count || 0 }}</button><button type="button" class="reply-comment" @click="replyTo(comment)">Reply</button><button type="button" class="reply-comment" @click="openResourceReport('comment', comment)">Report</button></div>
              </div>
            </div>
              <div v-for="reply in comment.replies || []" :key="reply.id" class="comment-reply">
                <div class="comment-avatar"><UserAvatar :src="reply.profiles?.avatar_url || reply.profiles?.avatar" :alt="reply.profiles?.display_name || reply.profiles?.username || 'Profile picture'" :icon-size="14" /></div>
                <div class="comment-body">
                  <div class="comment-meta"><strong>{{ reply.profiles?.display_name || reply.profiles?.username || 'Follia reader' }}</strong><span>{{ formatCommentTime(reply.created_at) }}</span></div>
                  <p>{{ reply.content }}</p>
                  <div class="comment-tools"><button type="button" class="comment-like" :class="{ liked: reply.liked }" :disabled="isCommentLikePending(reply)" @click="toggleCommentLike(reply)"><LoaderCircle v-if="isCommentLikePending(reply)" :size="13" class="spin" /><Heart v-else :size="13" :fill="reply.liked ? 'currentColor' : 'none'" /> {{ reply.like_count || 0 }}</button><button type="button" class="reply-comment" @click="openResourceReport('comment', reply)">Report</button></div>
                </div>
              </div>
            </article>

            <div v-if="comments.length === 0" class="comments-empty">
              <MessageCircle :size="24" />

              <p>No comments yet.</p>

              <span>Be the first to share your thoughts.</span>
            </div>

            </template>
          </div>

          <form class="comment-input" @submit.prevent="addComment">
            <div v-if="replyingTo" class="replying-to">
              <span>Replying to {{ replyingTo.profiles?.display_name || replyingTo.profiles?.username || 'comment' }}</span>
              <button type="button" aria-label="Cancel reply" @click="replyingTo = null"><X :size="14" /></button>
            </div>
            <p v-if="commentSubmitError" class="comment-submit-error" role="alert">{{ commentSubmitError }}</p>
            <input
              v-model="newComment"
              type="text"
              maxlength="2000"
              :placeholder="replyingTo ? 'Write a reply...' : 'Write a comment...'"
              :disabled="commentSubmitting"
            />

            <button type="submit" :disabled="!newComment.trim() || commentSubmitting">
              <LoaderCircle v-if="commentSubmitting" :size="15" class="spin" />

              <span v-else>Send</span>
            </button>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toastMessage" class="detail-toast">
        {{ toastMessage }}
      </div>
    </Teleport>
  </MainLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  Bookmark,
  Download,
  FileText,
  Eye,
  Flag,
  Heart,
  LoaderCircle,
  MessageCircle,
  Share2,
  ShieldCheck,
  X,
} from 'lucide-vue-next'

import MainLayout from '../layouts/MainLayout.vue'

import { createResourceSignedUrl, getResource, getResourcePreviewUrl } from '../services/resourceService'
import { resolveMediaUrl } from '../utils/media'
import UserAvatar from '../components/UserAvatar.vue'

import { isBookmarked, toggleBookmark } from '../services/bookmarkService'

import {
  getResourceLikeCount,
  isResourceLiked,
  toggleResourceLike,
} from '../services/resourceLikeService'

import {
  addResourceComment,
  getResourceCommentCount,
  getResourceComments,
  toggleResourceCommentLike,
} from '../services/commentService'
import { reportResource, reportResourceComment } from '../services/reportService'

const route = useRoute()
const router = useRouter()

const resource = ref(null)

const loading = ref(true)
const errorMessage = ref('')
const openingResource = ref(false)
const toastMessage = ref('')
const showPreview = ref(false)
const showResourceReport = ref(false)
const reportTarget = ref(null)
const reportReason = ref('')
const reportDescription = ref('')
const reportError = ref('')
const reportLoading = ref(false)

const bookmarked = ref(false)
const bookmarkLoading = ref(false)

const liked = ref(false)
const likeCount = ref(0)
const likeLoading = ref(false)

const comments = ref([])
const commentCount = ref(0)
const commentsLoading = ref(false)
const commentSubmitting = ref(false)
const commentLikePendingIds = ref(new Set())
const commentsError = ref('')
const commentSubmitError = ref('')

const showComments = ref(false)
const newComment = ref('')
const replyingTo = ref(null)
const previewUrl = computed(() => resource.value?.id ? getResourcePreviewUrl(resource.value.id) : '')
const previewKind = computed(() => {
  const type = (resource.value?.file_type || '').toLowerCase()
  const filename = (resource.value?.file_name || '').toLowerCase()
  if (type.includes('pdf') || filename.endsWith('.pdf')) return 'pdf'
  if (type.startsWith('image/') || /\.(png|jpe?g|webp|gif)$/.test(filename)) return 'image'
  return 'unsupported'
})

onMounted(() => {
  loadResource()
})

async function loadResource() {
  loading.value = true
  errorMessage.value = ''

  try {
    const resourceId = route.params.id

    if (!resourceId) {
      throw new Error('No resource was specified.')
    }

    resource.value = await getResource(resourceId)

    /*
     * Load bookmark, like and comment information
     * independently from the main resource.
     *
     * A signed-out visitor can still view resources.
     */
    await Promise.all([
      loadBookmarkState(resourceId),
      loadLikeData(resourceId),
      loadCommentCount(resourceId),
    ])
  } catch (error) {
    console.error('Resource detail error:', error)

    errorMessage.value = error.message || 'Unable to load this resource.'
  } finally {
    loading.value = false
  }
}

async function loadBookmarkState(resourceId) {
  try {
    bookmarked.value = await isBookmarked(resourceId)
  } catch (error) {
    console.error('Bookmark status error:', error)

    bookmarked.value = false
  }
}

async function loadLikeData(resourceId) {
  try {
    const [likedResult, countResult] = await Promise.all([
      isResourceLiked(resourceId),
      getResourceLikeCount(resourceId),
    ])

    liked.value = likedResult
    likeCount.value = countResult
  } catch (error) {
    console.error('Like status error:', error)

    liked.value = false
    likeCount.value = 0
  }
}

async function loadCommentCount(resourceId) {
  try {
    commentCount.value = await getResourceCommentCount(resourceId)
  } catch (error) {
    console.error('Comment count error:', error)

    commentCount.value = 0
  }
}

async function handleBookmark() {
  if (!resource.value) return

  bookmarkLoading.value = true

  try {
    bookmarked.value = await toggleBookmark(resource.value.id, bookmarked.value)

    showToast(bookmarked.value ? 'Added to your bookshelf.' : 'Removed from your bookshelf.')
  } catch (error) {
    console.error('Bookmark error:', error)

    showToast(error?.message || 'You must be signed in to save resources.')
  } finally {
    bookmarkLoading.value = false
  }
}

async function toggleLike() {
  if (!resource.value || likeLoading.value) {
    return
  }

  likeLoading.value = true

  const previousLiked = liked.value
  const previousCount = likeCount.value

  // Optimistic UI
  liked.value = !previousLiked

  likeCount.value = previousLiked ? Math.max(0, previousCount - 1) : previousCount + 1

  try {
    const result = await toggleResourceLike(resource.value.id, previousLiked)

    liked.value = result.liked

    likeCount.value = await getResourceLikeCount(resource.value.id)
  } catch (error) {
    console.error('Like error:', error)

    liked.value = previousLiked
    likeCount.value = previousCount

    showToast(error?.message || 'Unable to update your like.')
  } finally {
    likeLoading.value = false
  }
}

async function openComments() {
  showComments.value = true

  await loadComments()
}

async function loadComments() {
  if (!resource.value?.id) return

  commentsLoading.value = true
  commentsError.value = ''

  try {
    comments.value = await getResourceComments(resource.value.id)
    commentCount.value = comments.value.reduce((count, comment) => count + 1 + (comment.replies?.length || 0), 0)
  } catch (error) {
    console.error('Comments error:', error)
    commentsError.value = error?.message || 'Unable to load comments.'
  } finally {
    commentsLoading.value = false
  }
}

async function addComment() {
  const content = newComment.value.trim()

  if (!content || commentSubmitting.value || !resource.value) {
    return
  }

  commentSubmitting.value = true
  commentSubmitError.value = ''
  let commentCountRefreshed = false

  try {
    const comment = await addResourceComment(resource.value.id, content, replyingTo.value?.id || null)
    if (replyingTo.value) {
      const parent = comments.value.find((item) => item.id === replyingTo.value.id)
      if (parent) parent.replies = [...(parent.replies || []), comment]
      else {
        await loadComments()
        commentCountRefreshed = true
      }
    } else {
      comments.value.unshift({ ...comment, replies: comment.replies || [] })
    }
    if (!commentCountRefreshed) commentCount.value += 1
    newComment.value = ''
    replyingTo.value = null
  } catch (error) {
    console.error('Add comment error:', error)
    commentSubmitError.value = error?.message || 'Unable to add your comment.'
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
    const result = await toggleResourceCommentLike(resource.value.id, comment.id, previous)
    comment.liked = result.liked
    comment.like_count = result.count
  } catch (error) {
    comment.liked = previous
    comment.like_count = Math.max(0, Number(comment.like_count || 0) + (previous ? 1 : -1))
    showToast(error.message || 'Sign in to like this comment.')
  } finally {
    const pendingIds = new Set(commentLikePendingIds.value)
    pendingIds.delete(comment.id)
    commentLikePendingIds.value = pendingIds
  }
}

function isCommentLikePending(comment) {
  return commentLikePendingIds.value.has(comment.id)
}

function openResourceReport(type, comment = null) {
  reportTarget.value = { type, comment }
  reportReason.value = ''
  reportDescription.value = ''
  reportError.value = ''
  showResourceReport.value = true
}

async function submitResourceReport() {
  if (!resource.value || reportLoading.value) return
  reportLoading.value = true
  reportError.value = ''
  try {
    const result = reportTarget.value?.type === 'comment'
      ? await reportResourceComment(resource.value.id, reportTarget.value.comment.id, reportReason.value, reportDescription.value.trim())
      : await reportResource(resource.value.id, reportReason.value, reportDescription.value.trim())
    showResourceReport.value = false
    showToast(result?.duplicate ? 'You have already reported this item.' : 'Thanks. Your report was sent.')
  } catch (error) {
    reportError.value = error.message || 'Unable to send your report.'
  } finally {
    reportLoading.value = false
  }
}

function closeComments() {
  showComments.value = false
  replyingTo.value = null
  commentSubmitError.value = ''
}

function replyTo(comment) {
  replyingTo.value = comment
  commentSubmitError.value = ''
}

async function openResourceFile() {
  if (!resource.value?.file_url) {
    errorMessage.value = 'This resource file is not available yet.'

    return
  }

  /*
   * Paid-resource purchasing will be available here later
   * to Paystack later.
   *
   * For now we only allow the signed URL flow
   * for free resources.
   */
  if (!resource.value.is_free) {
    showToast('Payments will be available here later.')

    return
  }

  openingResource.value = true

  try {
    const signedUrl = await createResourceSignedUrl(resource.value.file_url)

    window.open(resolveMediaUrl(signedUrl), '_blank', 'noopener,noreferrer')
  } catch (error) {
    console.error('Resource access error:', error)

    showToast(error.message || 'Unable to open this resource.')
  } finally {
    openingResource.value = false
  }
}

function goBack() {
  router.back()
}

async function shareResource() {
  const shareData = {
    title: resource.value?.title || 'Follia Library',

    text: resource.value?.description || 'Check out this resource on Follia Library.',

    url: window.location.href,
  }

  try {
    if (navigator.share) {
      await navigator.share(shareData)
      return
    }

    await navigator.clipboard.writeText(window.location.href)

    showToast('Resource link copied.')
  } catch (error) {
    if (error?.name === 'AbortError') {
      return
    }

    showToast('Unable to share this resource.')
  }
}

function showToast(message) {
  toastMessage.value = message

  window.setTimeout(() => {
    toastMessage.value = ''
  }, 3000)
}

function formatPrice(price) {
  return Number(price || 0).toLocaleString('en-NG')
}

function formatCommentTime(dateString) {
  if (!dateString) return ''

  const date = new Date(dateString)
  const now = new Date()

  const difference = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (difference < 60) {
    return 'Just now'
  }

  const minutes = Math.floor(difference / 60)

  if (minutes < 60) {
    return `${minutes}m ago`
  }

  const hours = Math.floor(minutes / 60)

  if (hours < 24) {
    return `${hours}h ago`
  }

  const days = Math.floor(hours / 24)

  if (days < 7) {
    return `${days}d ago`
  }

  return date.toLocaleDateString('en-NG', {
    day: 'numeric',
    month: 'short',
  })
}
</script>

<style scoped>
.resource-detail-page {
  width: min(1180px, 100%);
  margin: 0 auto;
  padding: 28px 24px 100px;
}

.detail-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 26px;
}

.detail-top-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.back-button,
.share-button,
.bookmark-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  color: var(--text-main);
  border-radius: 12px;
  padding: 10px 14px;
  cursor: pointer;
  font: inherit;
  font-weight: 600;
  transition: 0.2s ease;
}

.back-button:hover,
.share-button:hover,
.bookmark-button:hover {
  transform: translateY(-1px);
}

.bookmark-button.bookmarked {
  background: var(--primary-bg);
  border-color: var(--primary-bg);
  color: var(--primary-text);
}

.bookmark-button:disabled {
  opacity: 0.6;
  cursor: wait;
  transform: none;
}

.resource-detail-hero {
  display: grid;
  grid-template-columns: 330px minmax(0, 1fr);
  gap: 46px;
  align-items: start;
  margin-bottom: 55px;
}

.detail-cover {
  width: 100%;
  aspect-ratio: 3 / 4;
  overflow: hidden;
  border-radius: 24px;
  background: var(--surface-soft);
  box-shadow: 0 18px 45px var(--shadow-color);
}

.detail-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.detail-cover-placeholder span {
  font-size: 14px;
  font-weight: 700;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 9px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.meta-dot {
  opacity: 0.5;
}

.detail-main-info h1 {
  margin: 12px 0 16px;
  max-width: 760px;
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1.03;
  letter-spacing: -0.04em;
}

.detail-description {
  max-width: 720px;
  margin: 0;
  color: var(--text-secondary);
  font-size: 17px;
  line-height: 1.75;
}

.detail-author {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  margin-top: 28px;
  color: inherit;
  text-decoration: none;
}

.author-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--text-secondary);
  font-weight: 800;
  width: 46px;
  height: 46px;
}

.author-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-author > div:last-child {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-label {
  color: var(--text-tertiary);
  font-size: 12px;
}

.detail-action-area {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  margin-top: 34px;
  padding-top: 25px;
  border-top: 1px solid var(--border-color);
}

.detail-price {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.price-label {
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.detail-price strong {
  font-size: 24px;
}

.get-resource-button,
.side-get-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  border: 0;
  border-radius: 13px;
  background: var(--primary-bg);
  color: var(--primary-text);
  padding: 13px 19px;
  cursor: pointer;
  font: inherit;
  font-weight: 700;
}

.get-resource-button {
  min-width: 190px;
}

.get-resource-button:disabled,
.side-get-button:disabled {
  opacity: 0.6;
  cursor: wait;
}

/* Social actions */
.resource-social-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
}

.social-action {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 10px 13px;
  background: var(--card-bg);
  color: var(--text-secondary);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  transition: 0.2s ease;
}

.social-action:hover {
  border-color: var(--border-color);
  transform: translateY(-1px);
}

.social-action.liked {
  color: #b84c5a;
  border-color: #e7c4c9;
  background: #fff8f9;
}

.social-action:disabled {
  opacity: 0.6;
  cursor: wait;
  transform: none;
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 50px;
}

.detail-section {
  padding: 30px 0;
  border-top: 1px solid var(--border-color);
}

.detail-section:first-child {
  padding-top: 0;
  border-top: 0;
}

.detail-section-heading {
  margin-bottom: 18px;
}

.section-kicker {
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.09em;
}

.detail-section h2 {
  margin: 5px 0 0;
  font-size: 25px;
  letter-spacing: -0.025em;
}

.detail-section p {
  max-width: 760px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.muted-text {
  color: var(--text-tertiary) !important;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.detail-tags span {
  border: 1px solid var(--border-color);
  border-radius: 999px;
  padding: 8px 12px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  border: 1px solid var(--border-color);
  border-radius: 16px;
  overflow: hidden;
}

.info-grid > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 17px;
  border-right: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

.info-grid > div:nth-child(2n) {
  border-right: 0;
}

.info-grid > div:nth-last-child(-n + 2) {
  border-bottom: 0;
}

.info-grid span {
  color: var(--text-tertiary);
  font-size: 12px;
}

.info-grid strong {
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-side-card {
  padding: 22px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--card-bg);
}

.side-card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  border-radius: 12px;
  background: var(--surface-soft);
}

.detail-side-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.detail-side-card p {
  margin: 0 0 18px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.side-get-button {
  width: 100%;
}

.muted-card {
  background: var(--card-soft);
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 14px;
  margin-top: 14px;
  border-top: 1px solid var(--border-color);
}

.file-info span {
  color: var(--text-tertiary);
  font-size: 12px;
}

.file-info strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.resource-detail-state {
  min-height: 55vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.resource-detail-state .state-icon {
  width: 58px;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  border-radius: 18px;
  background: var(--surface-soft);
}

.resource-detail-state .state-icon.error {
  color: #a44a4a;
}

.resource-detail-state h2 {
  margin: 0 0 7px;
}

.resource-detail-state p {
  margin: 0;
  color: var(--text-secondary);
}

.detail-back-button {
  display: inline-flex;
  margin-top: 20px;
  padding: 11px 16px;
  border-radius: 12px;
  background: var(--primary-bg);
  color: var(--primary-text);
  text-decoration: none;
  font-weight: 700;
}

/* Comments */
.comments-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  overflow-y: auto;
  padding: max(12px, env(safe-area-inset-top))
    max(12px, env(safe-area-inset-right))
    max(12px, env(safe-area-inset-bottom))
    max(12px, env(safe-area-inset-left));
  background: rgba(0, 0, 0, 0.48);
  backdrop-filter: blur(5px);
}

.comments-modal {
  width: min(620px, 100%);
  height: min(720px, calc(100dvh - 40px));
  min-height: min(420px, calc(100dvh - 40px));
  max-height: calc(100dvh - 40px);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  flex: 0 1 auto;
  overflow: hidden;
  border-radius: 24px;
  background: var(--card-bg);
  box-shadow: 0 30px 80px var(--shadow-color);
}

.comments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex: 0 0 auto;
  padding: 22px 24px;
  border-bottom: 1px solid var(--border-color);
}

.comments-kicker {
  margin: 0 0 4px;
  color: var(--text-tertiary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.comments-header h2 {
  margin: 0;
  font-size: 24px;
  letter-spacing: -0.025em;
}

.comments-close {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 11px;
  background: var(--surface-soft);
  color: var(--text-main);
  cursor: pointer;
}

.comments-list {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  padding: 8px 24px 18px;
}

.comment-thread {
  padding: 17px 0;
  border-bottom: 1px solid var(--border-soft);
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 0;
}

.comment-reply {
  display: flex;
  gap: 10px;
  margin: 13px 0 0 48px;
  padding-left: 12px;
  border-left: 2px solid var(--border-color);
}

.comment-reply .comment-avatar {
  width: 30px;
  height: 30px;
  flex-basis: 30px;
}

.comment-avatar {
  flex: 0 0 38px;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  font-weight: 800;
}

.comment-body {
  min-width: 0;
  flex: 1;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}

.comment-meta a,
.comment-meta strong,
.comment-meta > span:first-child {
  color: var(--text-main);
  text-decoration: none;
  font-size: 13px;
  font-weight: 800;
}

.comment-meta > span:last-child {
  color: var(--text-tertiary);
  font-size: 11px;
}

.comment-body p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.reply-comment {
  margin-top: 7px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.reply-comment:hover { color: var(--text-main); }
.comment-tools { display:flex; align-items:center; gap:12px; margin-top:7px; }
.comment-like { display:inline-flex; align-items:center; gap:4px; padding:0; background:transparent; color:var(--text-tertiary); font-size:10px; }
.comment-like.liked { color:#9e463a; }
.comment-like:disabled { cursor:wait; opacity:.7; }

.replying-to {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  color: var(--text-secondary);
  font-size: 11px;
}

.replying-to button {
  display: grid;
  place-items: center;
  padding: 3px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
}

.comment-submit-error,
.comments-error {
  color: #a33b30;
  font-size: 12px;
}

.comments-error {
  min-height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
}

.comments-error button {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 9px;
  background: var(--card-bg);
  color: var(--text-main);
  cursor: pointer;
}

.comments-empty,
.comments-loading {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  text-align: center;
  color: var(--text-tertiary);
}

.comments-empty p {
  margin: 5px 0 0;
  color: var(--text-secondary);
  font-weight: 700;
}

.comments-empty span,
.comments-loading span {
  font-size: 13px;
}

.comment-input {
  display: flex;
  flex: 0 0 auto;
  gap: 9px;
  padding: 16px 20px max(16px, env(safe-area-inset-bottom));
  border-top: 1px solid var(--border-color);
  background: var(--card-soft);
}

.comment-input input {
  min-width: 0;
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px 13px;
  outline: none;
  background: var(--input-bg);
  color: var(--text-main);
  font: inherit;
}

.comment-input input:focus {
  border-color: var(--border-color);
}

.comment-input button {
  min-width: 64px;
  border: 0;
  border-radius: 12px;
  background: var(--primary-bg);
  color: var(--primary-text);
  padding: 0 15px;
  cursor: pointer;
  font: inherit;
  font-weight: 700;
}

.comment-input button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.detail-toast {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 3000;
  padding: 13px 17px;
  border-radius: 13px;
  background: var(--primary-bg);
  color: var(--primary-text);
  box-shadow: 0 15px 40px var(--shadow-color);
  font-size: 14px;
  font-weight: 600;
}

.spin {
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .resource-detail-hero {
    grid-template-columns: 240px minmax(0, 1fr);
    gap: 30px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-sidebar {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .resource-detail-page {
    padding: 18px 16px 90px;
  }

  .resource-detail-hero {
    grid-template-columns: 1fr;
    gap: 28px;
  }

  .detail-cover {
    width: min(270px, 75%);
    margin: 0 auto;
  }

  .detail-main-info h1 {
    font-size: 38px;
  }

  .detail-action-area {
    align-items: stretch;
    flex-direction: column;
  }

  .get-resource-button {
    width: 100%;
  }

  .resource-social-actions {
    width: 100%;
  }

  .social-action {
    flex: 1;
    justify-content: center;
  }

  .detail-sidebar {
    display: flex;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .info-grid > div,
  .info-grid > div:nth-child(2n) {
    border-right: 0;
    border-bottom: 1px solid var(--border-color);
  }

  .info-grid > div:last-child {
    border-bottom: 0;
  }

  .detail-topbar span {
    display: none;
  }

  .detail-top-actions {
    gap: 7px;
  }

  .detail-top-actions .bookmark-button,
  .detail-top-actions .share-button {
    padding: 10px 12px;
  }

  .comments-overlay {
    align-items: flex-end;
    padding: max(12px, env(safe-area-inset-top)) 0 0;
  }

  .comments-modal {
    width: 100%;
    height: calc(100dvh - max(12px, env(safe-area-inset-top)));
    min-height: min(420px, calc(100dvh - max(12px, env(safe-area-inset-top))));
    max-height: calc(100dvh - max(12px, env(safe-area-inset-top)));
    flex: 0 0 auto;
    border-right: 0;
    border-bottom: 0;
    border-left: 0;
    border-radius: 24px 24px 0 0;
  }

  .comments-header {
    padding: 18px;
  }

  .comments-list {
    padding-left: 18px;
    padding-right: 18px;
  }

  .comment-input {
    padding: 12px;
  }
}
.preview-overlay,.report-overlay { position:fixed; inset:0; z-index:500; display:grid; place-items:center; padding:18px; background:rgba(14,15,17,.62); backdrop-filter:blur(5px); }
.preview-dialog { width:min(980px,100%); height:min(86dvh,760px); display:grid; grid-template-rows:auto minmax(0,1fr) auto; overflow:hidden; border:1px solid var(--border-color); border-radius:20px; background:var(--card-bg); box-shadow:0 24px 80px rgba(0,0,0,.28); }
.preview-dialog header,.preview-dialog footer { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:13px 17px; }
.preview-dialog header { border-bottom:1px solid var(--border-soft); }
.preview-dialog header p { margin:0 0 4px; color:var(--text-tertiary); font-size:9px; font-weight:750; letter-spacing:.13em; }
.preview-dialog header h2 { max-width:75vw; margin:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font:750 16px Manrope,sans-serif; }
.preview-dialog header > button { width:32px; height:32px; display:grid; place-items:center; border-radius:9px; background:var(--icon-bg); color:var(--text-main); }
.preview-dialog footer { border-top:1px solid var(--border-soft); color:var(--text-tertiary); font-size:10px; }
.preview-dialog footer > span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.preview-download { display:inline-flex; align-items:center; gap:6px; flex-shrink:0; padding:8px 11px; border-radius:9px; background:var(--primary-bg); color:var(--primary-text); font-size:11px; font-weight:700; }
.pdf-preview { width:100%; height:100%; border:0; background:#e7e9ec; }
.image-preview { display:grid; place-items:center; overflow:auto; padding:18px; background:#e7e9ec; }
.image-preview img { display:block; max-width:100%; max-height:100%; object-fit:contain; }
.unsupported-preview { display:grid; align-content:center; justify-items:center; gap:10px; color:var(--text-secondary); }
.unsupported-preview span { color:var(--text-tertiary); font-size:12px; }
.report-dialog { width:min(430px,100%); display:grid; gap:9px; padding:21px; border:1px solid var(--border-color); border-radius:19px; background:var(--card-bg); }
.report-dialog header,.report-dialog footer { display:flex; align-items:center; justify-content:space-between; gap:10px; }
.report-dialog header { margin-bottom:6px; padding:0; border:0; }
.report-dialog header p { margin:0 0 4px; color:var(--text-tertiary); font-size:9px; font-weight:750; letter-spacing:.13em; }
.report-dialog h2 { margin:0; font:750 19px Manrope,sans-serif; }
.report-dialog header > button { width:32px; height:32px; display:grid; place-items:center; border-radius:9px; background:var(--icon-bg); color:var(--text-main); }
.report-dialog label { margin-top:5px; color:var(--text-secondary); font-size:11px; font-weight:700; }
.report-dialog label span { color:var(--text-tertiary); font-weight:400; }
.report-dialog select,.report-dialog textarea { width:100%; padding:10px 11px; border:1px solid var(--border-color); border-radius:10px; outline:0; background:var(--input-bg); color:var(--text-main); font:inherit; font-size:12px; }
.report-dialog textarea { resize:vertical; }
.report-dialog footer { justify-content:flex-end; margin-top:8px; padding:0; border:0; }
.report-cancel,.report-submit { min-height:36px; padding:0 12px; border-radius:10px; font-size:11px; font-weight:700; }
.report-cancel { border:1px solid var(--border-color); background:transparent; color:var(--text-secondary); }
.report-submit { background:var(--primary-bg); color:var(--primary-text); }
.report-submit:disabled { opacity:.5; }
.report-error { margin:0; color:#a33b30; font-size:11px; }
</style>
