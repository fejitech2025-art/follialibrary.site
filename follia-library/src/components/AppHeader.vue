<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- Brand -->
      <RouterLink to="/" class="brand">
        <BrandLogo />

        <div class="brand-text">
          <span class="brand-name">Follia</span>
          <span class="brand-subtitle">library</span>
        </div>
      </RouterLink>

      <!-- Search -->
      <form class="header-search" @submit.prevent="performSearch">
        <Search :size="19" />

        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search anything..."
          aria-label="Search Follia"
        />

        <button
          v-if="searchQuery"
          type="button"
          class="search-clear"
          aria-label="Clear search"
          @click="clearSearch"
        >
          ×
        </button>

        <button type="submit" class="search-shortcut" aria-label="Search">
          /
        </button>
      </form>

      <!-- Header Actions -->
      <div class="header-actions">
        <!-- Profile -->
        <RouterLink to="/account" class="profile-button" aria-label="Account">
          <div class="profile-avatar">
            <img
              v-if="avatarUrl"
              :src="avatarUrl"
              alt="Profile"
              @error="handleAvatarError"
            />

            <span v-else>{{ userInitial }}</span>
          </div>
        </RouterLink>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from 'lucide-vue-next'

import BrandLogo from './BrandLogo.vue'
import { useAuth } from '../composables/useAuth'
import { getMyProfile } from '../services/profileService'

const router = useRouter()
const { user: authUser, initializeAuth } = useAuth()

const searchQuery = ref('')
const user = ref(null)
const profile = ref(null)
const avatarLoadFailed = ref(false)

/*
|--------------------------------------------------------------------------
| Django API URL
|--------------------------------------------------------------------------
|
| Development:
|   VITE_API_URL=http://127.0.0.1:8000/api
|
| Production:
|   Set VITE_API_URL to your deployed Django API URL.
|
| We remove a trailing /api because uploaded media is served from
| the Django backend's /media/ path, not /api/media/.
|
*/

const configuredApiUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL

const API_BASE_URL = (
  configuredApiUrl ||
  (
    import.meta.env.DEV
      ? 'http://127.0.0.1:8000'
      : window.location.origin
  )
)
  .replace(/\/+$/, '')
  .replace(/\/api$/i, '')

/*
|--------------------------------------------------------------------------
| Resolve avatar URLs
|--------------------------------------------------------------------------
|
| Handles:
|   /media/avatars/photo.jpg
|   media/avatars/photo.jpg
|   https://your-backend.com/media/avatars/photo.jpg
|
| Absolute URLs are preserved.
|
*/

function resolveMediaUrl(url) {
  if (!url || typeof url !== 'string') {
    return null
  }

  const trimmedUrl = url.trim()

  if (!trimmedUrl) {
    return null
  }

  // Keep fully qualified URLs unchanged.
  if (/^https?:\/\//i.test(trimmedUrl)) {
    return trimmedUrl
  }

  // Handle protocol-relative URLs.
  if (trimmedUrl.startsWith('//')) {
    return `${window.location.protocol}${trimmedUrl}`
  }

  try {
    return new URL(trimmedUrl, `${API_BASE_URL}/`).href
  } catch (error) {
    console.error('Invalid avatar URL:', error)
    return null
  }
}

/*
|--------------------------------------------------------------------------
| Avatar URL
|--------------------------------------------------------------------------
*/

const rawAvatarUrl = computed(() => {
  return (
    profile.value?.avatar_url ||
    profile.value?.avatar ||
    user.value?.user_metadata?.avatar_url ||
    null
  )
})

const avatarUrl = computed(() => {
  if (avatarLoadFailed.value) {
    return null
  }

  return resolveMediaUrl(rawAvatarUrl.value)
})

// If the user's profile or avatar changes, try loading the new image.
watch(rawAvatarUrl, () => {
  avatarLoadFailed.value = false
})

/*
|--------------------------------------------------------------------------
| Fallback initial
|--------------------------------------------------------------------------
*/

const userInitial = computed(() => {
  const name =
    profile.value?.display_name ||
    profile.value?.username ||
    user.value?.email ||
    'F'

  return String(name).charAt(0).toUpperCase()
})

/*
|--------------------------------------------------------------------------
| Load authenticated user and profile
|--------------------------------------------------------------------------
*/

async function loadUser() {
  try {
    await initializeAuth()

    user.value = authUser.value

    if (user.value) {
      profile.value = await getMyProfile()
    } else {
      profile.value = null
    }
  } catch (error) {
    console.error('Profile loading error:', error)
  }
}

/*
|--------------------------------------------------------------------------
| Avatar error fallback
|--------------------------------------------------------------------------
*/

function handleAvatarError() {
  avatarLoadFailed.value = true
}

/*
|--------------------------------------------------------------------------
| Search
|--------------------------------------------------------------------------
*/

function performSearch() {
  const query = searchQuery.value.trim()

  router.push({
    name: 'search',
    query: query ? { q: query } : {},
  })
}

function clearSearch() {
  searchQuery.value = ''
  router.push({ name: 'search' })
}

onMounted(loadUser)
</script>

<style scoped>
.profile-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--icon-bg);
  color: var(--text-main);
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.profile-avatar img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

@media (max-width: 768px) {
  .header-inner {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    box-sizing: border-box;
  }

  .brand {
    flex: 0 0 auto;
    min-width: 0;
  }

  .header-search {
    flex: 1 1 0;
    width: 0;
    min-width: 0;
    max-width: none;
  }

  .header-search input {
    width: 100%;
    min-width: 0;
  }

  .header-actions {
    flex: 0 0 auto;
    min-width: 0;
    display: flex;
    align-items: center;
  }

  .profile-button {
    flex: 0 0 auto;
  }
}

@media (max-width: 390px) {
  .header-inner {
    gap: 6px;
  }

  .header-search {
    flex: 1 1 0;
    min-width: 0;
  }

  .header-search > svg {
    width: 17px;
    height: 17px;
    flex-shrink: 0;
  }

  .header-search input {
    min-width: 0;
    font-size: 12px;
  }

  .search-shortcut {
    display: none;
  }

  .profile-avatar {
    width: 34px;
    height: 34px;
    font-size: 12px;
  }
}

@media (max-width: 360px) {
  .header-inner {
    gap: 4px;
  }

  .header-search input {
    font-size: 11px;
  }

  .profile-avatar {
    width: 32px;
    height: 32px;
  }
}
</style>
