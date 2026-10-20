import { apiBaseUrl } from '../services/api'

const MEDIA_BASE_URL = apiBaseUrl()

export function resolveMediaUrl(url) {
  if (!url || typeof url !== 'string') return null

  const value = url.trim()
  if (!value) return null

  // Preserve complete CDN and presigned URLs byte-for-byte so their signatures
  // and query strings remain valid. Local blob/data URLs are upload previews.
  if (/^(https?:\/\/|blob:|data:)/i.test(value)) return value

  if (value.startsWith('//')) {
    return `${window.location.protocol}${value}`
  }

  try {
    return new URL(value, `${MEDIA_BASE_URL}/`).href
  } catch {
    return null
  }
}
