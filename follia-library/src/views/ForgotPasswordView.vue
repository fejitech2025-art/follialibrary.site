<template>
  <AuthLayout>
    <div class="auth-mobile-brand">
      <BrandLogo />
      <span>Follia Library</span>
    </div>

    <div class="auth-heading">
      <p class="auth-kicker">ACCOUNT RECOVERY</p>
      <h1>Forgot password?</h1>
      <p>We'll send you a link to create a new password.</p>
    </div>

    <form class="auth-form" @submit.prevent="sendReset">
      <div class="auth-field">
        <label for="email">Email</label>

        <input
          id="email"
          v-model.trim="email"
          type="email"
          autocomplete="email"
          placeholder="you@example.com"
          required
        />
      </div>

      <div v-if="message" class="auth-success">
        {{ message }}
      </div>

      <div v-if="errorMessage" class="auth-error">
        {{ errorMessage }}
      </div>

      <button class="auth-submit" type="submit" :disabled="loading">
        {{ loading ? 'Sending...' : 'Send reset link' }}
      </button>
    </form>

    <p class="auth-switch">
      Remember your password?
      <RouterLink to="/login">Sign in</RouterLink>
    </p>
  </AuthLayout>
</template>

<script setup>
import { ref } from 'vue'
import BrandLogo from '../components/BrandLogo.vue'
import AuthLayout from '../components/auth/AuthLayout.vue'
import { api } from '../services/api'

const email = ref('')
const loading = ref(false)
const message = ref('')
const errorMessage = ref('')

async function sendReset() {
  loading.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    await api('/api/auth/password-reset/', { method: 'POST', body: { email: email.value, frontend_url: window.location.origin } })
    message.value = 'If an account exists for that email, a password reset link has been sent.'
  } catch (error) {
    errorMessage.value = error.message || 'Unable to send a password reset email.'
  } finally {
    loading.value = false
  }
}
</script>
