<template>
  <MainLayout>
    <div class="publishers-page">
      <section class="publishers-hero">
        <div>
          <p class="eyebrow">DISCOVER PEOPLE</p>

          <h1>Publishers</h1>

          <p class="publishers-intro">
            Discover people sharing useful books, notes, guides and learning resources.
          </p>
        </div>

        <div class="publisher-search">
          <Search :size="18" />

          <input v-model="searchQuery" type="search" placeholder="Search publishers..." />
        </div>
      </section>

      <!-- Loading -->
      <section v-if="loading" class="publishers-state">
        <div class="state-icon">
          <LoaderCircle :size="24" class="spin" />
        </div>

        <h2>Loading publishers...</h2>

        <p>Finding people and creators on Follia Library.</p>
      </section>

      <!-- Error -->
      <section v-else-if="error" class="publishers-state error-state">
        <div class="state-icon">
          <AlertCircle :size="24" />
        </div>

        <h2>Couldn't load publishers</h2>

        <p>{{ error }}</p>

        <button class="retry-button" @click="loadPublishers">Try again</button>
      </section>

      <!-- Empty -->
      <section v-else-if="filteredPublishers.length === 0" class="publishers-state">
        <div class="state-icon">
          <Users :size="24" />
        </div>

        <h2>No publishers found</h2>

        <p>
          {{
            searchQuery
              ? 'Try searching for another name.'
              : 'Publishers will appear here once people start sharing resources.'
          }}
        </p>
      </section>

      <!-- Publishers -->
      <section v-else class="publishers-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">PEOPLE TO EXPLORE</p>

            <h2>All publishers</h2>
          </div>

          <span class="publisher-count">
            {{ filteredPublishers.length }}
            {{ filteredPublishers.length === 1 ? 'publisher' : 'publishers' }}
          </span>
        </div>

        <div class="publishers-grid">
          <RouterLink
            v-for="publisher in filteredPublishers"
            :key="publisher.id"
            :to="{
              name: 'publisher-detail',
              params: { id: publisher.id },
            }"
            class="publisher-card"
          >
            <!-- Avatar -->
            <div class="publisher-avatar">
              <img
                v-if="publisher.avatar_url || publisher.avatar"
                :src="resolveMediaUrl(publisher.avatar_url || publisher.avatar)"
                :alt="publisher.display_name || publisher.username"
              />

              <span v-else>
                {{ getInitials(publisher) }}
              </span>
            </div>

            <!-- Publisher information -->
            <div class="publisher-card-info">
              <h3>
                {{ publisher.display_name || publisher.username || 'Publisher' }}
              </h3>

              <p v-if="publisher.username">@{{ publisher.username }}</p>

              <span>
                {{ publisher.bio || 'Sharing useful learning resources.' }}
              </span>
            </div>

            <!-- Arrow -->
            <div class="publisher-arrow">
              <ArrowUpRight :size="18" />
            </div>
          </RouterLink>
        </div>
      </section>
    </div>
  </MainLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { AlertCircle, ArrowUpRight, LoaderCircle, Search, Users } from 'lucide-vue-next'

import MainLayout from '../layouts/MainLayout.vue'

import { getPublishers } from '../services/publisherService'
import { resolveMediaUrl } from '../utils/media'

const publishers = ref([])

const loading = ref(true)

const error = ref('')

const searchQuery = ref('')

const filteredPublishers = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  if (!query) {
    return publishers.value
  }

  return publishers.value.filter((publisher) => {
    const name = publisher.display_name?.toLowerCase() || ''

    const username = publisher.username?.toLowerCase() || ''

    const bio = publisher.bio?.toLowerCase() || ''

    return name.includes(query) || username.includes(query) || bio.includes(query)
  })
})

function getInitials(publisher) {
  const name = publisher.display_name || publisher.username || 'P'

  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('')
}

async function loadPublishers() {
  loading.value = true

  error.value = ''

  try {
    publishers.value = await getPublishers()
  } catch (err) {
    console.error('Publishers error:', err)

    error.value = err?.message || 'Something went wrong.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPublishers()
})
</script>

<style scoped>
.publishers-page {
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 24px 120px;
}

/* =========================================================
   HERO
========================================================= */

.publishers-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 32px;
  margin-bottom: 48px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  color: var(--text-secondary);
}

.publishers-hero h1 {
  margin: 0;
  font-size: clamp(34px, 5vw, 52px);
  line-height: 1;
  letter-spacing: -0.045em;
}

.publishers-intro {
  max-width: 570px;
  margin: 18px 0 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.7;
}

