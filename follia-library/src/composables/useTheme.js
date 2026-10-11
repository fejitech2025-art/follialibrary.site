import { ref } from 'vue'

const theme = ref(localStorage.getItem('follia-theme') || 'light')
let systemPreferenceListenerRegistered = false

function applyTheme(value) {
  theme.value = value
  localStorage.setItem('follia-theme', value)

  const root = document.documentElement

  if (value === 'dark') {
    root.setAttribute('data-theme', 'dark')
  } else if (value === 'light') {
    root.setAttribute('data-theme', 'light')
  } else {
    const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false

    root.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
  }
}

function setTheme(value) {
  applyTheme(value)
}

export function initializeTheme() {
  const savedTheme = localStorage.getItem('follia-theme') || 'light'
  applyTheme(savedTheme)

  if (!systemPreferenceListenerRegistered && typeof window.matchMedia === 'function') {
    const systemPreference = window.matchMedia('(prefers-color-scheme: dark)')
    systemPreference.addEventListener?.('change', () => {
      if (theme.value === 'system') applyTheme('system')
    })
    systemPreferenceListenerRegistered = true
  }
}

export function useTheme() {
  return {
    theme,
    setTheme,
  }
}
