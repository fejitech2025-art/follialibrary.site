<template>
  <MainLayout>
    <section class="search-page">
      <div class="search-page-header">
        <div>
          <p class="search-kicker">FOLLIA LIBRARY</p>

          <h1>
            Search
            <span v-if="query">for "{{ query }}"</span>
          </h1>

          <p class="search-description">Discover resources and publishers across Follia Library.</p>
        </div>

        <div class="search-box">
          <Search :size="20" />

          <input
            ref="searchInput"
            v-model="searchInput"
            type="text"
            placeholder="Search books, resources, publishers..."
            @keyup.enter="performSearch"
          />

          <button
            v-if="searchInput"
            class="search-clear"
            type="button"
            aria-label="Clear search"
            @click="clearSearch"
          >
            <X :size="17" />
          </button>

          <button class="search-submit" type="button" @click="performSearch">Search</button>
        </div>
      </div>

      <!-- Empty initial state -->
      <div v-if="!query && !loading" class="search-empty">
        <div class="search-empty-icon">
          <Search :size="28" />
        </div>

        <h2>What are you looking for?</h2>

        <p>Search for books, study materials, publishers, categories, or topics.</p>
      </div>

      <!-- Loading -->
      <div v-else-if="loading" class="search-loading">
        <div class="loading-spinner"></div>

        <p>Searching Follia Library...</p>
      </div>

      <!-- Error -->
      <div v-else-if="errorMessage" class="search-error">
        <AlertCircle :size="22" />

        <div>
          <strong>Something went wrong.</strong>
          <p>{{ errorMessage }}</p>
        </div>

        <button type="button" @click="performSearch">Try again</button>
      </div>

      <!-- Results -->
      <div v-else class="search-results">
        <div class="results-summary">
          <span>
            {{ totalResults }}
            {{ totalResults === 1 ? 'result' : 'results' }}
          </span>
        </div>

        <!-- Publishers -->
        <section v-if="publishers.length" class="results-section">
          <div class="results-section-header">
            <div>
              <p class="section-kicker">PEOPLE</p>
              <h2>Publishers</h2>
            </div>

            <span class="result-count">
              {{ publishers.length }}
            </span>
          </div>

          <div class="publishers-grid">
            <RouterLink
              v-for="publisher in publishers"
              :key="publisher.id"
              :to="{
                name: 'publisher-detail',
                params: {
                  id: publisher.id,
                },
              }"
              class="publisher-card"
            >
              <div class="publisher-avatar">
                <img
                  v-if="publisher.avatar_url || publisher.avatar"
                  :src="resolveMediaUrl(publisher.avatar_url || publisher.avatar)"
                  :alt="publisher.display_name || publisher.username || 'Publisher'"
                />

                <span v-else>
                  {{
                    (publisher.display_name || publisher.username || 'P').charAt(0).toUpperCase()
                  }}
                </span>
              </div>

              <div class="publisher-info">
                <h3>
                  {{ publisher.display_name || publisher.username || 'Unknown publisher' }}
                </h3>

                <p v-if="publisher.username">@{{ publisher.username }}</p>

                <span v-if="publisher.bio">
                  {{ publisher.bio }}
                </span>
              </div>

              <ArrowUpRight :size="18" />
            </RouterLink>
          </div>
        </section>

        <!-- Resources -->
        <section v-if="resources.length" class="results-section">
          <div class="results-section-header">
            <div>
              <p class="section-kicker">RESOURCES</p>
              <h2>Library resources</h2>
            </div>

            <span class="result-count">
              {{ resources.length }}
            </span>
          </div>

          <div class="resources-grid">
            <ResourceCard v-for="resource in resources" :key="resource.id" :resource="resource" />
          </div>
        </section>

        <!-- No results -->
        <div v-if="!resources.length && !publishers.length" class="no-results">
          <div class="no-results-icon">
            <Search :size="26" />
          </div>

          <h2>No results found</h2>

          <p>
            We couldn't find anything matching
            <strong>"{{ query }}"</strong>.
          </p>

          <span> Try another keyword, title, category, or publisher. </span>
        </div>
      </div>
    </section>
  </MainLayout>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertCircle, ArrowUpRight, Search, X } from 'lucide-vue-next'

import MainLayout from '../layouts/MainLayout.vue'
import ResourceCard from '../components/ResourceCard.vue'
import { searchLibrary } from '../services/searchService'
import { resolveMediaUrl } from '../utils/media'

const route = useRoute()
const router = useRouter()

const searchInput = ref('')
const loading = ref(false)
const errorMessage = ref('')

const resources = ref([])
const publishers = ref([])

const query = computed(() => {
  return typeof route.query.q === 'string' ? route.query.q.trim() : ''
})

const totalResults = computed(() => {
  return resources.value.length + publishers.value.length
})

async function loadSearchResults() {
  if (!query.value) {
    resources.value = []
    publishers.value = []
    errorMessage.value = ''
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const results = await searchLibrary(query.value)

    resources.value = results.resources
    publishers.value = results.publishers
  } catch (error) {
    console.error('Search error:', error)

    resources.value = []
    publishers.value = []

    errorMessage.value = error?.message || 'Unable to complete your search right now.'
  } finally {
    loading.value = false
  }
}

async function performSearch() {
  const value = searchInput.value.trim()

  if (!value) {
    router.push({ name: 'search' })
    return
  }

  router.push({
    name: 'search',
    query: {
      q: value,
    },
  })
}

