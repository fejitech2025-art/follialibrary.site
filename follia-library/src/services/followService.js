import { api } from './api'
import { getCurrentUserId } from './profileService'

export async function isFollowing(userId) {
  const profile = await api('/api/users/' + userId + '/')
  return Boolean(profile.is_following)
}

export async function followUser(userId) {
  return api('/api/users/' + userId + '/follow/', { method: 'POST' })
}

export async function unfollowUser(userId) {
  return api('/api/users/' + userId + '/follow/', { method: 'DELETE' })
}

export async function getFollowing(userId = null) {
  const id = userId || await getCurrentUserId()
  if (!id) return []
  return api('/api/users/' + id + '/following/')
}

export async function getFollowers(userId = null) {
  const id = userId || await getCurrentUserId()
  if (!id) return []
  return api('/api/users/' + id + '/followers/')
}

export async function getFollowCounts(userId = null) {
  const id = userId || await getCurrentUserId()
  if (!id) return { followingCount: 0, followerCount: 0 }
  const profile = await api('/api/users/' + id + '/')
  return { followingCount: profile.following_count || 0, followerCount: profile.follower_count || 0 }
}
