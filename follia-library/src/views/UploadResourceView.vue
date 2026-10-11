<template>
  <MainLayout>
    <section class="upload-page">
      <div class="upload-heading">
        <div>
          <p class="page-kicker">PUBLISH</p>
          <h1>Share a resource.</h1>
          <p>Upload something useful and make it available to people looking for knowledge.</p>
        </div>

        <RouterLink to="/bookshelf" class="upload-back-button"> Cancel </RouterLink>
      </div>

      <form class="upload-layout" @submit.prevent="publishResource">
        <div class="upload-main">
          <!-- Resource file -->
          <section class="upload-card">
            <div class="upload-card-heading">
              <div>
                <p class="upload-card-kicker">RESOURCE FILE</p>
                <h2>Upload your resource</h2>
              </div>
              <span class="required-label">Required</span>
            </div>

            <label class="file-dropzone" :class="{ 'has-file': selectedFile }">
              <input type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.txt" @change="handleFile" />

              <div v-if="!selectedFile" class="dropzone-content">
                <div class="dropzone-icon"><Upload :size="24" /></div>
                <strong>Choose your resource file</strong>
                <span>PDF, DOC, DOCX, PPT, PPTX or TXT</span>
                <small>Click to browse your files</small>
              </div>

              <div v-else class="selected-file">
                <div class="selected-file-icon"><FileText :size="23" /></div>

                <div class="selected-file-info">
                  <strong>{{ selectedFile.name }}</strong>
                  <span>{{ formatFileSize(selectedFile.size) }}</span>
                </div>

                <button
                  type="button"
                  class="remove-file"
                  aria-label="Remove file"
                  @click.prevent="removeFile"
                >
                  <X :size="17" />
                </button>
              </div>
            </label>

            <p class="field-hint">Maximum file size: 50 MB.</p>
          </section>

          <!-- Optional cover -->
          <section class="upload-card">
            <div class="upload-card-heading">
              <div>
                <p class="upload-card-kicker">COVER IMAGE</p>
                <h2>Give it a visual identity</h2>
              </div>
              <span class="optional-label">Optional</span>
            </div>

            <label class="cover-upload" :class="{ 'has-cover': coverPreview }">
              <input type="file" accept="image/*" @change="handleCover" />

              <img v-if="coverPreview" :src="coverPreview" alt="Resource cover preview" />

              <div v-else class="cover-upload-empty">
                <ImageIcon :size="24" />
                <strong>Add a cover image</strong>
                <span>JPG, PNG or WebP · Max 5 MB</span>
              </div>
            </label>

            <button v-if="coverPreview" type="button" class="remove-file" @click="removeCover">
              <X :size="16" />
              Remove cover
            </button>
          </section>

          <!-- Resource details -->
          <section class="upload-card">
            <div class="upload-card-heading">
              <div>
                <p class="upload-card-kicker">RESOURCE DETAILS</p>
                <h2>Tell people about it</h2>
              </div>
            </div>

            <div class="form-grid">
              <div class="form-field full">
                <label for="title">Title</label>
                <input
                  id="title"
                  v-model.trim="form.title"
                  type="text"
                  maxlength="200"
                  placeholder="e.g. Introduction to Biology"
                  required
                />
              </div>

              <div class="form-field">
                <label for="category">Category</label>
                <select id="category" v-model="form.category" required>
                  <option value="" disabled>Select category</option>
                  <option>Books</option>
                  <option>Science</option>
                  <option>Mathematics</option>
                  <option>Technology</option>
                  <option>Business</option>
                  <option>Arts &amp; Design</option>
                  <option>Education</option>
                  <option>Other</option>
                </select>
              </div>

              <div class="form-field">
                <label for="language">Language</label>
                <select id="language" v-model="form.language">
                  <option>English</option>
                  <option>French</option>
                  <option>Spanish</option>
                  <option>Arabic</option>
                  <option>Other</option>
                </select>
              </div>

              <div class="form-field full">
                <label for="description">Description</label>
                <textarea
                  id="description"
                  v-model.trim="form.description"
                  rows="6"
                  placeholder="Tell readers what they will find in this resource..."
                ></textarea>
              </div>

              <div class="form-field full">
                <label for="tags">Tags</label>
                <input
                  id="tags"
                  v-model="form.tags"
                  type="text"
                  placeholder="biology, university, science, study"
                />
                <span class="field-hint">Separate tags with commas.</span>
              </div>
            </div>
          </section>

          <!-- Pricing -->
          <section class="upload-card">
            <div class="upload-card-heading">
              <div>
                <p class="upload-card-kicker">ACCESS &amp; PRICING</p>
                <h2>Choose how people get it</h2>
              </div>
            </div>

            <div class="pricing-options">
              <!-- Free -->
              <button
                type="button"
                class="pricing-option"
                :class="{ selected: form.free }"
                @click="form.free = true"
              >
                <div class="pricing-option-icon">
                  <Gift :size="21" />
                </div>

                <div>
                  <strong>Free</strong>
                  <span>Anyone can access this resource for free.</span>
                </div>

                <div class="pricing-radio">
                  <span></span>
                </div>
              </button>

              <!-- Paid — Coming soon -->
              <button
                type="button"
                class="pricing-option pricing-option-disabled"
                disabled
                aria-label="Paid resources coming soon"
              >
                <div class="pricing-option-icon">
                  <CreditCard :size="21" />
                </div>

                <div class="pricing-option-content">
                  <strong>Paid</strong>
                  <span>Set a price for your resource.</span>
                </div>

                <span class="coming-soon-badge">Coming soon</span>
              </button>
            </div>

            <div v-if="!form.free" class="paid-resource">
              <label for="price">Price (NGN)</label>

              <div class="price-input-wrapper">
                <span>₦</span>

                <input
                  id="price"
                  v-model.number="form.price"
                  type="number"
                  min="1"
                  step="1"
                  placeholder="2500"
                  required
                />
              </div>

              <p class="charge-preview">Follia Charges will apply to successful sales.</p>
            </div>
          </section>
        </div>

        <!-- Publish panel -->
        <aside class="upload-sidebar">
          <div class="publish-card">
            <div class="publish-card-icon"><Send :size="22" /></div>
            <h2>Ready to publish?</h2>
            <p>Your resource will appear in the Library once it has been published.</p>

            <div v-if="uploadProgress" class="upload-progress">
              {{ uploadProgress }}
            </div>

            <button type="submit" class="publish-button" :disabled="publishing">
              <LoaderCircle v-if="publishing" :size="17" class="spin" />
              <span>{{ publishing ? 'Publishing...' : 'Publish Resource' }}</span>
              <ArrowUpRight v-if="!publishing" :size="17" />
            </button>
          </div>

          <div class="upload-tips">
            <div class="upload-tips-heading">
              <Lightbulb :size="17" />
              <strong>Publishing tips</strong>
            </div>
            <ul>
              <li>Use a clear, descriptive title.</li>
              <li>Explain what readers will learn.</li>
              <li>Add a cover to help your resource stand out.</li>
              <li>Use relevant tags.</li>
            </ul>
          </div>
        </aside>
      </form>

      <p v-if="errorMessage" class="upload-error" role="alert">
        {{ errorMessage }}
      </p>

      <p v-if="successMessage" class="upload-success" role="status">
        {{ successMessage }}
        <RouterLink to="/">View Library</RouterLink>
      </p>
    </section>
  </MainLayout>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import {
  Upload,
  FileText,
  X,
  Image as ImageIcon,
  Gift,
  CreditCard,
  Send,
  ArrowUpRight,
  Lightbulb,
  LoaderCircle,
} from 'lucide-vue-next'

