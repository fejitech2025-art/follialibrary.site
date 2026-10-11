
<template>
  <AuthLayout>
    <div class="auth-mobile-brand">
      <BrandLogo />
      <span>Follia Library</span>
    </div>

    <div class="auth-heading">
      <p class="auth-kicker">JOIN THE LIBRARY</p>
      <h1>Create account</h1>
<p>Discover, share, and connect through resources that matter to you.</p>
    </div>

    <!-- Google sign-up -->
    <button
      class="google-button"
      type="button"
      :disabled="googleLoading || loading"
      @click="signUpWithGoogle"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill="#4285F4"
          d="M21.35 12.23c0-.79-.07-1.55-.22-2.27H12v4.3h5.24a4.48 4.48 0 0 1-1.94 2.94v2.45h3.14c1.84-1.7 2.91-4.2 2.91-7.42Z"
        />

        <path
          fill="#34A853"
          d="M12 21.5c2.63 0 4.84-.87 6.45-2.35l-3.14-2.45c-.87.58-1.98.93-3.31.93-2.54 0-4.69-1.72-5.46-4.03H3.3v2.53A9.74 9.74 0 0 0 12 21.5Z"
        />

        <path
          fill="#FBBC05"
          d="M6.54 13.6a5.86 5.86 0 0 1 0-3.74V7.33H3.3a9.75 9.75 0 0 0 0 8.8l3.24-2.53Z"
        />

        <path
          fill="#EA4335"
          d="M12 5.83c1.43 0 2.72.49 3.73 1.45l2.8-2.8C16.84 2.9 14.63 2 12 2a9.74 9.74 0 0 0-8.7 5.33l3.24 2.53C7.31 7.55 9.46 5.83 12 5.83Z"
        />
      </svg>

      <span>{{ googleLoading ? 'Connecting to Google...' : 'Continue with Google' }}</span>
    </button>

    <div class="auth-divider">
      <span>or sign up with email</span>
    </div>

    <!-- Registration form -->
    <form class="auth-form" @submit.prevent="handleRegister">
      <!-- Name -->
      <div class="auth-field">
        <label for="displayName">Name</label>

        <input
          id="displayName"
          v-model.trim="displayName"
          type="text"
          autocomplete="name"
          placeholder="Your name"
          required
        />
      </div>

      <!-- Email -->
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

      <!-- Password -->
      <div class="auth-field">
        <label for="password">Password</label>

        <div class="password-input">
          <input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            placeholder="At least 8 characters"
            minlength="6"
            required
          />

          <button
            type="button"
            class="password-toggle"
            :disabled="loading"
            @click="showPassword = !showPassword"
          >
            {{ showPassword ? 'Hide' : 'Show' }}
          </button>
        </div>
      </div>

      <!-- Confirm password -->
      <div class="auth-field">
        <label for="confirmPassword">Confirm password</label>

        <div class="password-input">
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            autocomplete="new-password"
            placeholder="Repeat your password"
            minlength="6"
            required
          />

          <button
            type="button"
            class="password-toggle"
            :disabled="loading"
            @click="showConfirmPassword = !showConfirmPassword"
          >
            {{ showConfirmPassword ? 'Hide' : 'Show' }}
          </button>
        </div>
      </div>

      <!-- Error -->
      <div v-if="errorMessage" class="auth-error" role="alert">
        {{ errorMessage }}
      </div>

      <!-- Submit -->
      <button
        class="auth-submit"
        type="submit"
        :disabled="loading || googleLoading"
      >
        {{ loading ? 'Creating account...' : 'Create account' }}
      </button>
    </form>

    <p class="auth-terms">
      By creating an account, you agree to use Follia Library responsibly.
      <button type="button" @click="showPolicyModal = true">
        Terms & Privacy Policy
      </button>
    </p>

    <p class="auth-switch">
      Already have an account?
      <RouterLink to="/login">Sign in</RouterLink>
    </p>

    <!-- Terms & Privacy Policy -->
    <Teleport to="body">
      <div
        v-if="showPolicyModal"
        class="policy-overlay"
        @click.self="showPolicyModal = false"
      >
        <div
          class="policy-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="policy-title"
        >
          <div class="policy-header">
            <div>
              <p class="policy-kicker">FOLLIA LIBRARY</p>
              <h2 id="policy-title">Terms & Privacy Policy</h2>
              <p class="policy-updated">
                Please review the rules for using our platform.
              </p>
            </div>

            <button
              class="policy-close"
              type="button"
              aria-label="Close policy"
              @click="showPolicyModal = false"
            >
              ×
            </button>
          </div>

          <div class="policy-content">
            <p class="policy-notice">
              These are the platform's current policy terms. We may update them as
              our services evolve, and will provide appropriate notice of material
              changes where required.
            </p>

            <section>
              <h3>1. Using Follia Library</h3>

              <p>
                Follia Library is a platform for discovering, sharing, saving, and
                discussing educational resources and other permitted content.
                Features may include profiles, posts, comments, likes, connections,
                bookmarks, notifications, and book clubs.
              </p>

              <p>
                You agree to provide accurate account information, protect your
                login credentials, and use the platform lawfully and respectfully.
                You are responsible for activity carried out through your account.
              </p>
            </section>

            <section>
              <h3>2. Content and copyright</h3>

              <p>
                You retain any rights you have in content you create. When you
                upload or publish content, you confirm that you own it or have the
                permissions required to share it.
              </p>

              <p>
                You must not upload, distribute, or promote material that infringes
                copyright, violates another person's rights, or breaches applicable
                law. By submitting content, you grant Follia Library permission to
                host, store, display, and distribute it as necessary to operate the
                features you use, subject to your settings and applicable law.
              </p>

              <p>
                We may restrict access to reported material, remove content, or
                take other appropriate action when there is a credible rights
                complaint or a violation of these terms. You can contact us through
                the support channel provided on our platform to report copyright
                concerns.
              </p>
            </section>

            <section>
              <h3>3. Prohibited content and conduct</h3>

              <p>You must not use Follia Library to publish, share, or promote:</p>

              <ul>
                <li>
                  Sexual exploitation or abuse, including any sexual content
                  involving minors.
                </li>
                <li>Non-consensual intimate images or sexual harassment.</li>
                <li>
                  Credible threats, targeted harassment, or encouragement of
                  violence.
                </li>
                <li>Illegal material, fraud, scams, impersonation, or malicious files.</li>
                <li>
                  Copyright-infringing uploads or content shared without necessary
                  permission.
                </li>
                <li>
                  Spam, deceptive activity, or attempts to compromise other
                  accounts or systems.
                </li>
              </ul>

              <p>
                Content that is unlawful, exploitative, or otherwise prohibited
                may be removed. Serious or repeated violations may result in
                account restrictions or termination.
              </p>
            </section>

            <section>
              <h3>4. Age eligibility and safety</h3>

              <p>
                Users must meet the minimum age requirements applicable to their
                location and any higher minimum age established by Follia Library.
                A parent or guardian's permission does not override a minimum age
                where the law does not allow it.
              </p>

              <p>
                Do not use the platform to expose children to sexual, exploitative,
                or otherwise harmful material. Do not solicit personal information
                from children or attempt to exploit, groom, or endanger them.
              </p>

              <p>
                We may investigate suspected underage accounts or harmful content
                and take appropriate action, subject to applicable law. Users
                should report suspected child-safety violations promptly.
              </p>
            </section>

            <section>
              <h3>5. Reporting and moderation</h3>

              <p>
                Users should report content, accounts, or conduct that may violate
                these rules. We may review reports, remove or restrict content,
                limit platform features, suspend accounts, or permanently terminate
                accounts when appropriate.
              </p>

              <p>
                We cannot guarantee that every harmful item will be detected
                immediately or that all user-published information is accurate.
                Do not rely on Follia Library as a substitute for appropriate
                safety precautions.
              </p>
            </section>

            <section>
              <h3>6. Privacy and personal information</h3>

              <p>
                We process personal information to operate accounts, authenticate
                users, display profiles, deliver requested features, support
                interactions, protect platform security, and respond to support
                requests.
              </p>

              <p>
                Depending on the features you use, information may include account
                details, profile information, uploaded content, comments,
                connections, bookmarks, notifications, and technical or usage
                information.
              </p>

              <p>
                Content or profile details you make public may be visible to other
                users. Do not publish sensitive personal information that you do
                not want others to see. We do not sell personal information as a
                business model. Information may be processed by service providers
                where necessary to operate the platform, subject to applicable
                safeguards and legal requirements.
              </p>
            </section>

            <section>
              <h3>7. Google sign-in and third-party services</h3>

              <p>
                If you choose Google sign-in, Google processes information
                according to its own terms and privacy policy. Follia Library
                receives the information required to authenticate your account
                and provide the service.
              </p>

              <p>
                Third-party services may have separate policies and availability
                conditions. Follia Library is not responsible for the independent
                policies of those services.
              </p>
            </section>

            <section>
              <h3>8. Account security and deletion</h3>

              <p>
                Keep your password and verification details secure, and notify us
                if you suspect unauthorized access. Do not access another person's
                account without permission.
              </p>

              <p>
                You may request account deletion through the account controls
                provided by the platform or by contacting our support channel.
                Some information may need to be retained for legitimate legal,
                security, or dispute-resolution purposes, where permitted by law.
                Deletion and retention are subject to applicable requirements.
              </p>
            </section>

            <section>
              <h3>9. Changes and enforcement</h3>

              <p>
                We may update these terms, introduce or change features, and
                enforce platform rules to protect users and the service. Where
                required, we will provide notice of material policy changes.
              </p>

              <p>
                Nothing in these terms removes rights that applicable law does
                not permit us to exclude or limit.
              </p>
            </section>

            <section>
              <h3>10. Contact</h3>

              <p>
                For privacy requests, copyright complaints, safety reports, or
                questions about these terms, use the official support contact
                published by Follia Library.
              </p>
            </section>
          </div>

          <div class="policy-footer">
            <button type="button" @click="showPolicyModal = false">Close</button>
          </div>
        </div>
      </div>
    </Teleport>
  </AuthLayout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../components/BrandLogo.vue'
