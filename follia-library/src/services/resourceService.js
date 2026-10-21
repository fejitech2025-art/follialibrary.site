import { api, apiBaseUrl } from './api'

export async function uploadResourceFile(file, resourceId) {
  const form = new FormData()
  form.append('file', file)
  const result = await api('/api/resources/' + resourceId + '/', { method: 'PATCH', body: form })
  return result.file_url
}

export async function uploadResourceCover(file, resourceId) {
  if (!file) return null
  const form = new FormData()
  form.append('cover', file)
  const result = await api('/api/resources/' + resourceId + '/', { method: 'PATCH', body: form })
  return result.cover_url
}

export async function createResource(resource) {
  return api('/api/resources/', { method: 'POST', body: resource })
}

export async function updateResource(resourceId, updates) {
  return api('/api/resources/' + resourceId + '/', { method: 'PATCH', body: updates })
}

export async function getPublishedResources(filters = {}) {
  const params = new URLSearchParams()
  if (filters.author) params.set('author', filters.author)
  if (filters.category) params.set('category', filters.category)
  const suffix = params.toString()
  return api('/api/resources/' + (suffix ? '?' + suffix : ''))
}

export async function getResource(resourceId) {
  return api('/api/resources/' + resourceId + '/')
}

export function getResourcePreviewUrl(resourceId) {
  return apiBaseUrl() + '/api/resources/' + resourceId + '/preview/'
}

export async function createResourceSignedUrl(fileUrl) {
  return fileUrl || ''
}

export async function deleteResource(resourceId) {
  await api('/api/resources/' + resourceId + '/', { method: 'DELETE' })
  return true
}
