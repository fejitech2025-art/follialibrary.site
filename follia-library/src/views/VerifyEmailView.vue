<template>
  <AuthLayout>
    <div class="auth-mobile-brand">
      <BrandLogo />
      <span>Follia Library</span>
    </div>

    <div class="verify-card">
      <div class="verify-icon">@</div>

      <p class="auth-kicker">CHECK YOUR INBOX</p>

      <h1>Verify your email</h1>

      <p>
        We sent a verification link to
        <strong>{{ email || 'your email address' }}</strong
        >.
      </p>

      <p>Click the link in that email to activate your Follia Library account.</p>

      <div v-if="message" class="auth-success">
        {{ message }}
      </div>

      <div v-if="errorMessage" class="auth-error">
        {{ errorMessage }}
      </div>

      <button class="auth-submit" :disabled="loading" @click="resendEmail">
        {{ loading ? 'Sending...' : 'Resend verification email' }}
      </button>

      <RouterLink class="back-login" to="/login"> Back to sign in </RouterLink>
    </div>
  </AuthLayout>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import BrandLogo from '../components/BrandLogo.vue'
import AuthLayout from '../components/auth/AuthLayout.vue'
import { api } from '../services/api'

const route = useRoute()
const email = computed(() => route.query.email || '')
const loading = ref(false)
const message = ref('')
const errorMessage = ref('')

async function resendEmail() {
  if (!email.value) return
  loading.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    await api('/api/auth/resend-verification/', { method: 'POST', body: { email: email.value } })
    message.value = 'Verification email sent. Check your inbox.'
  } catch (error) {
    errorMessage.value = error.message || 'Unable to resend the verification email.'
  } finally {
    loading.value = false
  }
}
</script>