import AuthLayout from '../components/auth/AuthLayout.vue'
import { useAuth } from '../composables/useAuth'
import { submitGoogleLogin } from '../services/api'

const router = useRouter()
const { signUp } = useAuth()

const displayName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)
const googleLoading = ref(false)
const errorMessage = ref('')
const showPolicyModal = ref(false)

async function handleRegister() {
  errorMessage.value = ''

  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }

  if (password.value.length < 8) {
    errorMessage.value = 'Password must be at least 8 characters.'
    return
  }

  loading.value = true

  try {
    await signUp(email.value, password.value, displayName.value)
    await router.push('/')
  } catch (error) {
    errorMessage.value = error.message || 'Unable to create your account.'
  } finally {
    loading.value = false
  }
}

async function signUpWithGoogle() {
  if (googleLoading.value || loading.value) return

  errorMessage.value = ''
  googleLoading.value = true

  try {
    await submitGoogleLogin()
  } catch (error) {
    errorMessage.value =
      error.message || 'Google sign-up could not be started.'
    googleLoading.value = false
  }
}
</script>

<style scoped>
.auth-terms {
  margin-top: 18px;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.6;
  text-align: center;
}

.auth-terms button {
  display: inline;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text-main);
  font: inherit;
  font-size: inherit;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.auth-terms button:hover {
  opacity: 0.75;
}

