import { api } from './api'

export async function getPublishers() {
  return api('/api/users/')
}

export async function getPublisher(userId) {
  return api('/api/users/' + userId + '/')
}

export async function getPublisherResources(userId) {
  return api('/api/resources/?author=' + encodeURIComponent(userId))
}

export async function getPublisherStats(userId) {
  const profile = await getPublisher(userId)
  return {
    resourceCount: profile.resource_count || 0,
    postCount: profile.post_count || 0,
    followingCount: profile.following_count || 0,
    followerCount: profile.follower_count || 0,
  }
}
