import { api } from './api'

export async function reportPublisher({ reportedUserId, reason, description }) {
  return api('/api/users/' + reportedUserId + '/report/', { method: 'POST', body: { reason, description } })
}

export async function reportPost(postId, reason = 'other', description = '') {
  return api('/api/posts/' + postId + '/report/', { method: 'POST', body: { reason, description } })
}