.coming-soon-google {
  cursor: not-allowed;
  opacity: 0.58;
}

.coming-soon-google:disabled {
  cursor: not-allowed;
}

.coming-soon-badge {
  margin-left: auto;
  flex-shrink: 0;
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--card-soft);
  color: var(--text-tertiary);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
}

.policy-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.5);
}

.policy-modal {
  width: min(620px, 100%);
  max-height: min(720px, 90vh);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border-soft);
  border-radius: 24px;
  background: var(--card-bg);
  box-shadow: 0 25px 80px var(--shadow-color);
}

.policy-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 24px;
  border-bottom: 1px solid var(--border-soft);
}

.policy-kicker {
  margin: 0 0 5px;
  color: var(--text-tertiary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.13em;
}

.policy-header h2 {
  margin: 0;
  color: var(--text-main);
  font-size: 21px;
}

.policy-updated {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.policy-close {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: transparent;
  color: var(--text-main);
  font-size: 25px;
  line-height: 1;
  cursor: pointer;
}

.policy-content {
  overflow-y: auto;
  padding: 24px;
}

.policy-content section + section {
  margin-top: 26px;
}

.policy-content h3 {
  margin: 0 0 9px;
  color: var(--text-main);
  font-size: 16px;
}

.policy-content p,
.policy-content li {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.65;
}

.policy-content p {
  margin: 0 0 10px;
}

.policy-content p:last-child {
  margin-bottom: 0;
}

.policy-content ul {
  margin: 8px 0 14px;
  padding-left: 22px;
}

.policy-content li + li {
  margin-top: 6px;
}

.policy-notice {
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--card-soft);
}

.policy-footer {
  display: flex;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid var(--border-soft);
}

.policy-footer button {
  border: 0;
  border-radius: 11px;
  padding: 10px 17px;
  background: var(--primary-bg);
  color: var(--primary-text);
  font-weight: 700;
  cursor: pointer;
}

@media (max-width: 600px) {
  .policy-overlay {
    align-items: flex-end;
    padding: 0;
  }

  .policy-modal {
    width: 100%;
    max-height: 88vh;
    border-radius: 24px 24px 0 0;
  }

  .policy-header {
    padding: 18px 20px;
  }

  .policy-content {
    padding: 20px;
  }

  .policy-footer {
    padding: 14px 20px;
  }

  .policy-footer button {
    width: 100%;
  }
}
</style>