import MainLayout from '../layouts/MainLayout.vue'
import {
  createResource,
  uploadResourceFile,
  uploadResourceCover,
} from '../services/resourceService'
import { updateResource, deleteResource } from '../services/resourceService'

const MAX_RESOURCE_SIZE = 50 * 1024 * 1024
const MAX_COVER_SIZE = 5 * 1024 * 1024

const selectedFile = ref(null)
const coverFile = ref(null)
const coverPreview = ref(null)
const publishing = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const uploadProgress = ref('')

const form = ref({
  title: '',
  category: '',
  language: 'English',
  description: '',
  tags: '',
  free: true,
  price: null,
})

function handleFile(event) {
  const file = event.target.files?.[0]
  if (!file) return

  errorMessage.value = ''
  successMessage.value = ''

  if (file.size > MAX_RESOURCE_SIZE) {
    event.target.value = ''
    errorMessage.value = 'The resource file must be 50 MB or smaller.'
    return
  }

  selectedFile.value = file
}

function removeFile() {
  selectedFile.value = null
}

function handleCover(event) {
  const file = event.target.files?.[0]
  if (!file) return

  errorMessage.value = ''

  if (!file.type.startsWith('image/')) {
    event.target.value = ''
    errorMessage.value = 'Please choose a valid image file.'
    return
  }

  if (file.size > MAX_COVER_SIZE) {
    event.target.value = ''
    errorMessage.value = 'The cover image must be 5 MB or smaller.'
    return
  }

  if (coverPreview.value) {
    URL.revokeObjectURL(coverPreview.value)
  }

  coverFile.value = file
  coverPreview.value = URL.createObjectURL(file)
}

