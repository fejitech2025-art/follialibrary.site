<template>
  <AuthLayout>
    <div class="reset-card">
      <p class="auth-kicker">ACCOUNT SECURITY</p>
      <h1>Choose a new password</h1>
      <p class="intro">Use a password you have not used for Follia before.</p>
      <form @submit.prevent="resetPassword">
        <label for="new-password">New password</label>
        <input id="new-password" v-model="password" type="password" minlength="8" autocomplete="new-password" required />
        <label for="confirm-password">Confirm password</label>
        <input id="confirm-password" v-model="confirm" type="password" minlength="8" autocomplete="new-password" required />
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
        <button :disabled="loading || !!success">{{ loading ? 'Saving…' : 'Update password' }}</button>
      </form>
      <RouterLink to="/login">Back to sign in</RouterLink>
    </div>
  </AuthLayout>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthLayout from '../components/auth/AuthLayout.vue'
import { api } from '../services/api'

const route = useRoute()
const router = useRouter()
const password = ref('')
const confirm = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

async function resetPassword() {
  error.value = ''
  if (password.value !== confirm.value) { error.value = 'Passwords do not match.'; return }
  loading.value = true
  try {
    const result = await api('/api/auth/password-reset/confirm/', {
      method: 'POST',
      body: { uid: route.params.uid, token: route.params.token, password: password.value },
    })
    success.value = result.detail || 'Password updated.'
    window.setTimeout(() => router.replace('/login'), 1800)
  } catch (err) {
    error.value = err.message || 'Unable to reset this password.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.reset-card { width:min(440px,100%); margin:40px auto; padding:30px; border:1px solid var(--border-color); border-radius:22px; background:var(--card-bg); }
.auth-kicker { margin:0 0 9px; color:var(--text-tertiary); font-size:10px; font-weight:750; letter-spacing:.14em; }
.reset-card h1 { margin:0; font:800 30px/1.1 Manrope,sans-serif; letter-spacing:-.05em; }
.intro { margin:9px 0 22px; color:var(--text-secondary); font-size:13px; line-height:1.5; }
.reset-card form { display:grid; gap:9px; }
.reset-card label { margin-top:4px; font-size:11px; font-weight:700; }
.reset-card input { height:45px; padding:0 12px; border:1px solid var(--border-color); border-radius:11px; background:var(--input-bg); color:var(--text-main); outline:0; }
.reset-card button { height:45px; margin-top:10px; border-radius:11px; background:var(--primary-bg); color:var(--primary-text); font-size:12px; font-weight:700; }
.reset-card button:disabled { opacity:.55; }
.reset-card > a { display:block; margin-top:18px; color:var(--text-secondary); text-align:center; font-size:12px; }
.error { color:#a33b30; font-size:11px; }
.success { color:#397755; font-size:11px; }
</style>
