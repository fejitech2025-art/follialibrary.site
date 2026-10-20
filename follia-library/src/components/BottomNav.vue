<template>
  <nav class="bottom-nav" aria-label="Main navigation">
    <RouterLink to="/" class="nav-item" :class="{ active: route.path === '/' }" aria-label="Home">
      <Home :size="21" stroke-width="1.8" />
      <span>Home</span>
    </RouterLink>
    <RouterLink to="/explore" class="nav-item" :class="{ active: route.path.startsWith('/explore') }" aria-label="Explore">
      <Compass :size="21" stroke-width="1.8" />
      <span>Explore</span>
    </RouterLink>
    <RouterLink to="/create" class="nav-create" aria-label="Create a post or upload a resource">
      <Plus :size="23" stroke-width="2.2" />
    </RouterLink>
    <RouterLink to="/clubs" class="nav-item" :class="{ active: route.path.startsWith('/clubs') || route.path.startsWith('/book-club') }" aria-label="Book Clubs">
      <UsersRound :size="21" stroke-width="1.8" />
      <span>Book Clubs</span>
    </RouterLink>
    <RouterLink to="/notifications" class="nav-item" :class="{ active: route.path.startsWith('/notifications') }" :aria-label="unreadCount ? `Notifications, ${unreadCount} unread` : 'Notifications'">
      <span class="notification-icon">
        <Bell :size="21" stroke-width="1.8" />
        <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
      </span>
      <span>Alerts</span>
    </RouterLink>
  </nav>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Bell, Compass, Home, Plus, UsersRound } from 'lucide-vue-next'
import { getUnreadNotificationCount } from '../services/notificationService'

const route = useRoute()
const unreadCount = ref(0)
let unreadTimer = null

async function refreshUnreadCount() {
  try {
    unreadCount.value = await getUnreadNotificationCount()
  } catch {
    unreadCount.value = 0
  }
}

onMounted(() => {
  refreshUnreadCount()
  unreadTimer = window.setInterval(refreshUnreadCount, 15000)
  window.addEventListener('follia:notification-change', refreshUnreadCount)
})

onBeforeUnmount(() => {
  if (unreadTimer) window.clearInterval(unreadTimer)
  window.removeEventListener('follia:notification-change', refreshUnreadCount)
})
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  z-index: 100;
  left: 50%;
  bottom: max(12px, env(safe-area-inset-bottom));
  transform: translateX(-50%);
  width: min(540px, calc(100% - 24px));
  min-height: 68px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 3px;
  padding: 7px 9px;
  border: 1px solid var(--border-color);
  border-radius: 21px;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  box-shadow: 0 10px 38px var(--shadow-color);
  backdrop-filter: blur(18px);
}
.nav-item {
  min-width: 0;
  flex: 1;
  min-height: 50px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  border-radius: 14px;
  color: var(--text-tertiary);
  font-size: 10px;
  font-weight: 650;
  transition: color .18s ease, background .18s ease;
}
.nav-item.active {
  color: var(--text-main);
  background: var(--hover-bg);
}
.nav-item:hover { color: var(--text-main); }
.notification-icon { position:relative; display:grid; place-items:center; }
.notification-badge { position:absolute; top:-7px; right:-11px; min-width:16px; height:16px; display:grid; place-items:center; padding:0 4px; border:2px solid var(--card-bg); border-radius:999px; background:#d83232; color:#fff; font-size:8px; font-weight:800; line-height:1; }
.nav-create {
  flex: 0 0 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: var(--primary-bg);
  color: var(--primary-text);
  box-shadow: 0 5px 14px var(--shadow-color);
  transition: transform .18s ease, box-shadow .18s ease;
}
.nav-create:hover { transform: translateY(-2px); box-shadow: 0 8px 19px var(--shadow-color); }
@media (min-width: 850px) {
  .bottom-nav { bottom: 22px; }
}
@media (max-width: 360px) {
  .bottom-nav { width: calc(100% - 16px); padding: 6px; gap: 1px; }
  .nav-create { flex-basis: 44px; height: 44px; }
  .nav-item { font-size: 9px; }
}
</style>
