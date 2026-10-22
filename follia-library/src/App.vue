<template>
  <RouterView />
</template>

<script setup>
import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useAuth } from './composables/useAuth'
import {
  getMyNotifications,
  getNotificationMessage,
  subscribeToMyNotifications,
} from './services/notificationService'

const { user, initializeAuth } = useAuth()
let notificationSubscription = null
let notificationWatcherId = 0
let seenNotificationIds = new Set()

watch(() => user.value?.id, (userId) => {
  stopNotificationWatcher()
  if (userId) startNotificationWatcher()
}, { immediate: true })

onMounted(() => initializeAuth())
onBeforeUnmount(stopNotificationWatcher)

function stopNotificationWatcher() {
  notificationWatcherId += 1
  notificationSubscription?.unsubscribe()
  notificationSubscription = null
  seenNotificationIds = new Set()
}

async function startNotificationWatcher() {
  const watcherId = notificationWatcherId
  try {
    const currentNotifications = await getMyNotifications()
    if (watcherId !== notificationWatcherId) return
    seenNotificationIds = new Set(currentNotifications.map((item) => item.id))
    const subscription = await subscribeToMyNotifications((event) => {
      if (watcherId !== notificationWatcherId || event.type !== 'insert') return
      const notification = event.notification
      if (!notification?.id || seenNotificationIds.has(notification.id)) return
      seenNotificationIds.add(notification.id)
      showBrowserNotification(notification)
    })
    if (watcherId === notificationWatcherId) notificationSubscription = subscription
    else subscription.unsubscribe()
  } catch {
    // The in-app notification page still reports API errors when the user opens it.
  }
}

function showBrowserNotification(notification) {
  if (
    !notification || notification.read || document.visibilityState !== 'visible' ||
    !('Notification' in window) || Notification.permission !== 'granted'
  ) return

  try {
    if (localStorage.getItem('follia-browser-notifications-disabled') === '1') return
  } catch {}

  const targetUrl = getNotificationTargetUrl(notification)
  try {
    const alert = new Notification('Follia Library', {
      body: getNotificationMessage(notification),
      icon: '/pwa-192x192.png',
      tag: `follia-notification-${notification.id}`,
      renotify: false,
      data: { url: targetUrl },
    })
    alert.onclick = () => {
      window.focus()
      window.location.assign(targetUrl)
      alert.close()
    }
  } catch {
    // Some browsers expose notifications only through a service worker.
    navigator.serviceWorker?.ready
      .then((registration) => registration.showNotification('Follia Library', {
        body: getNotificationMessage(notification),
        icon: '/pwa-192x192.png',
        tag: `follia-notification-${notification.id}`,
        data: { url: targetUrl },
      }))
      .catch(() => {})
  }
}

function getNotificationTargetUrl(notification) {
  if (notification.post_id && notification.comment_id) {
    return `/post/${notification.post_id}?comment=${notification.comment_id}`
  }
  if (notification.resource_id && notification.comment_id) {
    return `/resource/${notification.resource_id}?comment=${notification.comment_id}`
  }
  if (notification.post_id) return `/post/${notification.post_id}`
  if (notification.resource_id) return `/resource/${notification.resource_id}`
  if (notification.book_club_id) return `/book-club/${notification.book_club_id}`
  if (notification.actor_id) return `/profile/${notification.actor_id}`
  return '/notifications'
}
</script>
