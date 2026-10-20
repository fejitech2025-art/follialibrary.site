import { api } from './api'

export async function getFeed(feed = 'for-you') {
  return api('/api/feed/?tab=' + encodeURIComponent(feed))
}

export async function getPosts(params = {}) {
  const query = params.author ? '?author=' + encodeURIComponent(params.author) : ''
  return api('/api/posts/' + query)
}

export async function getPost(postId) {
  return api('/api/posts/' + postId + '/')
}

export async function createPost({ body = '', media = null, media_type = '' }) {
  if (media) {
    const form = new FormData()
    form.append('body', body)
    form.append('media', media)
    form.append('media_type', media_type || (media.type.startsWith('video/') ? 'video' : 'image'))
    return api('/api/posts/', { method: 'POST', body: form })
  }
  return api('/api/posts/', { method: 'POST', body: { body } })
}

export async function deletePost(postId) {
  return api('/api/posts/' + postId + '/', { method: 'DELETE' })
}

export async function updatePost(postId, body) {
  return api('/api/posts/' + postId + '/', { method: 'PATCH', body: { body } })
}

export async function togglePostLike(postId, liked) {
  return api('/api/posts/' + postId + '/like/', { method: liked ? 'DELETE' : 'POST' })
}

export async function togglePostSave(postId, saved) {
  return api('/api/posts/' + postId + '/save/', { method: saved ? 'DELETE' : 'POST' })
}

export async function getPostComments(postId) {
  return api('/api/posts/' + postId + '/comments/')
}

export async function addPostComment(postId, content, parentId = null) {
  if (!content?.trim()) throw new Error('Comment cannot be empty.')
  return api('/api/posts/' + postId + '/comments/', { method: 'POST', body: { content: content.trim(), parent_id: parentId } })
}
