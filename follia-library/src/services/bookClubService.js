import { api, websocketUrl } from './api'

export async function getBookClub(clubId) {
  return api('/api/clubs/' + clubId + '/')
}

export async function createBookClub({
  name,
  description = '',
  avatarUrl = null,
  avatarFile = null,
}) {
  if (avatarFile || avatarUrl instanceof File) {
    const form = new FormData()
    form.append('name', name)
    form.append('description', description)
    form.append('avatar', avatarFile || avatarUrl)

    return api('/api/clubs/', {
      method: 'POST',
      body: form,
    })
  }

  return api('/api/clubs/', {
    method: 'POST',
    body: { name, description },
  })
}

export async function updateBookClub(clubId, updates) {
  if (typeof clubId === 'object') {
    updates = clubId
    clubId = updates.bookClubId || updates.clubId
  }

  const file =
    updates.avatarFile ||
    (updates.avatar instanceof File ? updates.avatar : null)

  if (file) {
    const form = new FormData()

    for (const [key, value] of Object.entries(updates)) {
      if (key !== 'avatarFile' && key !== 'avatar') {
        form.append(key, value)
      }
    }

    form.append('avatar', file)

    return api('/api/clubs/' + clubId + '/', {
      method: 'PATCH',
      body: form,
    })
  }

  return api('/api/clubs/' + clubId + '/', {
    method: 'PATCH',
    body: updates,
  })
}

export async function isBookClubMember(clubId) {
  return api('/api/clubs/' + clubId + '/membership/')
}

export async function joinBookClub(clubId) {
  return api('/api/clubs/' + clubId + '/join/', {
    method: 'POST',
  })
}

export async function leaveBookClub(clubId) {
  return api('/api/clubs/' + clubId + '/join/', {
    method: 'DELETE',
  })
}

export async function getBookClubMessages(clubId) {
  return api('/api/clubs/' + clubId + '/messages/')
}

export async function sendBookClubMessage({
  clubId,
  bookClubId,
  content,
  replyTo = null,
  replyToId = null,
}) {
  const id = clubId || bookClubId

  return api('/api/clubs/' + id + '/messages/', {
    method: 'POST',
    body: {
      content,
      reply_to: replyTo || replyToId,
    },
  })
}

export async function deleteBookClubMessage(messageId, clubId) {
  return api(
    '/api/clubs/' + clubId + '/messages/' + messageId + '/',
    { method: 'DELETE' },
  )
}

export async function toggleBookClubMessagePin(
  messageIdOrPayload,
  pinned,
) {
  const payload =
    typeof messageIdOrPayload === 'object'
      ? messageIdOrPayload
      : { messageId: messageIdOrPayload, pinned }

  const clubId = payload.bookClubId || payload.clubId

  return api(
    '/api/clubs/' +
      clubId +
      '/messages/' +
      payload.messageId +
      '/pin/',
    {
      method: 'POST',
      body: {
        pinned: payload.isPinned ?? payload.pinned,
      },
    },
  )
}

export async function manageBookClubMember(payload) {
  const clubId = payload.clubId || payload.bookClubId
  const memberId = payload.memberId || payload.memberUserId
  const action = payload.action

  return api(
    '/api/clubs/' + clubId + '/members/' + memberId + '/',
    {
      method: action === 'remove' ? 'DELETE' : 'POST',
      body: { action },
    },
  )
}

/**
 * Subscribe to live events for a Book Club.
 *
 * Supported callbacks:
 *   onInsert(message)
 *   onUpdate(message)
 *   onDelete(message)
 *   onStatus(status)
 *   onError(error)
 *
 * A function can also be supplied as the second argument to receive
 * the original event payload, preserving the existing BookClubView API.
 */
