import { api } from './api'

export async function likeResource(resourceId) {
  return api('/api/resources/' + resourceId + '/like/', { method: 'POST' })
}

export async function unlikeResource(resourceId) {
  return api('/api/resources/' + resourceId + '/like/', { method: 'DELETE' })
}

export async function isResourceLiked(resourceId) {
  const resource = await api('/api/resources/' + resourceId + '/')
  return Boolean(resource.liked)
}

export async function getResourceLikeCount(resourceId) {
  const resource = await api('/api/resources/' + resourceId + '/')
  return resource.like_count || 0
}

export async function toggleResourceLike(resourceId, currentlyLiked) {
  return currentlyLiked ? unlikeResource(resourceId) : likeResource(resourceId)
}
