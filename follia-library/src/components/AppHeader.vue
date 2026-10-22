```vue
<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- Brand: Always at the top left -->
      <RouterLink to="/" class="brand" aria-label="Follia Library home">
        <BrandLogo />

        <div class="brand-text">
          <span class="brand-name">Follia</span>
          <span class="brand-subtitle">library</span>
        </div>
      </RouterLink>

      <!-- Profile: Always at the top right -->
      <div class="header-actions">
        <RouterLink to="/account" class="profile-button">
          <div class="profile-avatar">
            <UserAvatar
              :src="rawAvatarUrl"
              alt="Profile"
              :icon-size="20"
            />
          </div>

          <span class="profile-label">Profile</span>
        </RouterLink>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import BrandLogo from './BrandLogo.vue'
import UserAvatar from './UserAvatar.vue'
import { useAuth } from '../composables/useAuth'
import { getMyProfile } from '../services/profileService'

const { user: authUser, initializeAuth } = useAuth()

const user = ref(null)
const profile = ref(null)

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

onMounted(loadUser)
</script>

<style scoped>
/* Header */
.app-header {
  width: 100%;
  box-sizing: border-box;
}

.header-inner {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;

  display: flex;
  align-items: center;
  justify-content: space-between;

  gap: 16px;
  padding: 12px 24px;
}

/* Brand: top left */
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;

  flex: 0 1 auto;
  min-width: 0;

  color: inherit;
  text-decoration: none;
}

.brand-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.brand-name {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.1;
}

.brand-subtitle {
  font-size: 12px;
  line-height: 1.3;
  color: var(--text-muted, #777);
}

/* Profile: top right */
.header-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;

  flex: 0 0 auto;
  margin-left: auto;
}

.profile-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;

  flex: 0 0 auto;
  color: inherit;
  text-decoration: none;
  border-radius: 12px;
  padding: 2px 4px;

  transition: opacity 0.2s ease;
}

.profile-button:hover {
  opacity: 0.8;
}

.profile-button:focus-visible {
  outline: 2px solid var(--text-main, #333);
  outline-offset: 4px;
}

/* Avatar */
.profile-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;

  display: flex;
  align-items: center;
  justify-content: center;

  background: var(--icon-bg, #f1f1ef);
  color: var(--text-main, #333);
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

/* Label below avatar */
.profile-label {
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
  white-space: nowrap;
  color: var(--text-main, #333);
}

/* Tablets and mobile */
@media (max-width: 768px) {
  .header-inner {
    padding: 10px 16px;
    gap: 12px;
  }

  .brand {
    gap: 8px;
  }

  .brand-name {
    font-size: 17px;
  }

  .brand-subtitle {
    font-size: 11px;
  }

  .profile-avatar {
    width: 38px;
    height: 38px;
  }
}

/* Small phones */
@media (max-width: 390px) {
  .header-inner {
    padding: 10px 12px;
    gap: 8px;
  }

  .brand {
    gap: 6px;
  }

  .brand-name {
    font-size: 16px;
  }

  .profile-avatar {
    width: 34px;
    height: 34px;
  }

  .profile-label {
    font-size: 10px;
  }
}
</style>
