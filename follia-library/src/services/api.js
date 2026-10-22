
const configuredApiBase =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin)

const API_BASE = configuredApiBase
  .replace(/\/+$/, '')
  .replace(/\/api$/i, '')

async function getCsrfToken() {
  const response = await fetch(`${API_BASE}/api/auth/csrf/`, {
    method: 'GET',
    credentials: 'include',
    cache: 'no-store',
    headers: {
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error('Unable to obtain a CSRF token. Please refresh and try again.')
  }

  const data = await response.json()

  if (!data.csrfToken) {
    throw new Error('Django did not return a CSRF token. Please refresh and try again.')
  }

  return data.csrfToken
}

export async function api(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  const headers = new Headers(options.headers || {})

  headers.set('Accept', 'application/json')

  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    const token = await getCsrfToken()
    headers.set('X-CSRFToken', token)
  }

  let body = options.body

  if (
    body &&
    !(body instanceof FormData) &&
    typeof body !== 'string'
  ) {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    method,
    headers,
    body,
    credentials: 'include',
  })

  if (response.status === 204) {
    return null
  }

  const raw = await response.text()
  const contentType = response.headers.get('content-type') || ''
  let data = null

  if (/\bjson\b/i.test(contentType)) {
    try {
      data = raw ? JSON.parse(raw) : null
    } catch {
      data = { detail: 'The server returned an invalid JSON response.' }
    }
  } else if (response.ok) {
    throw new Error('The server returned a non-JSON response for an API request.')
  } else {
    const isHtml = /\btext\/html\b/i.test(contentType) || /^\s*<!doctype\s+html|^\s*<html\b/i.test(raw)
    data = {
      detail: isHtml
        ? 'The API returned an HTML page instead of JSON. Check that VITE_API_BASE_URL points to the Django API server.'
        : raw || response.statusText,
    }
  }

  if (!response.ok) {
    const firstMessage = (value) => {
      if (typeof value === 'string') return value
      if (Array.isArray(value)) return value.map(firstMessage).find(Boolean)
      if (value && typeof value === 'object') return Object.values(value).map(firstMessage).find(Boolean)
      return ''
    }
    const fieldError = data && typeof data === 'object'
      ? Object.entries(data).map(([field, value]) => {
          const message = firstMessage(value)
          if (!message) return ''
          return field === 'non_field_errors' || field === 'detail'
            ? message
            : `${field.replaceAll('_', ' ')}: ${message}`
        }).find(Boolean)
      : ''
    const detail = data?.detail || fieldError

    throw new Error(detail || `Request failed (${response.status}).`)
  }

  return data
}

export function apiBaseUrl() {
  return API_BASE
}

export function getGoogleLoginUrl() {
  return `${API_BASE}/accounts/google/login/`
}

export async function submitGoogleLogin(next = '') {
  const token = await getCsrfToken()

  const form = document.createElement('form')
  form.method = 'POST'
  form.action = getGoogleLoginUrl()

  const field = document.createElement('input')
  field.type = 'hidden'
  field.name = 'csrfmiddlewaretoken'
  field.value = token

  form.appendChild(field)

  if (next) {
    const redirect = document.createElement('input')
    redirect.type = 'hidden'
    redirect.name = 'next'
    redirect.value = next
    form.appendChild(redirect)
  }

  document.body.appendChild(form)
  form.submit()
}

export function websocketUrl(path) {
  const url = new URL(path, API_BASE)

  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'

  return url.toString()
}
