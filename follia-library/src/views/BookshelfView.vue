
<template>
  <MainLayout>
    <section class="saved-page">
      <header class="saved-heading">
        <div>
          <p class="page-kicker">YOUR COLLECTION</p>
          <h1>Saved for later.</h1>
          <p>Posts and resources you want to come back to.</p>
        </div>

        <div class="save-mark">
          <Bookmark :size="21" />
        </div>
      </header>

      <div v-if="loading" class="saved-state">
        <LoaderCircle :size="23" class="spin" />
        <p>Loading saved items…</p>
      </div>

      <div v-else-if="error" class="saved-state">
        <h2>Couldn't load your saved items</h2>
        <p>{{ error }}</p>
        <button @click="loadBookmarks">Try again</button>
      </div>

      <template v-else>
        <div class="saved-tabs" role="tablist" aria-label="Saved item type">
          <button
            v-for="tab in tabs"
            :key="tab"
            :class="{ active: activeTab === tab }"
            role="tab"
            :aria-selected="activeTab === tab"
            @click="activeTab = tab"
          >
            {{ tab }}
          </button>
        </div>

        <div v-if="bookmarks.length === 0" class="saved-state empty">
          <div class="empty-icon">
            <Bookmark :size="25" />
          </div>

          <h2>Nothing saved yet</h2>
          <p>Save a post or resource when you find something worth revisiting.</p>
          <RouterLink to="/explore">Explore Follia</RouterLink>
        </div>

        <div v-else-if="filteredItems.length === 0" class="saved-state empty">
          <div class="empty-icon">
            <Bookmark :size="25" />
          </div>

          <h2>No {{ activeTab.toLowerCase() }} saved</h2>
          <p>Try another tab or explore Follia for something new.</p>
        </div>

        <template v-else>
          <div class="saved-count">
            {{ filteredItems.length }}
            saved {{ filteredItems.length === 1 ? 'item' : 'items' }}
          </div>

          <div class="saved-feed">
            <FeedItemCard
              v-for="item in filteredItems.filter((entry) => entry.kind === 'post')"
              :key="'post-' + item.id"
              :item="item.posts"
            />
          </div>

          <div class="resource-grid">
            <ResourceCard
              v-for="item in filteredItems.filter((entry) => entry.kind === 'resource')"
              :key="'resource-' + item.id"
              :resource="normalizeResource(item.resources)"
            />
          </div>
        </template>
      </template>
    </section>
  </MainLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Bookmark, LoaderCircle } from 'lucide-vue-next'
import MainLayout from '../layouts/MainLayout.vue'
import FeedItemCard from '../components/FeedItemCard.vue'
import ResourceCard from '../components/ResourceCard.vue'
import { getMyBookmarks } from '../services/bookmarkService'

const configuredApiUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL

const API_BASE_URL = (
  configuredApiUrl ||
  (import.meta.env.DEV
    ? 'http://127.0.0.1:8000'
    : window.location.origin)
)
  .replace(/\/+$/, '')
  .replace(/\/api$/i, '')

function resolveMediaUrl(url) {
  if (!url || typeof url !== 'string') return null

  const value = url.trim()

  if (!value) return null

  // Keep absolute URLs and temporary local image previews unchanged.
  if (/^(https?:\/\/|blob:|data:)/i.test(value)) {
    return value
  }

  if (value.startsWith('//')) {
    return `${window.location.protocol}${value}`
  }

  try {
    // Django media paths such as /media/resource-covers/cover.jpg
    // must resolve against the backend origin, not the Vue origin.
    return new URL(value, `${API_BASE_URL}/`).href
  } catch (error) {
    console.error('Unable to resolve media URL:', error)
    return null
  }
}

const bookmarks = ref([])
const loading = ref(true)
const error = ref('')
const activeTab = ref('All')

const tabs = ['All', 'Posts', 'Resources']

const filteredItems = computed(() =>
  bookmarks.value.filter(
    (item) =>
      activeTab.value === 'All' ||
      item.kind === activeTab.value.toLowerCase().slice(0, -1),
  ),
)

function normalizeResource(resource) {
  if (!resource) return {}

  const cover = resource.cover_url || resource.cover || null

  return {
    ...resource,

    // Support both the API's URL field and a relative Django media path.
    cover_url: resolveMediaUrl(cover),
    cover: resolveMediaUrl(cover),

    free: resource.is_free ?? resource.free,

    author:
      resource.profiles?.display_name ||
      resource.profiles?.username ||
      resource.author ||
      'Follia creator',

    authorProfile: resource.profiles?.id
      ? `/profile/${resource.profiles.id}`
      : resource.authorProfile || null,
  }
}

async function loadBookmarks() {
  loading.value = true
  error.value = ''

  try {
    bookmarks.value = await getMyBookmarks()
  } catch (err) {
    error.value =
      err.message || 'We could not load your saved items.'
  } finally {
    loading.value = false
  }
}

onMounted(loadBookmarks)
</script>

<style scoped>
.saved-page {
  max-width: 960px;
  margin: 0 auto;
  padding-bottom: 35px;
}

.saved-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin: 3px 0 22px;
}

.page-kicker {
  margin: 0 0 10px;
  color: var(--text-tertiary);
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.14em;
}

.saved-heading h1 {
  margin: 0;
  font: 800 clamp(34px, 5vw, 52px) / 1.05 Manrope, sans-serif;
  letter-spacing: -0.06em;
}

.saved-heading p:not(.page-kicker) {
  margin: 9px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.save-mark {
  width: 52px;
  height: 52px;
  flex: 0 0 52px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: var(--primary-bg);
  color: var(--primary-text);
}

.saved-tabs {
  display: flex;
  gap: 7px;
  margin: 18px 0;
}

.saved-tabs button {
  padding: 9px 13px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--card-bg);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 650;
}

.saved-tabs button.active {
  border-color: var(--primary-bg);
  background: var(--primary-bg);
  color: var(--primary-text);
}

.saved-count {
  margin: 0 0 12px;
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 650;
}

.saved-feed {
  display: grid;
  gap: 12px;
  max-width: 700px;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-top: 12px;
}

.saved-state {
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 30px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--card-bg);
  color: var(--text-secondary);
  text-align: center;
}

.saved-state h2 {
  margin: 0;
  color: var(--text-main);
  font: 750 18px Manrope, sans-serif;
}

.saved-state p {
  max-width: 390px;
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
}

.saved-state button,
.saved-state a {
  margin-top: 8px;
  padding: 10px 13px;
  border-radius: 10px;
  background: var(--primary-bg);
  color: var(--primary-text);
  font-size: 11px;
  font-weight: 700;
}

.empty-icon {
  width: 47px;
  height: 47px;
  display: grid;
  place-items: center;
  border-radius: 15px;
  background: var(--icon-bg);
  color: var(--text-secondary);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 740px) {
  .resource-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 11px;
  }
}

@media (max-width: 380px) {
  .saved-heading h1 {
    font-size: 37px;
  }

  .save-mark {
    width: 45px;
    height: 45px;
    flex-basis: 45px;
  }
}
</style>