/* =========================================================
   SEARCH
========================================================= */

.publisher-search {
  width: min(340px, 100%);
  min-width: 260px;
  height: 48px;

  display: flex;
  align-items: center;
  gap: 10px;

  padding: 0 16px;

  border: 1px solid var(--border-color);
  border-radius: 16px;

  background: var(--input-bg);
  color: var(--text-tertiary);
}

.publisher-search input {
  width: 100%;

  border: 0;
  outline: 0;

  background: transparent;
  color: inherit;

  font: inherit;
}

.publisher-search input::placeholder {
  color: var(--text-tertiary);
}

/* =========================================================
   SECTION HEADING
========================================================= */

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;

  margin-bottom: 20px;
}

.section-heading h2 {
  margin: 0;
  font-size: 25px;
  letter-spacing: -0.03em;
}

.publisher-count {
  color: var(--text-tertiary);
  font-size: 13px;
}

/* =========================================================
   PUBLISHER GRID
========================================================= */

.publishers-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

/* =========================================================
   PUBLISHER CARD
========================================================= */

.publisher-card {
  position: relative;

  display: flex;

  /*
   * IMPORTANT:
   *
   * Align the avatar with the top of the publisher name
   * instead of vertically centering it against the whole
   * text block.
   */
  align-items: flex-start;

  gap: 16px;

  min-height: 130px;

  padding: 20px;

  border: 1px solid var(--border-color);
  border-radius: 22px;

  background: var(--card-bg);
  color: inherit;

  text-decoration: none;

  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.publisher-card:hover {
  transform: translateY(-3px);

  border-color: var(--border-color);

  box-shadow: 0 12px 30px var(--shadow-color);
}

/* =========================================================
   AVATAR
========================================================= */

.publisher-avatar {
  width: 58px;
  height: 58px;

  flex: 0 0 58px;

  overflow: hidden;

  display: grid;
  place-items: center;

  /*
   * Keeps the avatar aligned directly with
   * the publisher name at the top.
   */
  margin-top: 0;

  border-radius: 18px;

  background: #eef0ff;
  color: #4f5bd5;

  font-size: 17px;
  font-weight: 800;
}

.publisher-avatar img {
  width: 100%;
  height: 100%;

  display: block;

  object-fit: cover;
}

/* =========================================================
   PUBLISHER INFO
========================================================= */

.publisher-card-info {
  min-width: 0;

  flex: 1;

  padding-right: 24px;
}

.publisher-card-info h3 {
  margin: 0;

  overflow: hidden;

  font-size: 16px;
  font-weight: 750;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.publisher-card-info p {
  margin: 4px 0 8px;

  color: var(--text-tertiary);

  font-size: 12px;
}

.publisher-card-info span {
  display: -webkit-box;

  overflow: hidden;

  color: var(--text-secondary);

  font-size: 13px;
  line-height: 1.45;

  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

/* =========================================================
   ARROW
========================================================= */

.publisher-arrow {
  position: absolute;

  top: 18px;
  right: 18px;

  display: grid;
  place-items: center;

  color: var(--text-tertiary);
}

/* =========================================================
   STATES
========================================================= */

.publishers-state {
  min-height: 320px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  text-align: center;
}

.state-icon {
  width: 52px;
  height: 52px;

  display: grid;
  place-items: center;

  margin-bottom: 16px;

  border-radius: 17px;

  background: var(--surface-soft);
  color: var(--text-secondary);
}

.publishers-state h2 {
  margin: 0;

  font-size: 20px;
}

.publishers-state p {
  max-width: 420px;

  margin: 8px 0 0;

  color: var(--text-tertiary);

  font-size: 14px;
  line-height: 1.6;
}

.retry-button {
  margin-top: 20px;

  padding: 11px 17px;

  border: 0;
  border-radius: 12px;

  background: var(--primary-bg);
  color: var(--primary-text);

  font: inherit;

  cursor: pointer;
}

/* =========================================================
   ANIMATION
========================================================= */

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* =========================================================
   TABLET
========================================================= */

@media (max-width: 900px) {
  .publishers-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .publishers-hero {
    align-items: stretch;
    flex-direction: column;
  }

  .publisher-search {
    width: 100%;
  }
}

/* =========================================================
   MOBILE
========================================================= */

@media (max-width: 600px) {
  .publishers-page {
    padding: 24px 16px 110px;
  }

  .publishers-grid {
    grid-template-columns: 1fr;
  }

  .publisher-card {
    min-height: 112px;
  }

  .section-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }
}
</style>
