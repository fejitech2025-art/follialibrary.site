<template>
  <section class="book-club-explorer">
    <div class="book-club-heading">
      <div>
        <p class="book-club-kicker">COMMUNITY</p>
        <h2>Book Clubs</h2>
        <p>Find people who enjoy the same stories, books, and ideas.</p>
      </div>

      <button class="create-club-button" @click="showCreateModal = true">
        <Plus :size="18" />
        <span>Create Club</span>
      </button>
    </div>

    <!-- Search -->
    <div class="book-club-search">
      <Search :size="19" />

      <input
        v-model="search"
        type="search"
        placeholder="Search book clubs..."
      />

      <button
        v-if="search"
        class="clear-search"
        aria-label="Clear search"
        @click="search = ''"
      >
        <X :size="16" />
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="book-club-state">
      <LoaderCircle :size="24" class="spin" />
      <span>Finding book clubs...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="book-club-state error">
      <p>{{ error }}</p>
      <button @click="loadClubs">Try again</button>
    </div>

    <!-- Empty -->
    <div v-else-if="clubs.length === 0" class="book-club-empty">
      <div class="empty-icon">
        <Users :size="26" />
      </div>

      <h3>{{ search ? 'No clubs found' : 'No book clubs yet' }}</h3>

      <p>
        {{
          search
            ? 'Try another search.'
            : 'Create the first book club and start the conversation.'
        }}
      </p>

      <button
        v-if="!search"
        class="create-club-button"
        @click="showCreateModal = true"
      >
        <Plus :size="18" />
        Create Book Club
      </button>
    </div>

    <!-- Clubs -->
    <div v-else class="book-club-grid">
      <article
        v-for="club in clubs"
        :key="club.id"
        class="book-club-card"
        @click="openClub(club.id)"
      >
        <div class="book-club-card-avatar">
          <img
            v-if="getClubAvatarUrl(club)"
            :src="getClubAvatarUrl(club)"
            :alt="club.name"
            @error="handleClubAvatarError(club.id)"
          />

          <span v-else>
            {{ getInitial(club.name) }}
          </span>
        </div>

        <div class="book-club-card-content">
          <h3>{{ club.name }}</h3>

          <p class="book-club-description">
            {{ club.description || 'A Follia Book Club.' }}
          </p>

          <div class="book-club-card-meta">
            <span>
              <Users :size="15" />
              {{ club.book_club_members?.length || 0 }}
              members
            </span>

            <span v-if="club.profiles">
              {{ club.profiles.display_name || club.profiles.username }}
            </span>
          </div>
        </div>

        <ChevronRight :size="19" />
      </article>
    </div>

    <!-- Create modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal"
        class="club-modal-overlay"
        @click.self="closeCreateModal"
      >
        <div class="club-modal">
          <div class="club-modal-header">
            <div>
              <p class="book-club-kicker">NEW CLUB</p>
              <h2>Create a Book Club</h2>
            </div>

            <button
              class="club-modal-close"
              aria-label="Close modal"
              @click="closeCreateModal"
            >
              <X :size="20" />
            </button>
          </div>

          <form @submit.prevent="createClub">
            <!-- Club image -->
            <div class="club-avatar-picker">
              <div class="club-avatar-preview">
                <img
                  v-if="avatarPreview"
                  :src="avatarPreview"
                  alt="Club preview"
                />

                <span v-else>
                  {{ getInitial(form.name) }}
                </span>
              </div>

              <div class="club-avatar-picker-info">
                <strong>Club profile image</strong>
                <p>Give your club its own identity.</p>

                <div class="club-avatar-buttons">
                  <button type="button" @click="avatarInput?.click()">
                    Choose image
                  </button>

                  <button
                    v-if="avatarPreview"
                    type="button"
                    class="remove-avatar"
                    @click="removeAvatar"
                  >
                    Remove
                  </button>
                </div>
              </div>

              <input
                ref="avatarInput"
                class="hidden-file-input"
                type="file"
                accept="image/*"
                @change="handleAvatar"
              />
            </div>

            <label>
              Club name

              <input
                v-model="form.name"
                type="text"
                maxlength="80"
                placeholder="e.g. African Fiction Readers"
                required
              />
            </label>

            <label>
              Description

              <textarea
                v-model="form.description"
                maxlength="500"
                rows="4"
                placeholder="What is this club about?"
              />
            </label>

            <div class="club-modal-actions">
              <button
                type="button"
                class="secondary-button"
                @click="closeCreateModal"
              >
                Cancel
              </button>

              <button
                type="submit"
                class="primary-button"
                :disabled="creating"
              >
                <LoaderCircle
                  v-if="creating"
                  :size="16"
                  class="spin"
                />

                <span>
                  {{ creating ? 'Creating...' : 'Create Club' }}
                </span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { resolveMediaUrl } from '../utils/media'

