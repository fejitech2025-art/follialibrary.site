<template>
  <MainLayout>
    <section class="explore-page">
      <header class="explore-heading">
        <div>
          <p class="page-kicker">OPEN A NEW DOOR</p>
          <h1>Explore <span>anything.</span></h1>
          <p>People, conversations, resources and communities across Follia.</p>
        </div>
        <div class="explore-symbol"><Compass :size="22" /></div>
      </header>

      <form class="discovery-search" @submit.prevent="submitSearch">
        <Search :size="19" />
        <input
          v-model="query"
          type="search"
          placeholder="Search people, posts, books, clubs…"
          aria-label="Search all of Follia"
        />
        <button
          v-if="query"
          type="button"
          aria-label="Clear search"
          @click="clearSearch"
        >
          <X :size="17" />
        </button>
      </form>

      <div class="discovery-tabs" role="tablist" aria-label="Explore category">
        <button
          v-for="option in tabs"
          :key="option.key"
          type="button"
          role="tab"
          :aria-selected="activeTab === option.key"
          :class="{ active: activeTab === option.key }"
          @click="activeTab = option.key"
        >
          {{ option.label }}
          <span v-if="resultCount(option.key)">
            {{ resultCount(option.key) }}
          </span>
        </button>
      </div>

      <!-- Loading skeleton: preserved -->
      <div v-if="loading" class="explore-loading">
        <div v-for="n in 4" :key="n" class="loading-row"></div>
      </div>

      <div v-else-if="error" class="explore-empty">
        <div class="empty-mark"><Search :size="20" /></div>
        <h2>Search is taking a moment.</h2>
        <p>{{ error }}</p>
        <button type="button" @click="runSearch">Try again</button>
      </div>

      <div v-else-if="isEmpty" class="explore-empty">
        <div class="empty-mark"><Search :size="20" /></div>
        <h2>No matches yet.</h2>
        <p>Try a broader word or browse one of the other discovery tabs.</p>
        <button v-if="query" type="button" @click="clearSearch">
          Clear search
        </button>
      </div>

      <div v-else class="explore-results">
        <!-- People -->
        <section
          v-if="showUsers && results.users.length"
          class="result-section"
        >
          <div class="section-title">
            <div>
              <small>CREATORS & READERS</small>
              <h2>People</h2>
            </div>
            <span>{{ results.users.length }}</span>
          </div>

          <div class="people-grid">
            <RouterLink
              v-for="person in results.users"
              :key="person.id"
              :to="{ name: 'publisher-detail', params: { id: person.id } }"
              class="person-card"
            >
              <div class="person-avatar">
                <img
                  v-if="personAvatarUrl(person) && !hasFailedImage(`person-${person.id}`)"
                  :src="personAvatarUrl(person)"
                  alt=""
                  @error="handleImageError(`person-${person.id}`)"
                />
                <span v-else>
                  {{ (person.display_name || person.username || 'F').charAt(0).toUpperCase() }}
                </span>
              </div>

              <strong>{{ person.display_name || person.username }}</strong>
              <small>@{{ person.username }}</small>
              <p v-if="person.bio">{{ person.bio }}</p>
              <span class="person-stats">
                {{ person.follower_count || 0 }} followers
              </span>
            </RouterLink>
          </div>
        </section>

        <!-- Posts -->
        <section
          v-if="showPosts && results.posts.length"
          class="result-section"
        >
          <div class="section-title">
            <div>
              <small>CONVERSATION</small>
              <h2>Posts</h2>
            </div>
            <span>{{ results.posts.length }}</span>
          </div>

          <div class="feed-results">
            <FeedItemCard
              v-for="post in results.posts"
              :key="'post-' + post.id"
              :item="{ ...post, kind: 'post' }"
            />
          </div>
        </section>

        <!-- Resources -->
        <section
          v-if="showResources && results.resources.length"
          class="result-section"
        >
          <div class="section-title">
            <div>
              <small>BOOKS & RESOURCES</small>
              <h2>Library</h2>
            </div>
            <span>{{ results.resources.length }}</span>
          </div>

          <div class="feed-results">
            <FeedItemCard
              v-for="resource in results.resources"
              :key="'resource-' + resource.id"
              :item="{
                ...resource,
                kind: 'resource',
                author: resource.profiles,
                body: resource.description
              }"
            />
          </div>
        </section>

        <!-- Book Clubs -->
        <section
          v-if="showClubs && results.clubs.length"
          class="result-section"
        >
          <div class="section-title">
            <div>
              <small>READ TOGETHER</small>
              <h2>Book Clubs</h2>
            </div>
            <span>{{ results.clubs.length }}</span>
          </div>

          <div class="clubs-grid">
            <RouterLink
              v-for="club in results.clubs"
              :key="club.id"
              :to="{ name: 'book-club', params: { id: club.id } }"
              class="club-card"
            >
              <div class="club-avatar">
                <img
                  v-if="clubAvatarUrl(club) && !hasFailedImage(`club-${club.id}`)"
                  :src="clubAvatarUrl(club)"
                  alt=""
                  @error="handleImageError(`club-${club.id}`)"
                />
                <UsersRound v-else :size="22" />
              </div>

              <span>
                <strong>{{ club.name }}</strong>
                <small>
                  {{ club.member_count || club.members?.length || 0 }} members
                </small>
              </span>

              <ArrowUpRight :size="17" />

              <p>
                {{ club.description || 'A place to read, discuss and share recommendations.' }}
              </p>
            </RouterLink>
          </div>
        </section>
      </div>
    </section>
  </MainLayout>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowUpRight,
  Compass,
  Search,
  UsersRound,
  X,
} from 'lucide-vue-next'

