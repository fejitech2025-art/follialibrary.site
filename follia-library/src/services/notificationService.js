import { api } from './api'

export async function getMyNotifications() {
  return api('/api/notifications/')
}

export async function getUnreadNotificationCount() {
  const result = await api('/api/notifications/unread-count/')
  return Number(result?.count || 0)
}

export async function markNotificationAsRead(notificationId) {
  const result = await api('/api/notifications/' + notificationId + '/read/', { method: 'POST' })
  window.dispatchEvent(new Event('follia:notification-change'))
  return result
}

export async function markAllNotificationsAsRead() {
  const result = await api('/api/notifications/read-all/', { method: 'POST' })
  window.dispatchEvent(new Event('follia:notification-change'))
  return result
}

export async function getPushStatus() {
  const notificationSupported = 'Notification' in window
  const permission = notificationSupported ? Notification.permission : 'unsupported'
  const notificationsEnabled = permission === 'granted' && !browserNotificationsOptedOut()
  const baseStatus = {
    available: false,
    subscribed: false,
    permission,
    notificationSupported,
    notificationsEnabled,
    reason: '',
  }

  if (!('serviceWorker' in navigator) || !('PushManager' in window) || !window.isSecureContext) {
    return { ...baseStatus, reason: notificationSupported ? 'push-unsupported' : 'unsupported' }
  }

  const registration = await navigator.serviceWorker.getRegistration()
  if (!registration) {
    return { ...baseStatus, reason: 'push-unsupported' }
  }

  const [server, config] = await Promise.all([
    api('/api/push/subscriptions/'),
    api('/api/push/public-key/'),
  ])
  const subscription = await registration.pushManager.getSubscription()
  return {
    available: Boolean(config?.enabled && config?.public_key),
    reason: config?.enabled ? '' : 'unconfigured',
    subscribed: Boolean(server?.subscribed && subscription),
    permission,
    notificationSupported,
    notificationsEnabled,
    registration,
    publicKey: config?.public_key || '',
    subscription,
  }
}

export async function enablePushNotifications() {
  if (!('Notification' in window)) throw new Error('This browser does not support browser notifications.')
  let permission = Notification.permission
  if (permission === 'default') permission = await Notification.requestPermission()
  if (permission !== 'granted') {
    throw new Error(permission === 'denied'
      ? 'Notifications are blocked in browser settings. You can enable them there later.'
      : 'Notification permission was not granted.')
  }

  try { localStorage.removeItem('follia-browser-notifications-disabled') } catch {}
  const status = await getPushStatus()
  if (!status.available) {
    window.dispatchEvent(new Event('follia:notification-change'))
    return { subscribed: false, foregroundOnly: true }
  }

  const subscription = status.subscription || await status.registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: decodeVapidKey(status.publicKey),
  })
  await api('/api/push/subscriptions/', {
    method: 'POST',
    body: subscription.toJSON(),
  })
  window.dispatchEvent(new Event('follia:notification-change'))
  return { subscribed: true, foregroundOnly: false }
}

export async function disablePushNotifications() {
  try { localStorage.setItem('follia-browser-notifications-disabled', '1') } catch {}
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    window.dispatchEvent(new Event('follia:notification-change'))
    return
  }
  const registration = await navigator.serviceWorker.getRegistration()
  if (!registration) {
    window.dispatchEvent(new Event('follia:notification-change'))
    return
  }
  const subscription = await registration.pushManager.getSubscription()
  if (subscription) {
    await api('/api/push/subscriptions/', {
      method: 'DELETE',
      body: { endpoint: subscription.endpoint },
    })
    await subscription.unsubscribe()
  }
  window.dispatchEvent(new Event('follia:notification-change'))
}

function browserNotificationsOptedOut() {
  try {
    return localStorage.getItem('follia-browser-notifications-disabled') === '1'
  } catch {
    return false
  }
}

function decodeVapidKey(value) {
  const padding = '='.repeat((4 - value.length % 4) % 4)
  const base64 = (value + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = window.atob(base64)
  return Uint8Array.from(raw, (character) => character.charCodeAt(0))
}

export async function createBookClubNotification() {
  return null
}

export async function subscribeToMyNotifications(callback) {
  let previous = new Map()
  let stopped = false

  async function refresh() {
    if (stopped) return
    try {
      const rows = await getMyNotifications()
      const next = new Map(rows.map((notification) => [notification.id, notification]))
      for (const [id, notification] of next) {
        if (!previous.has(id)) callback({ type: 'insert', notification })
        else if (previous.get(id).read !== notification.read) callback({ type: 'update', notification })
      }
      for (const id of previous.keys()) {
        if (!next.has(id)) callback({ type: 'delete', notificationId: id })
      }
      previous = next
      window.dispatchEvent(new Event('follia:notification-change'))
    } catch (error) {
      console.error('Notification refresh error:', error)
    }
  }

  await refresh()
  const timer = window.setInterval(refresh, 20000)
  return { unsubscribe() { stopped = true; window.clearInterval(timer) } }
}

export function getNotificationMessage(notification) {
  const actor = notification?.actor?.display_name || notification?.actor?.username || 'Someone'
  switch (notification?.type) {
    case 'follow': return actor + ' followed you.'
    case 'like': return actor + ' liked your post.'
    case 'comment': return actor + ' commented on your content.'
    case 'comment_reply': return actor + ' replied to your comment.'
    case 'comment_like': return actor + ' liked your comment on ' + (notification?.resource_id ? 'a resource.' : 'a post.')
    case 'book_club_join': return actor + ' joined your Book Club.'
    case 'book_club_reply': return actor + ' replied to your message.'
    case 'book_club_admin': return actor + ' updated your Book Club role.'
    default: return 'You have a new notification.'
  }
}

export function getNotificationTypeLabel(type) {
  if (type === 'follow') return 'Follow'
  if (type === 'like') return 'Like'
  if (type === 'comment') return 'Comment'
  if (type === 'comment_reply') return 'Reply'
  if (type === 'comment_like') return 'Comment like'
  if (type?.startsWith('book_club')) return 'Book Club'
  return 'Notification'
}
