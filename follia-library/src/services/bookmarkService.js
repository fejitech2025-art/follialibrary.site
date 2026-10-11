import { api } from './api'

export async function addBookmark(resourceId) {
  return api('/api/resources/' + resourceId + '/save/', { method: 'POST' })
}

export async function removeBookmark(resourceId) {
  return api('/api/resources/' + resourceId + '/save/', { method: 'DELETE' })
}

export async function isBookmarked(resourceId) {
  const resource = await api('/api/resources/' + resourceId + '/')
  return Boolean(resource.saved)
}

export async function toggleBookmark(resourceId, currentlyBookmarked) {
  const result = currentlyBookmarked ? await removeBookmark(resourceId) : await addBookmark(resourceId)
  return Boolean(result?.saved)
}

export async function getMyBookmarks() {
  const [resources, posts] = await Promise.all([api('/api/bookmarks/'), api('/api/bookmarks/posts/')])
  return [...resources, ...posts].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
}