import MainLayout from '../layouts/MainLayout.vue'
import FeedItemCard from '../components/FeedItemCard.vue'

import { getFeed } from '../services/postService'
import { getPublishers } from '../services/publisherService'
import { getBookClubs } from '../services/bookClubService'
import { searchLibrary } from '../services/searchService'

const route = useRoute()
const router = useRouter()

/*
|--------------------------------------------------------------------------
| Backend media URL handling
|--------------------------------------------------------------------------
|
| Development:
| VITE_API_URL=http://127.0.0.1:8000/api
|
| Production:
| Set VITE_API_URL to your deployed backend API URL.
*/

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
  if (!url || typeof url !== 'string') {
    return null
  }

  const value = url.trim()

  if (!value) {
    return null
  }

  // Preserve full URLs and temporary local image previews.
  if (/^(https?:\/\/|blob:|data:)/i.test(value)) {
    return value
  }

  if (value.startsWith('//')) {
    return `${window.location.protocol}${value}`
  }

  try {
    // Resolve Django paths such as /media/avatars/user.jpg
    // against the backend origin rather than the Vue origin.
    return new URL(value, `${API_BASE_URL}/`).href
  } catch (error) {
    console.error('Unable to resolve media URL:', error)
    return null
  }
}

/*
|--------------------------------------------------------------------------
| Image helpers
|--------------------------------------------------------------------------
*/

const failedImages = ref(new Set())

function hasFailedImage(key) {
  return failedImages.value.has(key)
}

function handleImageError(key) {
  failedImages.value = new Set([
    ...failedImages.value,
    key,
  ])
}

function personAvatarUrl(person) {
  return resolveMediaUrl(
    person?.avatar_url ||
    person?.avatar ||
    person?.user?.avatar_url ||
    person?.user?.avatar,
  )
}

function clubAvatarUrl(club) {
  return resolveMediaUrl(
    club?.avatar_url ||
    club?.avatar,
  )
}

/*
|--------------------------------------------------------------------------
| Discovery state
|--------------------------------------------------------------------------
*/

const query = ref(String(route.query.q || ''))
const activeTab = ref('all')
const loading = ref(true)
const error = ref('')

const results = ref({
  users: [],
  posts: [],
  resources: [],
  clubs: [],
})

const tabs = [
  { key: 'all', label: 'All' },
  { key: 'people', label: 'People' },
  { key: 'posts', label: 'Posts' },
  { key: 'resources', label: 'Resources' },
  { key: 'clubs', label: 'Book Clubs' },
]

const showUsers = computed(
  () => activeTab.value === 'all' || activeTab.value === 'people',
)

const showPosts = computed(
  () => activeTab.value === 'all' || activeTab.value === 'posts',
)

const showResources = computed(
  () => activeTab.value === 'all' || activeTab.value === 'resources',
)