import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import {
  ChevronRight,
  LoaderCircle,
  Plus,
  Search,
  Users,
  X,
} from 'lucide-vue-next'

import {
  createBookClub,
  getBookClubs,
} from '../services/bookClubService'

const router = useRouter()

const search = ref('')
const clubs = ref([])

const loading = ref(false)
const error = ref('')

const showCreateModal = ref(false)
const creating = ref(false)
const failedClubAvatars = ref(new Set())

const avatarInput = ref(null)
const avatarFile = ref(null)
const avatarPreview = ref(null)

function getClubAvatarUrl(club) {
  if (failedClubAvatars.value.has(club.id)) {
    return null
  }

  return resolveMediaUrl(club.avatar_url)
}

function handleClubAvatarError(clubId) {
  failedClubAvatars.value = new Set([
    ...failedClubAvatars.value,
    clubId,
  ])
}

onMounted(() => {
  loadClubs()
})

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  cleanupPreview()
})

watch(search, () => {
  clearTimeout(searchTimer)

  searchTimer = setTimeout(() => {
    loadClubs()
  }, 300)
})

async function loadClubs() {
  loading.value = true
  error.value = ''

  try {
    clubs.value = await getBookClubs(search.value)

    // Reset image failures when the list is refreshed.
    failedClubAvatars.value = new Set()
  } catch (err) {
    console.error('Book clubs error:', err)
    error.value = err?.message || 'Unable to load book clubs.'
  } finally {
    loading.value = false
  }
}

async function createClub() {
  if (!form.value.name.trim() || creating.value) {
    return
  }

  creating.value = true

  try {
    const club = await createBookClub({
      name: form.value.name,
      description: form.value.description,
      avatarFile: avatarFile.value,
    })

    closeCreateModal()

    router.push({
      name: 'book-club',
      params: {
        id: club.id,
      },
    })
  } catch (err) {
    console.error('Create book club error:', err)
    window.alert(err?.message || 'Unable to create the book club.')
  } finally {
    creating.value = false
  }
}

function handleAvatar(event) {
  const file = event.target.files?.[0]

  if (!file) return

  if (!file.type.startsWith('image/')) {
    window.alert('Please select an image file.')
    event.target.value = ''
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    window.alert('Image must be smaller than 5MB.')
    event.target.value = ''
    return
  }

  cleanupPreview()

  avatarFile.value = file
  avatarPreview.value = URL.createObjectURL(file)
}

function removeAvatar() {
  cleanupPreview()

  avatarFile.value = null
  avatarPreview.value = null

  if (avatarInput.value) {
    avatarInput.value.value = ''
  }
}

function cleanupPreview() {
  if (avatarPreview.value?.startsWith('blob:')) {
    URL.revokeObjectURL(avatarPreview.value)
  }

  // Do not leave a revoked blob URL in the preview.
  avatarPreview.value = null
}

function closeCreateModal() {
  showCreateModal.value = false

  cleanupPreview()

  avatarFile.value = null

  if (avatarInput.value) {
    avatarInput.value.value = ''
  }

  form.value = {
    name: '',
    description: '',
  }
}

function openClub(clubId) {
  router.push({
    name: 'book-club',
    params: {
      id: clubId,
    },
  })
}

function getInitial(name) {
  if (!name) return 'F'

  return name.trim().charAt(0).toUpperCase()
}
</script>

<style scoped>
.book-club-explorer {
  width: 100%;
}

