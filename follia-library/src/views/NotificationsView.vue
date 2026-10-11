<template>
  <MainLayout>
    <div class="notifications-page">
      <!-- Header -->
      <header class="notifications-header">
        <div>
          <p class="eyebrow">YOUR ACTIVITY</p>

          <div class="notifications-title-row">
            <h1>Notifications</h1>

            <span v-if="unreadCount > 0" class="unread-count">
              {{ unreadCount }}
              {{ unreadCount === 1 ? 'unread' : 'unread' }}
            </span>
          </div>

          <p class="notifications-subtitle">
            Stay close to the people and ideas you follow.
          </p>
        </div>

        <button
          v-if="unreadCount > 0"
          type="button"
          class="mark-all-button"
          :disabled="markingAll"
          @click="handleMarkAllRead"
        >
          <LoaderCircle v-if="markingAll" :size="16" class="spin" />

          <CheckCheck v-else :size="16" />

          <span>
            {{ markingAll ? 'Marking...' : 'Mark all as read' }}
          </span>
        </button>
      </header>

      <!-- Loading -->
      <section v-if="loading" class="notification-state">
        <LoaderCircle :size="26" class="spin" />

        <p>Loading notifications...</p>
      </section>

      <!-- Error -->
      <section v-else-if="errorMessage" class="notification-state error-state">
        <div class="state-icon">
          <AlertCircle :size="24" />
        </div>

        <h2>Couldn't load notifications</h2>

        <p>{{ errorMessage }}</p>

        <button type="button" class="retry-button" @click="loadNotifications">Try again</button>
      </section>

      <!-- Empty -->
      <section v-else-if="notifications.length === 0" class="notification-empty">
        <div class="empty-icon">
          <Bell :size="28" />
        </div>

        <h2>You're all caught up</h2>

        <p>Follows, post conversations and Book Club activity will show up here.</p>

        <RouterLink to="/explore" class="empty-action">
          Explore Follia
          <ArrowUpRight :size="16" />
        </RouterLink>
      </section>

      <!-- Notifications -->
      <section v-else class="notification-list">
        <article
          v-for="notification in notifications"
          :key="notification.id"
          class="notification-card"
          :class="{ unread: !notification.read }"
          role="button"
          tabindex="0"
          @click="handleNotificationClick(notification)"
          @keydown.enter="handleNotificationClick(notification)"
          @keydown.space.prevent="handleNotificationClick(notification)"
        >
          <!-- Actor avatar -->
          <div class="notification-avatar">
            <img
              v-if="notification.actor?.avatar_url || notification.actor?.avatar"
              :src="resolveMediaUrl(notification.actor.avatar_url || notification.actor.avatar)"
              :alt="notification.actor.display_name || notification.actor.username || 'User'"
            />

            <span v-else>
              {{ getInitial(notification.actor) }}
            </span>
          </div>

          <!-- Content -->
          <div class="notification-content">
            <div class="notification-top">
              <span class="notification-type">
                {{ getNotificationTypeLabel(notification.type) }}
              </span>

              <span class="notification-time">
                {{ formatTime(notification.created_at) }}
              </span>
            </div>

            <p class="notification-message">
              {{ getNotificationMessage(notification) }}
            </p>

            <!-- Follow hint -->
            <p v-if="notification.type === 'follow'" class="notification-hint">
              View their profile
            </p>

            <!-- Book Club hint -->
            <p v-else-if="isBookClubNotification(notification)" class="notification-hint">
              Open Book Club
            </p>

            <!-- Resource hint -->
            <p
              v-else-if="
                (notification.type === 'like' || notification.type === 'comment') &&
                notification.resource_id
              "
              class="notification-hint"
            >
              View conversation
            </p>
          </div>

          <!-- Unread indicator -->
          <span
            v-if="!notification.read"
            class="unread-dot"
            aria-label="Unread notification"
          ></span>

          <!-- Read action -->
          <button
            v-if="!notification.read"
            type="button"
            class="notification-read-button"
            aria-label="Mark notification as read"
            title="Mark as read"
            @click.stop="handleMarkRead(notification)"
          >
            <Check :size="16" />
          </button>
        </article>
      </section>
    </div>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toastMessage" class="notification-toast">
        <CheckCircle :size="17" />

        <span>{{ toastMessage }}</span>
      </div>
    </Teleport>
  </MainLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { useRouter } from 'vue-router'