const showClubs = computed(
  () => activeTab.value === 'all' || activeTab.value === 'clubs',
)

const totalResults = computed(() =>
  Object.values(results.value).reduce(
    (total, list) => total + list.length,
    0,
  ),
)

const resultCount = (key) => {
  if (key === 'all') {
    return totalResults.value
  }

  const resultKey = {
    people: 'users',
    posts: 'posts',
    resources: 'resources',
    clubs: 'clubs',
  }[key]

  return resultKey ? results.value[resultKey].length : 0
}

const isEmpty = computed(() => totalResults.value === 0)

/*
|--------------------------------------------------------------------------
| Load discovery
|--------------------------------------------------------------------------
*/

async function loadDiscovery() {
  loading.value = true
  error.value = ''

  try {
    const [feed, users, clubs] = await Promise.all([
      getFeed('for-you'),
      getPublishers(),
      getBookClubs(),
    ])

    results.value = {
      users: users.slice(0, 8),
      posts: feed.filter((item) => item.kind === 'post').slice(0, 8),
      resources: feed.filter((item) => item.kind === 'resource').slice(0, 8),
      clubs: clubs.slice(0, 8),
    }
  } catch (err) {
    error.value = err.message || 'Unable to load discovery right now.'
  } finally {
    loading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Search
|--------------------------------------------------------------------------
*/

async function runSearch() {
  loading.value = true
  error.value = ''

  try {
    if (!query.value.trim()) {
      await loadDiscovery()
      return
    }

    const searchResults = await searchLibrary(query.value.trim())

    results.value = {
      users: searchResults.users || [],
      posts: searchResults.posts || [],
      resources: searchResults.resources || [],
      clubs: searchResults.clubs || [],
    }
  } catch (err) {
    error.value = err.message || 'Unable to search Follia right now.'
  } finally {
    loading.value = false
  }
}

function submitSearch() {
  router.replace({
    name: 'explore',
    query: query.value.trim()
      ? { q: query.value.trim() }
      : {},
  })

  runSearch()
}

function clearSearch() {
  query.value = ''

  router.replace({ name: 'explore' })

  runSearch()
}

watch(
  () => route.query.q,
  (value) => {
    const next = String(value || '')

    if (query.value !== next) {
      query.value = next
    }

    runSearch()
  },
)

onMounted(() => {
  if (query.value) {
    runSearch()
  } else {
    loadDiscovery()
  }
})
</script>

<style scoped>
.explore-page { max-width:1000px; margin:0 auto; padding-bottom:35px; }
.explore-heading { display:flex; align-items:flex-end; justify-content:space-between; gap:22px; padding:4px 0 24px; }
.page-kicker { margin:0 0 10px; color:var(--text-tertiary); font-size:10px; font-weight:750; letter-spacing:.15em; }
.explore-heading h1 { margin:0; font:800 clamp(34px,5vw,53px)/1.06 Manrope,sans-serif; letter-spacing:-.06em; }
.explore-heading h1 span { color:var(--text-secondary); }
.explore-heading p:not(.page-kicker) { margin:10px 0 0; color:var(--text-secondary); font-size:13px; }
.explore-symbol { width:54px; height:54px; flex:0 0 54px; display:grid; place-items:center; border-radius:17px; background:var(--primary-bg); color:var(--primary-text); }
.discovery-search { height:56px; display:flex; align-items:center; gap:12px; padding:0 15px; border:1px solid var(--border-color); border-radius:16px; background:var(--card-bg); color:var(--text-tertiary); box-shadow:0 3px 15px color-mix(in srgb,var(--shadow-color) 35%,transparent); }
.discovery-search input { flex:1; min-width:0; height:100%; border:0; outline:0; background:transparent; color:var(--text-main); font-size:13px; }
.discovery-search button { width:31px; height:31px; display:grid; place-items:center; border-radius:9px; background:var(--icon-bg); color:var(--text-secondary); }
.discovery-tabs { display:flex; gap:7px; margin:17px 0 25px; overflow:auto; scrollbar-width:none; }
.discovery-tabs::-webkit-scrollbar { display:none; }
.discovery-tabs button { flex-shrink:0; display:flex; align-items:center; gap:6px; padding:9px 13px; border:1px solid var(--border-color); border-radius:999px; background:var(--card-bg); color:var(--text-secondary); font-size:11px; font-weight:650; }
.discovery-tabs button.active { border-color:var(--primary-bg); background:var(--primary-bg); color:var(--primary-text); }
.discovery-tabs button span { opacity:.68; font-size:9px; }
.explore-results { display:grid; gap:31px; }
.result-section { min-width:0; }
.section-title { display:flex; align-items:flex-end; justify-content:space-between; margin-bottom:13px; }
.section-title small { color:var(--text-tertiary); font-size:9px; font-weight:750; letter-spacing:.13em; }
.section-title h2 { margin:4px 0 0; font:750 23px Manrope,sans-serif; letter-spacing:-.04em; }
.section-title > span { min-width:25px; padding:5px 7px; border-radius:8px; background:var(--icon-bg); color:var(--text-secondary); text-align:center; font-size:10px; }
.people-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:11px; }
.person-card { min-width:0; display:flex; flex-direction:column; align-items:flex-start; padding:15px; border:1px solid var(--border-color); border-radius:17px; background:var(--card-bg); }
.person-avatar { width:44px; height:44px; display:grid; place-items:center; overflow:hidden; margin-bottom:12px; border-radius:50%; background:var(--icon-bg); font-size:13px; font-weight:750; }
.person-avatar img { width:100%; height:100%; object-fit:cover; }
.person-card > strong { max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:12px; }
.person-card > small { margin-top:3px; color:var(--text-tertiary); font-size:10px; }
.person-card p { display:-webkit-box; min-height:32px; margin:9px 0 8px; color:var(--text-secondary); font-size:10px; line-height:1.5; overflow:hidden; -webkit-box-orient:vertical; -webkit-line-clamp:2; }
.person-stats { color:var(--text-tertiary); font-size:10px; }
.feed-results { display:grid; gap:12px; max-width:700px; }
.clubs-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:11px; }
.club-card { display:grid; grid-template-columns:42px 1fr 18px; align-items:center; gap:11px; padding:14px; border:1px solid var(--border-color); border-radius:16px; background:var(--card-bg); }
.club-avatar { width:42px; height:42px; display:grid; place-items:center; overflow:hidden; border-radius:13px; background:var(--icon-bg); color:var(--text-secondary); }
.club-avatar img { width:100%; height:100%; object-fit:cover; }
.club-card > span { min-width:0; }
.club-card strong,.club-card small { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.club-card strong { font-size:12px; }
.club-card small { margin-top:3px; color:var(--text-tertiary); font-size:10px; }
.club-card > svg { color:var(--text-tertiary); }
.club-card p { grid-column:1/-1; margin:0; color:var(--text-secondary); font-size:11px; line-height:1.5; }

/* Original loading skeleton and shimmer animation preserved. */
.explore-loading { display:grid; gap:12px; }
.loading-row { height:130px; border:1px solid var(--border-color); border-radius:17px; background:linear-gradient(100deg,var(--card-bg),var(--icon-bg),var(--card-bg)); background-size:200% 100%; animation:shimmer 1.3s ease infinite; }
@keyframes shimmer { to { background-position:-200% 0; } }

.explore-empty { display:flex; flex-direction:column; align-items:center; padding:55px 24px; border:1px dashed var(--border-color); border-radius:20px; background:var(--card-bg); text-align:center; }
.empty-mark { width:46px; height:46px; display:grid; place-items:center; border-radius:14px; background:var(--icon-bg); color:var(--text-secondary); }
.explore-empty h2 { margin:15px 0 0; font:750 18px Manrope,sans-serif; }
.explore-empty p { max-width:390px; margin:8px 0 18px; color:var(--text-secondary); font-size:12px; line-height:1.6; }
.explore-empty button { padding:10px 13px; border-radius:10px; background:var(--primary-bg); color:var(--primary-text); font-size:11px; font-weight:700; }
@media(max-width:760px) { .people-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media(max-width:520px) { .explore-heading { align-items:flex-start; } .explore-heading h1 { font-size:37px; } .explore-symbol { width:46px; height:46px; flex-basis:46px; } .discovery-search { height:52px; } .clubs-grid { grid-template-columns:1fr; } .section-title h2 { font-size:20px; } }
@media(max-width:360px) { .explore-heading h1 { font-size:32px; } .person-card { padding:12px; } }
</style>
