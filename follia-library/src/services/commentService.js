import { api } from './api'

export async function getResourceComments(resourceId) {
  return resourceId ? api('/api/resources/' + resourceId + '/comments/') : []
}

export async function addResourceComment(resourceId, content) {
  if (!content?.trim()) throw new Error('Comment cannot be empty.')
  return api('/api/resources/' + resourceId + '/comments/', { method: 'POST', body: { content: content.trim() } })
}

export async function deleteResourceComment(commentId, resourceId) {
  return api('/api/resources/' + resourceId + '/comments/' + commentId + '/', { method: 'DELETE' })
}

export async function updateResourceComment(commentId, content, resourceId) {
  return api('/api/resources/' + resourceId + '/comments/' + commentId + '/', { method: 'PATCH', body: { content } })
}

export async function getResourceCommentCount(resourceId) {
  const resource = await api('/api/resources/' + resourceId + '/')
  return resource.comment_count || 0
}