import {
  AlertCircle,
  ArrowUpRight,
  Bell,
  Check,
  CheckCheck,
  CheckCircle,
  LoaderCircle,
} from 'lucide-vue-next'

import MainLayout from '../layouts/MainLayout.vue'
import { resolveMediaUrl } from '../utils/media'

import {
  getMyNotifications,
  getNotificationMessage,
  getNotificationTypeLabel,
  markAllNotificationsAsRead,
  markNotificationAsRead,
  subscribeToMyNotifications,
} from '../services/notificationService'

const router = useRouter()

const notifications = ref([])

const loading = ref(true)

const errorMessage = ref('')

const markingAll = ref(false)

const toastMessage = ref('')

let notificationSubscription = null

const unreadCount = computed(() => {
  return notifications.value.filter((notification) => !notification.read).length
})

const bookClubNotificationTypes = [
  'book_club_join',
  'book_club_reply',
  'book_club_admin',
  'book_club_removed',
  'book_club_pin',
]

/*
|--------------------------------------------------------------------------
| Initial load
|--------------------------------------------------------------------------
*/

onMounted(async () => {
  await loadNotifications()

  await setupNotificationRealtime()
})

/*
|--------------------------------------------------------------------------
| Cleanup
|--------------------------------------------------------------------------
*/

onBeforeUnmount(() => {
  if (notificationSubscription) {
    notificationSubscription.unsubscribe()

    notificationSubscription = null
  }
})

/*
|--------------------------------------------------------------------------
| Load notifications
|--------------------------------------------------------------------------
*/

