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
                  id: resource.profiles.id,
                },
              }"
              class="detail-author"
            >
              <div class="author-avatar">
                <img
                  v-if="resource.profiles.avatar_url || resource.profiles.avatar"
                  :src="resolveMediaUrl(resource.profiles.avatar_url || resource.profiles.avatar)"
                  alt=""
                />

                <span v-else>
                  {{ getInitial(resource.profiles.display_name || resource.profiles.username) }}
                </span>
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
                <span>
                  {{ getInitial(resource.profiles?.display_name || resource.profiles?.username) }}
                </span>
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
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <RouterLink
                v-if="comment.profiles?.id"
                :to="{
                  name: 'publisher-detail',
                  params: {
                    id: comment.profiles.id,
                  },
                }"
                class="comment-avatar"
                @click.stop
              >
                {{ getInitial(comment.profiles.display_name || comment.profiles.username) }}
              </RouterLink>

              <div v-else class="comment-avatar">?</div>

              <div class="comment-body">
                <div class="comment-meta">
                  <RouterLink
                    v-if="comment.profiles?.id"
                    :to="{
                      name: 'publisher-detail',
                      params: {
                        id: comment.profiles.id,
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
              </div>
            </div>

            <div v-if="comments.length === 0 && !commentsLoading" class="comments-empty">
              <MessageCircle :size="24" />

              <p>No comments yet.</p>

              <span> Be the first to share your thoughts. </span>
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

            <button :disabled="!newComment.trim() || commentSubmitting" @click="addComment">
              <LoaderCircle v-if="commentSubmitting" :size="15" class="spin" />

              <span v-else>Send</span>
            </button>
          </div>
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
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  Bookmark,
  Download,
  FileText,
  Heart,
  LoaderCircle,
  MessageCircle,
  Share2,
  ShieldCheck,
  X,
} from 'lucide-vue-next'

import MainLayout from '../layouts/MainLayout.vue'

import { createResourceSignedUrl, getResource } from '../services/resourceService'
import { resolveMediaUrl } from '../utils/media'

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
} from '../services/commentService'

const route = useRoute()
const router = useRouter()

const resource = ref(null)

const loading = ref(true)
const errorMessage = ref('')
const openingResource = ref(false)
const toastMessage = ref('')

const bookmarked = ref(false)
const bookmarkLoading = ref(false)

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

  try {
    comments.value = await getResourceComments(resource.value.id)

    commentCount.value = comments.value.length
  } catch (error) {
    console.error('Comments error:', error)

    showToast('Unable to load comments.')
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

  try {
    const comment = await addResourceComment(resource.value.id, content)

    comments.value.unshift(comment)

    commentCount.value = comments.value.length

    newComment.value = ''
  } catch (error) {
    console.error('Add comment error:', error)

    showToast(error?.message || 'Unable to add your comment.')
  } finally {
    commentSubmitting.value = false
  }
}

function closeComments() {
  showComments.value = false
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

function getInitial(name) {
  if (!name) return '?'

  return name.trim().charAt(0).toUpperCase()
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
  padding: 20px;
  background: rgba(0, 0, 0, 0.48);
  backdrop-filter: blur(5px);
}

.comments-modal {
  width: min(620px, 100%);
  max-height: min(720px, 90vh);
  display: flex;
  flex-direction: column;
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
  flex: 1;
  min-height: 180px;
  overflow-y: auto;
  padding: 8px 24px 18px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 17px 0;
  border-bottom: 1px solid var(--border-soft);
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
  gap: 9px;
  padding: 16px 20px;
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
    padding: 0;
  }

  .comments-modal {
    width: 100%;
    max-height: 88vh;
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
</style>
