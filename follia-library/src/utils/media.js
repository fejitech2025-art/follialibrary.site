import { apiBaseUrl } from '../services/api'

const MEDIA_BASE_URL = apiBaseUrl()
  .replace(/\/+$/, '')
  .replace(/\/api$/i, '')

export function resolveMediaUrl(url) {
  if (!url || typeof url !== 'string') return null

  const value = url.trim()
  if (!value) return null

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
