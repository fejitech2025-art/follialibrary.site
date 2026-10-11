
const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
).replace(/\/$/, '')

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
  let data = null

  try {
    data = raw ? JSON.parse(raw) : null
  } catch {
    data = { detail: raw || response.statusText }
  }

  if (!response.ok) {
    const detail =
      data?.detail ||
      data?.email?.[0] ||
      data?.password?.[0]

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

export async function submitGoogleLogin() {
  const token = await getCsrfToken()

  const form = document.createElement('form')
  form.method = 'POST'
  form.action = getGoogleLoginUrl()

  const field = document.createElement('input')
  field.type = 'hidden'
  field.name = 'csrfmiddlewaretoken'
  field.value = token

  form.appendChild(field)
  document.body.appendChild(form)
  form.submit()
}

export function websocketUrl(path) {
  const url = new URL(path, API_BASE)

  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'

  return url.toString()
}