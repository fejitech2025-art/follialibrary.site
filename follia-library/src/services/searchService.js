import { api } from './api'

export async function searchResources(query) {
  if (!query?.trim()) return []
  const data = await api('/api/search/?q=' + encodeURIComponent(query.trim()))
  return data.resources || []
}

export async function searchPublishers(query) {
  if (!query?.trim()) return []
  const data = await api('/api/search/?q=' + encodeURIComponent(query.trim()))
  return data.users || []
}

export async function searchLibrary(query) {
  if (!query?.trim()) return { resources: [], publishers: [], users: [], posts: [] }
  const data = await api('/api/search/?q=' + encodeURIComponent(query.trim()))
  return { ...data, publishers: data.users || [] }
}
