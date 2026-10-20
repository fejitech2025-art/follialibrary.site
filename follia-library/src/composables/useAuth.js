import { ref } from 'vue'
import { api } from '../services/api'

const user = ref(null)
const loading = ref(true)
let initialized = false
let initializePromise = null

export function useAuth() {
  async function initializeAuth() {
    if (initializePromise) return initializePromise
    if (initialized) return user.value

    initializePromise = (async () => {
      loading.value = true
      try {
        const result = await api('/api/auth/me/')
        user.value = result?.user || null
        initialized = true
        return user.value
      } catch (error) {
        user.value = null
        initialized = true
        return null
      } finally {
        loading.value = false
        initializePromise = null
      }
    })()
    return initializePromise
  }

  async function signOut() {
    await api('/api/auth/logout/', { method: 'POST' })
    user.value = null
    initialized = true
  }

  return { user, loading, initializeAuth, signOut }
}
