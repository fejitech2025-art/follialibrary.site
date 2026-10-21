import { api } from './api'

export async function reportPublisher({ reportedUserId, reason, description }) {
  return api('/api/users/' + reportedUserId + '/report/', { method: 'POST', body: { reason, description } })
}

export async function reportPost(postId, reason = 'other', description = '') {
  return api('/api/posts/' + postId + '/report/', { method: 'POST', body: { reason, description } })
}

export async function reportPostComment(postId, commentId, reason = 'other', description = '') {
  return api(`/api/posts/${postId}/comments/${commentId}/report/`, { method: 'POST', body: { reason, description } })
}

export async function reportResource(resourceId, reason = 'other', description = '') {
  return api(`/api/resources/${resourceId}/report/`, { method: 'POST', body: { reason, description } })
}

export async function reportResourceComment(resourceId, commentId, reason = 'other', description = '') {
  return api(`/api/resources/${resourceId}/comments/${commentId}/report/`, { method: 'POST', body: { reason, description } })
}
