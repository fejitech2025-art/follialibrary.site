import { api } from './api'

export function getConversations() {
  return api('/api/messages/conversations/')
}

export function startConversation(userId) {
  return api('/api/messages/conversations/', { method: 'POST', body: { user_id: userId } })
}

export function getConversationMessages(conversationId, before = null) {
  const query = before ? '?before=' + encodeURIComponent(before) : ''
  return api(`/api/messages/conversations/${conversationId}/messages/${query}`)
}

export function sendMessage(conversationId, { message_type = 'text', messageType = message_type, body = '', post_id = null, postId = post_id, file = null, duration_seconds = null, durationSeconds = duration_seconds, client_id = null, clientId = client_id || createClientId() }) {
  if (file) {
    const form = new FormData()
    form.append('client_id', clientId)
    form.append('message_type', messageType)
    form.append('duration_seconds', String(durationSeconds || 0))
    form.append('file', file, file.name || 'voice-note.webm')
    return api(`/api/messages/conversations/${conversationId}/messages/`, { method: 'POST', body: form })
  }
  return api(`/api/messages/conversations/${conversationId}/messages/`, {
    method: 'POST',
    body: { client_id: clientId, message_type: messageType, body, ...(postId ? { post_id: postId } : {}) },
  })
}

export function markConversationRead(conversationId) {
  return api(`/api/messages/conversations/${conversationId}/read/`, { method: 'POST' })
}

export function blockUser(userId) {
  return api('/api/messages/blocks/', { method: 'POST', body: { user_id: userId } })
}

export function unblockUser(userId) {
  return api(`/api/messages/blocks/${userId}/`, { method: 'DELETE' })
}

export function reportMessage(messageId, reason = 'other') {
  return api(`/api/messages/${messageId}/report/`, { method: 'POST', body: { reason } })
}

export function createClientId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  const bytes = new Uint8Array(16)
  if (globalThis.crypto?.getRandomValues) globalThis.crypto.getRandomValues(bytes)
  else for (let index = 0; index < bytes.length; index += 1) bytes[index] = Math.floor(Math.random() * 256)
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = [...bytes].map((value) => value.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`
}
