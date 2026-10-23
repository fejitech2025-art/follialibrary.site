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
        <RouterLink to="/messages" class="header-icon-link" aria-label="Messages">
          <MessageCircle :size="20" />
        </RouterLink>
        <RouterLink to="/notifications" class="header-icon-link notification-link" :aria-label="unreadCount ? `Notifications, ${unreadCount} unread` : 'Notifications'">
          <Bell :size="20" />
          <span v-if="unreadCount" class="header-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </RouterLink>
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Bell, MessageCircle } from 'lucide-vue-next'

import BrandLogo from './BrandLogo.vue'
import UserAvatar from './UserAvatar.vue'
import { useAuth } from '../composables/useAuth'
import { getMyProfile } from '../services/profileService'
import { getUnreadNotificationCount } from '../services/notificationService'
import { subscribeUserEvents } from '../services/userEvents'

const { user: authUser, initializeAuth } = useAuth()

const user = ref(null)
const profile = ref(null)
const unreadCount = ref(0)
let unreadTimer = null
let liveEvents = null

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
      await refreshUnreadCount()
      liveEvents?.unsubscribe()
      liveEvents = subscribeUserEvents((event) => {
        if (event.type === 'notification_count' || event.type === 'notification_new') {
          unreadCount.value = Number(event.count || 0)
        }
      })
    } else {
      profile.value = null
      unreadCount.value = 0
    }
  } catch (error) {
    console.error('Profile loading error:', error)
  }
}

onMounted(loadUser)
onMounted(() => {
  unreadTimer = window.setInterval(refreshUnreadCount, 45000)
  window.addEventListener('follia:notification-change', refreshUnreadCount)
  window.addEventListener('follia:notification-count', handleCountEvent)
})
onBeforeUnmount(() => {
  if (unreadTimer) window.clearInterval(unreadTimer)
  window.removeEventListener('follia:notification-change', refreshUnreadCount)
  window.removeEventListener('follia:notification-count', handleCountEvent)
  liveEvents?.unsubscribe()
})

async function refreshUnreadCount() {
  try { unreadCount.value = await getUnreadNotificationCount() } catch {}
}
function handleCountEvent(event) { unreadCount.value = Number(event.detail || 0) }
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
  gap: 9px;
}

.header-icon-link { position:relative; width:42px; height:42px; display:grid; place-items:center; border-radius:13px; color:var(--text-secondary); transition:background .18s,color .18s,transform .18s; }
.header-icon-link:hover { background:var(--hover-bg); color:var(--text-main); transform:translateY(-1px); }
.header-badge { position:absolute; top:1px; right:0; min-width:17px; height:17px; padding:0 4px; display:grid; place-items:center; border:2px solid var(--card-bg); border-radius:999px; background:var(--accent); color:#101010; font-size:9px; font-weight:850; line-height:1; animation:badge-pop .22s ease-out; }
@keyframes badge-pop { from { transform:scale(.7); opacity:.6 } to { transform:scale(1); opacity:1 } }

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
  .header-actions { gap:5px; }
  .header-icon-link { width:38px; height:38px; }
}
</style>