async function loadNotifications() {
  loading.value = true
  errorMessage.value = ''

  try {
    notifications.value = await getMyNotifications()
  } catch (error) {
    console.error('Notifications error:', error)

    errorMessage.value = error?.message || 'Unable to load your notifications.'
  } finally {
    loading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Realtime notifications
|--------------------------------------------------------------------------
*/

async function setupNotificationRealtime() {
  try {
    notificationSubscription = await subscribeToMyNotifications((event) => {
      /*
       * New notification
       */
      if (event.type === 'insert') {
        const notification = event.notification

        if (!notification) {
          return
        }

        /*
         * Prevent duplicates.
         */
        const alreadyExists = notifications.value.some((item) => item.id === notification.id)

        if (!alreadyExists) {
          notifications.value.unshift(notification)
        }

        return
      }

      /*
       * Existing notification changed.
       */
      if (event.type === 'update') {
        const index = notifications.value.findIndex((item) => item.id === event.notification?.id)

        if (index !== -1) {
          notifications.value[index] = {
            ...notifications.value[index],
            ...event.notification,
          }
        }

        return
      }

      /*
       * Notification deleted.
       */
      if (event.type === 'delete') {
        notifications.value = notifications.value.filter((item) => item.id !== event.notificationId)
      }
    })
  } catch (error) {
    console.error('Notifications realtime error:', error)
  }
}

/*
|--------------------------------------------------------------------------
| Book Club notification check
|--------------------------------------------------------------------------
*/

function isBookClubNotification(notification) {
  return bookClubNotificationTypes.includes(notification?.type)
}

/*
|--------------------------------------------------------------------------
| Mark one notification as read
|--------------------------------------------------------------------------
*/

async function handleMarkRead(notification) {
  if (!notification || notification.read) {
    return
  }

  try {
    await markNotificationAsRead(notification.id)

    notification.read = true
  } catch (error) {
    console.error('Mark notification read error:', error)

    showToast(error?.message || 'Unable to mark notification as read.')
  }
}

/*
|--------------------------------------------------------------------------
| Mark everything as read
|--------------------------------------------------------------------------
*/

async function handleMarkAllRead() {
  if (unreadCount.value === 0) {
    return
  }

  markingAll.value = true

  try {
    await markAllNotificationsAsRead()

    notifications.value = notifications.value.map((notification) => ({
      ...notification,
      read: true,
    }))

    showToast('All notifications marked as read.')
  } catch (error) {
    console.error('Mark all notifications error:', error)

    showToast(error?.message || 'Unable to mark notifications as read.')
  } finally {
    markingAll.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Notification click
|--------------------------------------------------------------------------
*/

async function handleNotificationClick(notification) {
  if (!notification) {
    return
  }

  /*
   * Mark it read first.
   */
  if (!notification.read) {
    try {
      await markNotificationAsRead(notification.id)

      notification.read = true
    } catch (error) {
      console.error('Notification read error:', error)
    }
  }

  /*
   * Book Club notifications
   */
  if (isBookClubNotification(notification) && notification.book_club_id) {
    router.push({
      name: 'book-club',
      params: {
        id: notification.book_club_id,
      },
    })

    return
  }

  /*
   * Follow notification
   */
  if (notification.type === 'follow' && notification.actor_id) {
    router.push({
      name: 'publisher-detail',
      params: {
        id: notification.actor_id,
      },
    })

    return
  }

  if ((notification.type === 'like' || notification.type === 'comment') && notification.post_id) {
    router.push({ name: 'post-detail', params: { id: notification.post_id } })
    return
  }

  if ((notification.type === 'like' || notification.type === 'comment') && notification.resource_id) {
    router.push({ name: 'resource-detail', params: { id: notification.resource_id } })
    return
  }
}

/*
|--------------------------------------------------------------------------
| Avatar initials
|--------------------------------------------------------------------------
*/

function getInitial(actor) {
  const name = actor?.display_name || actor?.username || 'U'

  return name.trim().charAt(0).toUpperCase()
}

/*
|--------------------------------------------------------------------------
| Time formatting
|--------------------------------------------------------------------------
*/

function formatTime(dateString) {
  if (!dateString) {
    return ''
  }

  const date = new Date(dateString)

  const now = new Date()

  const difference = now.getTime() - date.getTime()

  const seconds = Math.floor(difference / 1000)

  if (seconds < 60) {
    return 'Just now'
  }

  const minutes = Math.floor(seconds / 60)

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
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  })
}

/*
|--------------------------------------------------------------------------
| Toast
|--------------------------------------------------------------------------
*/

function showToast(message) {
  toastMessage.value = message

  window.setTimeout(() => {
    toastMessage.value = ''
  }, 3000)
}
</script>

<style scoped>
.notifications-page {
  width: min(980px, 100%);
  margin: 0 auto;
  padding: 32px 24px 110px;
}

/* =========================
   HEADER
========================= */

.notifications-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 30px;
}

.notifications-header .eyebrow {
  margin: 0 0 8px;
}

.notifications-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.notifications-title-row h1 {
  margin: 0;
  color: var(--text-main);
  font-size: clamp(32px, 5vw, 46px);
  line-height: 1.05;
  letter-spacing: -0.04em;
}

.notifications-subtitle {
  max-width: 620px;
  margin: 12px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.65;
}

.unread-count {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--card-bg);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
}

.mark-all-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid var(--border-color);
  border-radius: 11px;
  background: var(--card-bg);
  color: var(--text-main);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease;
}

.mark-all-button:hover:not(:disabled) {
  background: var(--surface-soft);
  border-color: var(--border-color);
}

.mark-all-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

/* =========================
   LIST
========================= */

.notification-list {
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--card-bg);
}

.notification-card {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 18px 20px;
  border: 0;
  border-bottom: 1px solid var(--border-color);
  background: var(--card-bg);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    background 0.2s ease,
    transform 0.2s ease;
}

.notification-card:last-child {
  border-bottom: 0;
}

.notification-card:hover {
  background: var(--surface-soft);
}

.notification-card:focus-visible {
  outline: 2px solid var(--primary-bg);
  outline-offset: -2px;
}

.notification-card.unread {
  background: var(--surface-soft);
}

.notification-card.unread:hover {
  background: var(--surface-soft);
}

/* =========================
   AVATAR
========================= */

.notification-avatar {
  width: 46px;
  height: 46px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 14px;
  background: var(--surface-soft);
  color: var(--text-main);
  font-size: 14px;
  font-weight: 700;
}

.notification-avatar img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

/* =========================
   CONTENT
========================= */

.notification-content {
  min-width: 0;
  flex: 1;
}

.notification-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 5px;
}