function clearSearch() {
  searchInput.value = ''

  router.push({
    name: 'search',
  })

  nextTick(() => {
    searchInput.value = ''
  })
}

watch(
  () => route.query.q,
  async (newQuery) => {
    searchInput.value = typeof newQuery === 'string' ? newQuery : ''

    await loadSearchResults()
  },
  { immediate: true },
)

onMounted(() => {
  nextTick(() => {
    if (query.value) {
      searchInput.value = query.value
    }
  })
})
</script>

<style scoped>
.search-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 34px 20px 110px;
}

.search-page-header {
  display: grid;
  gap: 26px;
  margin-bottom: 42px;
}

.search-kicker,
.section-kicker {
  margin: 0 0 8px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.search-page-header h1 {
  margin: 0;
  font-size: clamp(32px, 5vw, 52px);
  line-height: 1.02;
  letter-spacing: -0.045em;
  color: var(--text-main);
}

.search-page-header h1 span {
  color: var(--text-secondary);
}

.search-description {
  max-width: 620px;
  margin: 14px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 58px;
  padding: 7px 8px 7px 17px;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 18px;
  box-shadow: 0 12px 35px var(--shadow-color);
}

.search-box > svg {
  flex-shrink: 0;
  color: var(--text-secondary);
}

.search-box input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text-main);
  font: inherit;
}

.search-box input::placeholder {
  color: var(--text-tertiary);
}

.search-clear,
.search-submit {
  border: 0;
  cursor: pointer;
  font: inherit;
}

.search-clear {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 10px;
  background: transparent;
  color: var(--text-secondary);
}

.search-clear:hover {
  background: var(--surface-soft);
  color: var(--text-main);
}

.search-submit {
  min-height: 42px;
  padding: 0 17px;
  border-radius: 12px;
  background: var(--primary-bg);
  color: var(--primary-text);
  font-weight: 700;
}

.search-submit:hover {
  opacity: 0.9;
}

.search-empty,
.no-results,
.search-loading {
  display: flex;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  min-height: 340px;
  padding: 40px 20px;
  text-align: center;
}

.search-empty-icon,
.no-results-icon {
  display: grid;
  width: 64px;
  height: 64px;
  margin-bottom: 20px;
  place-items: center;
  border-radius: 20px;
  background: var(--surface-soft);
  color: var(--text-secondary);
}

.search-empty h2,
.no-results h2 {
  margin: 0;
  color: var(--text-main);
  font-size: 24px;
  letter-spacing: -0.025em;
}

.search-empty p,
.no-results p {
  max-width: 500px;
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.no-results span {
  margin-top: 6px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.search-loading {
  gap: 14px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-bg);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.search-error {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  border: 1px solid #e8dcdc;
  border-radius: 18px;
  background: #fffafa;
  color: #7a4a4a;
}

.search-error svg {
  flex-shrink: 0;
}

.search-error strong {
  display: block;
  margin-bottom: 3px;
  color: #4e2929;
}

.search-error p {
  margin: 0;
  font-size: 14px;
}

.search-error button {
  margin-left: auto;
  padding: 9px 14px;
  border: 0;
  border-radius: 10px;
  background: var(--primary-bg);
  color: var(--primary-text);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
}

.results-summary {
  margin-bottom: 24px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.results-section {
  margin-bottom: 48px;
}

.results-section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.results-section-header h2 {
  margin: 0;
  font-size: 25px;
  letter-spacing: -0.03em;
  color: var(--text-main);
}

.result-count {
  display: grid;
  min-width: 34px;
  height: 30px;
  padding: 0 9px;
  place-items: center;
  border-radius: 10px;
  background: var(--surface-soft);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 800;
}

.publishers-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.publisher-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--card-bg);
  color: inherit;
  text-decoration: none;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.publisher-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-color);
  box-shadow: 0 12px 30px var(--shadow-color);
}

.publisher-avatar {
  display: grid;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  overflow: hidden;
  place-items: center;
  border-radius: 15px;
  background: var(--surface-soft);
  color: var(--text-secondary);
  font-weight: 800;
}

.publisher-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.publisher-info {
  flex: 1;
  min-width: 0;
}

.publisher-info h3 {
  margin: 0;
  overflow: hidden;
  color: var(--text-main);
  font-size: 15px;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.publisher-info p {
  margin: 3px 0 0;
  color: var(--text-tertiary);
  font-size: 13px;
}

.publisher-info span {
  display: block;
  overflow: hidden;
  margin-top: 7px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.publisher-card > svg {
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.resources-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

@media (max-width: 900px) {
  .resources-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .search-page {
    padding: 24px 16px 100px;
  }

  .search-page-header {
    gap: 20px;
    margin-bottom: 32px;
  }

  .search-box {
    min-height: 54px;
    border-radius: 16px;
  }

  .search-submit {
    min-height: 40px;
    padding: 0 13px;
  }

  .publishers-grid {
    grid-template-columns: 1fr;
  }

  .resources-grid {
    grid-template-columns: 1fr;
  }

  .search-error {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .search-error button {
    width: 100%;
    margin-left: 0;
  }
}

@media (max-width: 460px) {
  .search-box {
    flex-wrap: wrap;
    padding: 10px;
  }

  .search-box > svg {
    margin-left: 4px;
  }

  .search-box input {
    min-width: calc(100% - 45px);
  }

  .search-clear {
    margin-left: auto;
  }

  .search-submit {
    width: 100%;
  }
}
</style>
