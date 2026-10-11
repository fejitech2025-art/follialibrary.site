import { api } from './api'

export async function getMyNotifications() {
  return api('/api/notifications/')
}

export async function getUnreadNotificationCount() {
  const rows = await api('/api/notifications/?unread=true')
  return rows.length
}

export async function markNotificationAsRead(notificationId) {
  return api('/api/notifications/' + notificationId + '/read/', { method: 'POST' })
}

export async function markAllNotificationsAsRead() {
  return api('/api/notifications/read-all/', { method: 'POST' })
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
    case 'comment': return actor + ' commented on your post.'
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
  if (type?.startsWith('book_club')) return 'Book Club'
  return 'Notification'
}