export async function subscribeToBookClubMessages(
  clubId,
  callbacks = {},
) {
  let socket = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  let intentionallyClosed = false
  let connectionId = 0

  const isFunctionCallback = typeof callbacks === 'function'

  function notifyStatus(status) {
    if (!isFunctionCallback) {
      callbacks.onStatus?.(status)
    }
  }

  function notifyError(error) {
    if (!isFunctionCallback) {
      callbacks.onError?.(error)
    }
  }

  function deliver(payload) {
    if (isFunctionCallback) {
      callbacks(payload)
      return
    }

    if (payload?.type === 'insert') {
      callbacks.onInsert?.(payload.message)
    }

    if (payload?.type === 'update') {
      callbacks.onUpdate?.(payload.message)
    }

    if (payload?.type === 'delete') {
      callbacks.onDelete?.(payload.message)
    }
  }

  function clearReconnectTimer() {
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function connect() {
    if (intentionallyClosed) return

    clearReconnectTimer()

    const thisConnectionId = ++connectionId
    notifyStatus('connecting')

    try {
      socket = new WebSocket(
        websocketUrl('/ws/clubs/' + clubId + '/'),
      )
    } catch (error) {
      notifyError(error)
      scheduleReconnect()
      return
    }

    const currentSocket = socket

    currentSocket.addEventListener('open', () => {
      if (thisConnectionId !== connectionId) return

      reconnectAttempts = 0
      notifyStatus('connected')
    })

    currentSocket.addEventListener('message', (event) => {
      if (thisConnectionId !== connectionId) return

      try {
        const payload = JSON.parse(event.data)
        deliver(payload)
      } catch (error) {
        console.error(
          'Unable to process Book Club WebSocket message:',
          error,
        )
        notifyError(error)
      }
    })

    currentSocket.addEventListener('error', () => {
      if (thisConnectionId !== connectionId) return

      notifyStatus('error')
      notifyError(
        new Error('The Book Club live connection encountered an error.'),
      )
    })

    currentSocket.addEventListener('close', (event) => {
      if (thisConnectionId !== connectionId) return

      socket = null
      notifyStatus('disconnected')

      // 4403 is the consumer's explicit authentication/membership rejection.
      // Repeatedly reconnecting cannot fix that access-denied condition.
      if (event.code === 4403) {
        notifyStatus('unauthorized')
        return
      }

      if (!intentionallyClosed) {
        scheduleReconnect()
      }
    })
  }

  function scheduleReconnect() {
    if (intentionallyClosed || reconnectTimer !== null) return

    reconnectAttempts += 1

    // Exponential backoff, capped at 15 seconds.
    const delay = Math.min(
      1000 * 2 ** Math.min(reconnectAttempts - 1, 4),
      15000,
    )

    notifyStatus('reconnecting')

    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null
      connect()
    }, delay)
  }

  connect()

  return {
    get socket() {
      return socket
    },

    unsubscribe() {
      intentionallyClosed = true
      clearReconnectTimer()

      // Invalidate callbacks belonging to an old connection.
      connectionId += 1

      if (socket) {
        const currentSocket = socket
        socket = null

        if (currentSocket.readyState < WebSocket.CLOSING) {
          currentSocket.close(1000, 'Subscription ended')
        }
      }

      notifyStatus('disconnected')
    },
  }
}

export async function unsubscribeFromChannel(channel) {
  channel?.unsubscribe?.()
}

export async function uploadBookClubAvatar(file, clubId) {
  return updateBookClub(clubId, { avatarFile: file })
}

export async function getBookClubBooks(clubId) {
  return api('/api/clubs/' + clubId + '/resources/')
}

export async function searchBookClubResources(search = '') {
  const data = await api(
    '/api/search/?q=' + encodeURIComponent(search.trim()),
  )

  return data.resources || []
}

export async function addBookToBookClub(clubId, resourceId) {
  return api('/api/clubs/' + clubId + '/resources/', {
    method: 'POST',
    body: { resource_id: resourceId },
  })
}

export async function removeBookFromBookClub(clubId, resourceId) {
  return api(
    '/api/clubs/' + clubId + '/resources/' + resourceId + '/',
    { method: 'DELETE' },
  )
}

export async function getBookClubs(search = '') {
  return api(
    '/api/clubs/' +
      (search ? '?q=' + encodeURIComponent(search) : ''),
  )
}
