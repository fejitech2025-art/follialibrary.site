self.addEventListener('push', (event) => {
  let data = {}
  try {
    data = event.data ? event.data.json() : {}
  } catch {
    data = { body: event.data?.text() || 'You have a new notification.' }
  }

  const title = data.title || 'Follia Library'
  const options = {
    body: data.body || 'You have a new notification.',
    icon: '/pwa-192x192.png',
    badge: '/pwa-192x192.png',
    tag: data.id ? `follia-notification-${data.id}` : 'follia-notification',
    data: { url: data.url || '/notifications' },
  }

  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const target = new URL(event.notification.data?.url || '/notifications', self.location.origin).href

  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    for (const client of windows) {
      if (client.url.startsWith(self.location.origin) && 'focus' in client) {
        await client.navigate(target)
        return client.focus()
      }
    }
    return self.clients.openWindow(target)
  })())
})