function removeCover() {
  if (coverPreview.value) {
    URL.revokeObjectURL(coverPreview.value)
  }

  coverPreview.value = null
  coverFile.value = null
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function resetForm() {
  form.value = {
    title: '',
    category: '',
    language: 'English',
    description: '',
    tags: '',
    free: true,
    price: null,
  }

  selectedFile.value = null
  removeCover()
}

async function publishResource() {
  errorMessage.value = ''
  successMessage.value = ''
  uploadProgress.value = ''

  if (!selectedFile.value) { errorMessage.value = 'Please select a resource file first.'; return }
  if (!form.value.title.trim()) { errorMessage.value = 'Please enter a title.'; return }
  if (!form.value.category) { errorMessage.value = 'Please select a category.'; return }
  if (!form.value.free && (!form.value.price || form.value.price < 1)) {
    errorMessage.value = 'Please enter a valid resource price.'
    return
  }

  publishing.value = true
  let resource = null
  try {
    uploadProgress.value = 'Creating resource…'
    resource = await createResource({
      title: form.value.title.trim(),
      description: form.value.description.trim(),
      category: form.value.category,
      language: form.value.language,
      tags: form.value.tags.split(',').map((tag) => tag.trim()).filter(Boolean),
      file_name: selectedFile.value.name,
      file_type: selectedFile.value.type || 'application/octet-stream',
      is_free: form.value.free,
      price: form.value.free ? null : Number(form.value.price),
      status: 'draft',
    })
    uploadProgress.value = 'Uploading resource file…'
    await uploadResourceFile(selectedFile.value, resource.id)
    if (coverFile.value) {
      uploadProgress.value = 'Uploading cover image…'
      await uploadResourceCover(coverFile.value, resource.id)
    }
    uploadProgress.value = 'Finishing publication…'
    await updateResource(resource.id, { status: 'published' })
    successMessage.value = 'Your resource is now part of the Follia library.'
    resetForm()
  } catch (error) {
    console.error('Resource publishing error:', error)
    if (resource?.id) {
      try { await deleteResource(resource.id) } catch (cleanupError) {
        console.error('Resource cleanup error:', cleanupError)
      }
    }
    errorMessage.value = error.message || 'Unable to publish this resource.'
  } finally {
    publishing.value = false
    uploadProgress.value = ''
  }
}
onBeforeUnmount(() => {
  if (coverPreview.value) {
    URL.revokeObjectURL(coverPreview.value)
  }
})
</script>

<style scoped>
.pricing-option-disabled {
  position: relative;
  cursor: not-allowed;
  opacity: 0.58;
}

.pricing-option-disabled:disabled {
  cursor: not-allowed;
}

.pricing-option-disabled .pricing-option-icon {
  opacity: 0.75;
}

.pricing-option-content {
  flex: 1;
  min-width: 0;
}

.coming-soon-badge {
  flex-shrink: 0;
  padding: 5px 9px;
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
/* Prevent selected resource files from causing mobile overflow */
.upload-page {
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

.upload-layout,
.upload-main,
.upload-sidebar,
.upload-card,
.file-dropzone,
.selected-file {
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.selected-file {
  width: 100%;
}

.selected-file-info {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
}

.selected-file-info strong {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-file-info span {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-file-icon {
  flex: 0 0 auto;
}

.selected-file .remove-file {
  flex: 0 0 auto;
}
</style>