.book-club-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.book-club-kicker {
  margin: 0 0 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--text-tertiary);
}

.book-club-heading h2 {
  margin: 0;
  color: var(--text-main);
  font-size: 28px;
}

.book-club-heading p:not(.book-club-kicker) {
  margin: 7px 0 0;
  color: var(--text-secondary);
}

.create-club-button,
.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 0;
  border-radius: 12px;
  background: var(--primary-bg);
  color: var(--primary-text);
  padding: 11px 16px;
  font-weight: 700;
  cursor: pointer;
}

.book-club-search {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 0 14px;
  margin-bottom: 22px;
  border: 1px solid var(--border-color);
  border-radius: 15px;
  background: var(--input-bg);
  color: var(--text-tertiary);
}

.book-club-search input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text-main);
  font: inherit;
}

.clear-search,
.club-modal-close {
  border: 0;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
}

.book-club-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.book-club-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 18px;
  border: 1px solid var(--border-soft);
  border-radius: 20px;
  background: var(--card-bg);
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.book-club-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px var(--shadow-color);
}

.book-club-card-avatar {
  width: 58px;
  height: 58px;
  min-width: 58px;
  border-radius: 17px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--icon-bg);
  color: var(--text-main);
  font-size: 21px;
  font-weight: 800;
}

.book-club-card-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.book-club-card-content {
  min-width: 0;
  flex: 1;
}

.book-club-card-content h3 {
  margin: 0;
  color: var(--text-main);
  font-size: 16px;
}

.book-club-description {
  margin: 5px 0 10px;
  color: var(--text-secondary);
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.book-club-card-meta {
  display: flex;
  gap: 12px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.book-club-card-meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.book-club-state,
.book-club-empty {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-secondary);
}

.book-club-empty h3 {
  margin: 15px 0 5px;
  color: var(--text-main);
}

.book-club-empty p {
  margin: 0 0 18px;
}

.empty-icon {
  width: 58px;
  height: 58px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--icon-bg);
  color: var(--text-main);
}

.club-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.45);
}

.club-modal {
  width: min(520px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  padding: 24px;
  border-radius: 24px;
  background: var(--card-bg);
  box-shadow: 0 25px 70px var(--shadow-color);
}

.club-modal-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.club-modal-header h2 {
  margin: 0;
  color: var(--text-main);
}

.club-modal form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.club-modal label {
  display: flex;
  flex-direction: column;
  gap: 7px;
  color: var(--text-main);
  font-size: 14px;
  font-weight: 700;
}

.club-modal input,
.club-modal textarea {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--input-bg);
  color: var(--text-main);
  padding: 12px 13px;
  font: inherit;
  outline: none;
}

.club-modal textarea {
  resize: vertical;
}

.club-avatar-picker {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  border: 1px solid var(--border-soft);
  border-radius: 15px;
  background: var(--card-soft);
}

.club-avatar-preview {
  width: 68px;
  height: 68px;
  min-width: 68px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 19px;
  background: var(--icon-bg);
  color: var(--text-main);
  font-size: 24px;
  font-weight: 800;
}

.club-avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.club-avatar-picker-info {
  min-width: 0;
}

.club-avatar-picker-info strong {
  display: block;
  color: var(--text-main);
  font-size: 13px;
}

.club-avatar-picker-info p {
  margin: 3px 0 8px;
  color: var(--text-tertiary);
  font-size: 11px;
}

.club-avatar-buttons {
  display: flex;
  gap: 7px;
}

.club-avatar-buttons button {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 6px 9px;
  background: var(--card-bg);
  color: var(--text-main);
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
}

.club-avatar-buttons .remove-avatar {
  color: #d94c4c;
}

.hidden-file-input {
  display: none;
}

.club-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.secondary-button {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: transparent;
  color: var(--text-main);
  padding: 11px 16px;
  cursor: pointer;
  font-weight: 700;
}

@media (max-width: 700px) {
  .book-club-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .create-club-button {
    width: 100%;
  }

  .book-club-grid {
    grid-template-columns: 1fr;
  }

  .book-club-card {
    padding: 15px;
  }

  .club-avatar-picker {
    align-items: flex-start;
  }
}
</style>
