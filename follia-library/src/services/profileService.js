import { api } from './api'
import { useAuth } from '../composables/useAuth'

export async function getCurrentUser() {
  const auth = useAuth()
  await auth.initializeAuth()
  return auth.user.value
}

export async function getCurrentUserId() {
  return (await getCurrentUser())?.id || null
}

export async function getProfile(userId) {
  if (!userId) return null
  return api('/api/users/' + userId + '/')
}

export async function getProfileByUsername(username) {
  const clean = username?.trim().replace(/^@/, '').toLowerCase()
  if (!clean) return null
  const results = await api('/api/users/?q=' + encodeURIComponent(clean))
  return results.find((profile) => profile.username?.toLowerCase() === clean) || null
}

export async function isUsernameTaken(username, excludeUserId = null) {
  const clean = username?.trim().replace(/^@/, '').toLowerCase()
  if (!clean) return false
  const results = await api('/api/users/?q=' + encodeURIComponent(clean))
  return results.some((profile) => profile.id !== excludeUserId && profile.username?.toLowerCase() === clean)
}

export async function getMyProfile() {
  return api('/api/me/profile/')
}

export async function createProfile(profile) {
  return updateMyProfile(profile)
}

export async function updateProfile(userId, profile) {
  const currentId = await getCurrentUserId()
  if (String(userId) !== String(currentId)) throw new Error('You can only edit your own profile.')
  return updateMyProfile(profile)
}

export async function updateMyProfile(profile) {
  return api('/api/me/profile/', { method: 'PATCH', body: profile })
}

export async function uploadAvatar(file) {
  if (!file) throw new Error('Please select an image.')
  if (!file.type.startsWith('image/')) throw new Error('Please select a valid image file.')
  if (file.size > 5 * 1024 * 1024) throw new Error('Image must be smaller than 5MB.')
  const form = new FormData()
  form.append('avatar', file)
  const result = await api('/api/me/profile/', { method: 'PATCH', body: form })
  return result.avatar_url || null
}
