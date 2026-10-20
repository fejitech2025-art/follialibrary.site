<template>
  <div class="edit-profile-page">
    <div class="edit-profile-container">
      <!-- Header -->
      <div class="edit-page-header">
        <RouterLink to="/account" class="back-button">
          <ArrowLeft :size="18" />
        </RouterLink>

        <div>
          <p class="edit-page-kicker">ACCOUNT</p>
          <h1>Edit Profile</h1>
        </div>
      </div>

      <!-- Profile -->
      <section class="settings-card profile-settings-card">
        <div class="settings-card-header">
          <div>
            <p class="settings-kicker">PROFILE</p>
            <h2>Your profile</h2>
            <p>Update how your profile appears across Follia Library.</p>
          </div>
        </div>

        <!-- Avatar -->
        <div class="profile-photo-section">
          <div class="profile-photo-wrapper">
            <div class="profile-photo"><UserAvatar :src="avatarPreview" alt="Profile preview" :icon-size="30" /></div>

            <button
              class="photo-camera-button"
              type="button"
              @click="triggerImageUpload"
              aria-label="Change profile image"
            >
              <Camera :size="16" />
            </button>
          </div>

          <div class="photo-info">
            <h3>Profile photo</h3>
            <p>Use a clear image so people can recognize you.</p>

            <div class="photo-actions">
              <button
                class="secondary-button"
                type="button"
                :disabled="saving"
                @click="triggerImageUpload"
              >
                <Upload :size="15" />
                Upload image
              </button>

              <button
                v-if="avatarPreview"
                class="text-button"
                type="button"
                :disabled="saving"
                @click="removeImage"
              >
                Remove
              </button>
            </div>

            <input
              ref="imageInput"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              hidden
              @change="handleImageUpload"
            />
          </div>
        </div>

        <!-- Fields -->
        <div class="form-grid">
          <div class="form-field full-width">
            <label for="displayName">Display name</label>

            <input
              id="displayName"
              v-model="form.displayName"
              type="text"
              placeholder="Your name"
              maxlength="50"
            />

            <span class="field-hint">
              This is the name other people will see.
            </span>
          </div>

          <div class="form-field">
            <label for="username">Username</label>

            <div class="input-with-prefix">
              <span>@</span>

              <input
                id="username"
                v-model="form.username"
                type="text"
                placeholder="yourusername"
                maxlength="30"
              />
            </div>

            <span class="field-hint">
              Your unique username on Follia Library.
            </span>
          </div>

          <div class="form-field">
            <label for="location">Location</label>

            <div class="input-with-icon">
              <MapPin :size="16" />

              <input
                id="location"
                v-model="form.location"
                type="text"
                placeholder="Lagos, Nigeria"
                maxlength="80"
              />
            </div>
          </div>

          <div class="form-field full-width">
            <label for="bio">Bio</label>

            <textarea
              id="bio"
              v-model="form.bio"
              rows="4"
              maxlength="160"
              placeholder="Tell people a little about yourself..."
            ></textarea>

            <div class="textarea-footer">
              <span>Keep it short and personal.</span>
              <span>{{ form.bio.length }}/160</span>
            </div>
          </div>

          <div class="form-field full-width">
            <label for="website">Website</label>

            <div class="input-with-icon">
              <Globe :size="16" />

              <input
                id="website"
                v-model="form.website"
                type="url"
                placeholder="https://example.com"
              />
            </div>
          </div>
        </div>
      </section>

      <!-- Appearance -->
      <section class="settings-card">
        <div class="settings-card-header">
          <div>
            <p class="settings-kicker">APPEARANCE</p>
            <h2>Theme</h2>
            <p>Choose how Follia Library looks on your device.</p>
          </div>
        </div>

        <div class="theme-options">
          <button
            v-for="option in themeOptions"
            :key="option.value"
            type="button"
            class="theme-option"
            :class="{ selected: theme === option.value }"
            @click="setTheme(option.value)"
          >
            <div
              class="theme-preview"
              :class="`theme-preview-${option.value}`"
            >
              <div class="theme-preview-top"></div>

              <div class="theme-preview-content">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>

            <div class="theme-option-info">
              <div class="theme-option-title">
                <component :is="option.icon" :size="16" />
                <span>{{ option.label }}</span>
              </div>

              <p>{{ option.description }}</p>
            </div>

            <div
              class="theme-radio"
              :class="{ active: theme === option.value }"
            >
              <Check v-if="theme === option.value" :size="13" />
            </div>
          </button>
        </div>
      </section>

      <!-- Account -->
      <section class="settings-card">
        <div class="settings-card-header">
          <div>
            <p class="settings-kicker">ACCOUNT</p>
            <h2>Account settings</h2>
            <p>Manage your Follia Library account.</p>
          </div>
        </div>

        <div class="account-settings-list">
          <!-- Email -->
          <div class="account-setting-row">
            <div class="account-setting-icon">
              <Mail :size="17" />
            </div>

            <div>
              <h3>Email address</h3>
              <p>{{ email || 'Loading...' }}</p>
            </div>
          </div>

          <!-- Password -->
          <button type="button" class="account-setting-row">
            <div class="account-setting-icon">
              <Lock :size="17" />
            </div>

            <div>
              <h3>Password</h3>
              <p>Change your account password</p>
            </div>

            <ChevronRight :size="17" />
          </button>

          <!-- Logout -->
          <button
            type="button"
            class="logout-button"
            :disabled="loggingOut"
            @click="logout"
          >
            <div class="logout-icon">
              <LogOut :size="17" />
            </div>

            <div class="logout-info">
              <h3>{{ loggingOut ? 'Logging out...' : 'Log out' }}</h3>
              <p>Sign out of your Follia Library account.</p>
            </div>

            <ChevronRight :size="17" />
          </button>
        </div>
      </section>

      <!-- Error -->
      <div v-if="errorMessage" class="profile-error">
        {{ errorMessage }}
      </div>

      <!-- Save -->
      <div class="save-profile-bar">
        <p v-if="saved">
          <CheckCircle :size="16" />
          Changes saved
        </p>

        <button
          type="button"
          class="save-button"
          :disabled="saving || loading"
          @click="saveProfile"
        >
          {{ saving ? 'Saving...' : loading ? 'Loading...' : 'Save changes' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { resolveMediaUrl } from '../utils/media'

import { onMounted, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  ArrowLeft,
  Camera,
  Check,
  CheckCircle,
  ChevronRight,
  Globe,
  Lock,
  LogOut,
  Mail,
  MapPin,
  Moon,
  Sun,
  Monitor,
  Upload,
} from 'lucide-vue-next'

import { useTheme } from '../composables/useTheme'
import { useAuth } from '../composables/useAuth'
import UserAvatar from '../components/UserAvatar.vue'

import {
  getCurrentUser,
  getMyProfile,
  updateMyProfile,
  uploadAvatar,
} from '../services/profileService'

const router = useRouter()

const { theme, setTheme } = useTheme()
const { signOut } = useAuth()

const imageInput = ref(null)

const avatarPreview = ref(null)
const avatarFile = ref(null)

const saving = ref(false)
const saved = ref(false)
const loading = ref(true)
const loggingOut = ref(false)

const errorMessage = ref('')
const email = ref('')

const form = ref({
  displayName: '',
  username: '',
  location: '',
  bio: '',
  website: '',
})

const themeOptions = [
  {
    value: 'light',
    label: 'Light',
    description: 'Clean and bright.',
    icon: Sun,
  },
  {
    value: 'dark',
    label: 'Dark',
    description: 'Easy on the eyes.',
    icon: Moon,
  },
  {
    value: 'system',
    label: 'System',
    description: 'Follow your device.',
    icon: Monitor,
  },
]

/*
|--------------------------------------------------------------------------
| Load profile
|--------------------------------------------------------------------------
*/

async function loadProfile() {
  loading.value = true
  errorMessage.value = ''

  try {
    const [profile, user] = await Promise.all([
      getMyProfile(),
      getCurrentUser(),
    ])

    form.value.displayName = profile?.display_name || ''
    form.value.username = profile?.username || ''
    form.value.location = profile?.location || ''
    form.value.bio = profile?.bio || ''
    form.value.website = profile?.website || ''

    // Support both the API URL field and a local Django media path.
    avatarPreview.value = resolveMediaUrl(
      profile?.avatar_url || profile?.avatar || null,
    )

    // Email is managed by the Django account system.
    email.value = user?.email || ''
  } catch (error) {
    console.error('Profile loading error:', error)

    errorMessage.value =
      error.message || 'Unable to load your profile.'
  } finally {
    loading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Image upload preview
|--------------------------------------------------------------------------
*/

function triggerImageUpload() {
  imageInput.value?.click()
}

function handleImageUpload(event) {
  const file = event.target.files?.[0]

  if (!file) {
    return
  }

  if (!file.type.startsWith('image/')) {
    errorMessage.value = 'Please choose an image file.'
    event.target.value = ''
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    errorMessage.value = 'Please choose an image smaller than 5 MB.'
    event.target.value = ''
    return
  }

  errorMessage.value = ''

  // Clean up the previous temporary preview URL.
  if (avatarPreview.value?.startsWith('blob:')) {
    URL.revokeObjectURL(avatarPreview.value)
  }

  avatarFile.value = file
  avatarPreview.value = URL.createObjectURL(file)
}

function removeImage() {
  if (avatarPreview.value?.startsWith('blob:')) {
    URL.revokeObjectURL(avatarPreview.value)
  }

  avatarPreview.value = null
  avatarFile.value = null

  if (imageInput.value) {
    imageInput.value.value = ''
  }
}

/*
|--------------------------------------------------------------------------
| Save profile
|--------------------------------------------------------------------------
*/

async function saveProfile() {
  saving.value = true
  saved.value = false
  errorMessage.value = ''

  try {
    const currentProfile = await getMyProfile()

    const currentUsername =
      currentProfile?.username?.trim().toLowerCase() || ''

    const newUsername = form.value.username.trim().toLowerCase()

    /*
     * Keep the existing profile service payload.
     * The backend service must support these fields.
     */

    const profileData = {
      display_name: form.value.displayName.trim(),
      location: form.value.location.trim(),
      bio: form.value.bio.trim(),
      website: form.value.website.trim(),
      avatar_url: avatarPreview.value || null,
      updated_at: new Date().toISOString(),
    }

    // Only include username if it actually changed.
    if (newUsername && newUsername !== currentUsername) {
      profileData.username = newUsername
    }

    // Upload a newly selected avatar.
    let avatarUrl = avatarPreview.value

    if (avatarFile.value) {
      avatarUrl = await uploadAvatar(avatarFile.value)

      profileData.avatar_url = avatarUrl
    }

    // Save the profile.
    await updateMyProfile(profileData)

    // Clear temporary file state after a successful save.
    if (avatarPreview.value?.startsWith('blob:')) {
      URL.revokeObjectURL(avatarPreview.value)
    }

    avatarFile.value = null
    avatarPreview.value = resolveMediaUrl(avatarUrl || null)

    if (imageInput.value) {
      imageInput.value.value = ''
    }

    saved.value = true

    setTimeout(() => {
      saved.value = false
    }, 3000)
  } catch (error) {
    console.error('Profile save error:', error)

    errorMessage.value =
      error.message || 'Unable to save your profile.'
  } finally {
    saving.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Logout
|--------------------------------------------------------------------------
*/

async function logout() {
  loggingOut.value = true
  errorMessage.value = ''

  try {
    await signOut()

    router.replace({
      name: 'login',
    })
  } catch (error) {
    console.error('Logout error:', error)

    errorMessage.value =
      error.message || 'Unable to log out.'
  } finally {
    loggingOut.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Mounted
|--------------------------------------------------------------------------
*/

onMounted(() => {
  loadProfile()
})

/*
|--------------------------------------------------------------------------
| Cleanup
|--------------------------------------------------------------------------
*/

onBeforeUnmount(() => {
  if (avatarPreview.value?.startsWith('blob:')) {
    URL.revokeObjectURL(avatarPreview.value)
  }
})
</script>

<style scoped>
.logout-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 0;
  border: 0;
  border-top: 1px solid var(--border-soft);
  background: transparent;
  color: var(--text-main);
  text-align: left;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.logout-button:hover {
  opacity: 0.8;
}

.logout-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.logout-icon {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--card-soft);
  color: #c94b4b;
}

.logout-info {
  flex: 1;
  min-width: 0;
}

.logout-info h3 {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 700;
  color: #c94b4b;
}

.logout-info p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.logout-button > svg {
  flex-shrink: 0;
  color: var(--text-tertiary);
}
</style>