.notification-type {
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.notification-time {
  flex-shrink: 0;
  color: var(--text-secondary);
  font-size: 11px;
}

.notification-message {
  margin: 0;
  color: var(--text-main);
  font-size: 14px;
  line-height: 1.5;
}

.notification-hint {
  margin: 5px 0 0;
  color: var(--text-secondary);
  font-size: 11px;
}

/* =========================
   UNREAD
========================= */

.unread-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--primary-bg);
}

.notification-read-button {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border: 1px solid var(--border-color);
  border-radius: 9px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    border-color 0.2s ease;
}

.notification-read-button:hover {
  background: var(--surface-soft);
  border-color: var(--border-color);
  color: var(--text-main);
}

/* =========================
   STATES
========================= */

.notification-state {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 50px 24px;
  border: 1px dashed var(--border-color);
  border-radius: 20px;
  color: var(--text-secondary);
  text-align: center;
}

.notification-state p {
  margin: 0;
  font-size: 13px;
}

.error-state {
  color: var(--text-secondary);
}

.state-icon {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  margin-bottom: 4px;
  border-radius: 16px;
  background: var(--surface-soft);
  color: var(--text-main);
}

.notification-state h2 {
  margin: 0;
  color: var(--text-main);
  font-size: 19px;
}

.retry-button {
  margin-top: 8px;
  padding: 10px 15px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--card-bg);
  color: var(--text-main);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

/* =========================
   EMPTY
========================= */

.notification-empty {
  min-height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  border: 1px dashed var(--border-color);
  border-radius: 20px;
  background: var(--card-bg);
  text-align: center;
}

.empty-icon {
  width: 68px;
  height: 68px;
  display: grid;
  place-items: center;
  margin-bottom: 20px;
  border-radius: 20px;
  background: var(--surface-soft);
  color: var(--text-main);
}

.notification-empty h2 {
  margin: 0 0 8px;
  color: var(--text-main);
  font-size: 21px;
  letter-spacing: -0.02em;
}

.notification-empty p {
  max-width: 470px;
  margin: 0 0 24px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.empty-action {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 10px;
  background: var(--primary-bg);
  color: var(--primary-text);
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

/* =========================
   TOAST
========================= */

.notification-toast {
  position: fixed;
  right: 22px;
  bottom: 22px;
  z-index: 1000;

  display: flex;
  align-items: center;
  gap: 9px;

  padding: 12px 15px;

  border: 1px solid var(--border-color);
  border-radius: 12px;

  background: var(--card-bg);
  color: var(--text-main);

  box-shadow: 0 16px 40px var(--shadow-color);

  font-size: 12px;
  font-weight: 600;
}

/* =========================
   SPINNER
========================= */

.spin {
  animation: notification-spin 0.9s linear infinite;
}

@keyframes notification-spin {
  to {
    transform: rotate(360deg);
  }
}

/* =========================
   MOBILE
========================= */

@media (max-width: 700px) {
  .notifications-page {
    padding: 24px 16px 100px;
  }

  .notifications-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 18px;
  }

  .notifications-header h1 {
    font-size: 36px;
  }

  .mark-all-button {
    width: 100%;
  }

  .notification-card {
    align-items: flex-start;
    gap: 11px;
    padding: 15px;
  }

  .notification-avatar {
    width: 42px;
    height: 42px;
    border-radius: 13px;
  }

  .notification-top {
    align-items: flex-start;
  }

  .notification-type {
    display: none;
  }

  .notification-message {
    font-size: 13px;
  }

  .notification-read-button {
    width: 32px;
    height: 32px;
  }

  .unread-dot {
    width: 7px;
    height: 7px;
  }
}

@media (max-width: 480px) {
  .notifications-page {
    padding-left: 12px;
    padding-right: 12px;
  }

  .notifications-title-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 9px;
  }

  .notifications-header h1 {
    font-size: 32px;
  }

  .notification-card {
    padding: 13px;
  }

  .notification-avatar {
    width: 38px;
    height: 38px;
    min-width: 38px;
    font-size: 12px;
  }

  .notification-message {
    font-size: 12px;
  }

  .notification-time {
    font-size: 10px;
  }

  .notification-read-button {
    width: 30px;
    height: 30px;
  }

  .notification-toast {
    right: 12px;
    bottom: 85px;
    left: 12px;
    justify-content: center;
  }
}
</style>
