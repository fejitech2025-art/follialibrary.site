<template>
  <MainLayout>
    <div class="book-club-page">
      <!-- Loading -->
      <div v-if="loading" class="state-card">
        <LoaderCircle class="spin" :size="24" />
        <p>Loading book club...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="state-card error-state">
        <p>{{ error }}</p>
        <button class="retry-button" type="button" @click="loadClub">Try again</button>
      </div>

      <template v-else-if="club">
        <!-- HEADER -->
        <header class="club-header">
          <button class="header-icon-button" type="button" aria-label="Go back" @click="router.back()">
            <ArrowLeft :size="19" />
          </button>

          <div class="club-header-avatar">
            <img
              v-if="clubAvatarUrl && !clubAvatarFailed"
              :src="clubAvatarUrl"
              :alt="club.name"
              @error="clubAvatarFailed = true"
            />
            <Users v-else :size="21" />
          </div>

          <div class="club-header-info">
            <h1>{{ club.name }}</h1>
            <p>
              {{ club.book_club_members?.length || 0 }}
              {{ club.book_club_members?.length === 1 ? 'member' : 'members' }}
            </p>
          </div>

          <div class="club-header-actions">
            <button class="header-icon-button" type="button" aria-label="Share Book Club" @click="shareBookClub">
              <Share2 :size="18" />
            </button>

            <button
              v-if="isOwner"
              class="header-icon-button"
              type="button"
              aria-label="Book Club settings"
              @click="openEditModal"
            >
              <MoreHorizontal :size="20" />
            </button>
          </div>
        </header>

        <!-- TABS -->
        <div class="club-tabs">
          <button type="button" :class="{ active: activeTab === 'chat' }" @click="activeTab = 'chat'">
            <MessageCircle :size="16" />
            <span>Chat</span>
          </button>

          <button type="button" :class="{ active: activeTab === 'books' }" @click="activeTab = 'books'">
            <BookOpen :size="16" />
            <span>Books</span>
          </button>

          <button type="button" :class="{ active: activeTab === 'about' }" @click="activeTab = 'about'">
            <Users :size="16" />
            <span>About</span>
          </button>
        </div>

        <!-- CHAT -->
        <section v-if="activeTab === 'chat'" class="chat-section">
          <div v-if="!isMember" class="join-card">
            <div class="join-icon">
              <Users :size="22" />
            </div>

            <div class="join-content">
              <h2>Join this Book Club</h2>
              <p>Join the conversation and meet your fellow readers.</p>
            </div>

            <button class="join-button" type="button" @click="joinClub">Join</button>
          </div>

          <div v-else class="chat-shell">
            <div ref="messagesContainer" class="messages-container" @click="closeMessageMenu">
              <div v-if="messagesLoading" class="chat-state">
                <LoaderCircle class="spin" :size="22" />
                <span>Loading conversation...</span>
              </div>

              <div v-else-if="messages.length === 0" class="chat-empty">
                <div class="chat-empty-icon">
                  <MessageCircle :size="25" />
                </div>
                <h3>Start the conversation</h3>
                <p>Be the first person to say something in this Book Club.</p>
              </div>

              <div v-else class="messages-list">
                <div
                  v-for="(message, index) in messages"
                  :key="message.id"
                  class="message-group"
                  :class="{ own: message.sender_id === currentUserId }"
                >
                  <div v-if="shouldShowDate(message, index)" class="date-divider">
                    <span>{{ formatMessageDay(message.created_at) }}</span>
                  </div>

                  <div class="message-row" :class="{ 'own-row': message.sender_id === currentUserId }">
                    <RouterLink
                      v-if="message.sender_id !== currentUserId && message.profiles?.id"
                      :to="{ name: 'publisher-detail', params: { id: message.profiles.id } }"
                      class="message-avatar-link"
                      @click.stop
                    >
                      <UserAvatar :src="message.profiles?.avatar_url || message.profiles?.avatar" :alt="getProfileName(message.profiles)" :icon-size="16" />
                    </RouterLink>

                    <div v-else-if="message.sender_id !== currentUserId" class="message-avatar">
                      <UserAvatar :src="message.profiles?.avatar_url || message.profiles?.avatar" :alt="getProfileName(message.profiles)" :icon-size="16" />
                    </div>

                    <div class="message-main" :class="{ 'own-main': message.sender_id === currentUserId }">
                      <div v-if="message.sender_id !== currentUserId" class="sender-name">
                        {{ getProfileName(message.profiles) }}
                      </div>

                      <div class="message-line">
                        <div
                          class="message-bubble"
                          :class="{ 'own-bubble': message.sender_id === currentUserId }"
                          @contextmenu.prevent="openMessageMenu($event, message)"
                        >
                          <div v-if="message.reply_to" class="message-reply">
                            <div class="reply-name">
                              {{ getProfileName(message.reply_to.profiles) }}
                            </div>
                            <div class="reply-text">{{ getReplyText(message) }}</div>
                          </div>

                          <p class="message-text">{{ getMessageText(message) }}</p>

                          <div class="message-meta">
                            <span>{{ formatMessageTime(message.created_at) }}</span>
                            <Pin v-if="message.is_pinned" :size="11" class="message-pin" />
                          </div>
                        </div>

                        <button
                          class="message-more"
                          type="button"
                          aria-label="Message actions"
                          @click.stop="openMessageMenu($event, message)"
                        >
                          <MoreHorizontal :size="15" />
                        </button>
                      </div>

                      <button
                        v-if="isOwner && message.is_pinned"
                        type="button"
                        class="pinned-label"
                        @click.stop="togglePin(message)"
                      >
                        <Pin :size="10" />
                        Pinned
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div
                v-if="activeMessageMenu"
                ref="messageMenu"
                class="message-menu"
                :style="messageMenuStyle"
                @click.stop
              >
                <button type="button" @click="handleMessageAction('reply')">
                  <Reply :size="15" />
                  <span>Reply</span>
                </button>

                <button type="button" @click="handleMessageAction('copy')">
                  <Copy :size="15" />
                  <span>Copy</span>
                </button>

                <button v-if="isOwner" type="button" @click="handleMessageAction('pin')">
                  <Pin :size="15" />
                  <span>{{ activeMessageMenu.message?.is_pinned ? 'Unpin' : 'Pin' }}</span>
                </button>

                <button
                  v-if="activeMessageMenu.message?.sender_id === currentUserId || isOwner"
                  type="button"
                  class="danger-menu-item"
                  @click="handleMessageAction('delete')"
                >
                  <Trash2 :size="15" />
                  <span>Delete</span>
                </button>
              </div>
            </div>

            <form class="message-composer" @submit.prevent="sendMessage">
              <div v-if="replyingTo" class="replying-bar">
                <div class="replying-accent"></div>

                <div class="replying-info">
                  <span>Replying to {{ getProfileName(replyingTo.profiles) }}</span>
                  <p>{{ getMessageText(replyingTo) }}</p>
                </div>

                <button type="button" aria-label="Cancel reply" @click="cancelReply">
                  <X :size="17" />
                </button>
              </div>

              <div class="composer-row">
                <input
                  v-model="messageText"
                  type="text"
                  placeholder="Write a message..."
                  autocomplete="off"
                  maxlength="2000"
                  @focus="closeMessageMenu"
                  @input="messageSendError = ''"
                />

                <button
                  type="submit"
                  class="send-button"
                  :disabled="isMessageEmpty || sendingMessage"
                  aria-label="Send message"
                >
                  <LoaderCircle v-if="sendingMessage" class="spin" :size="18" />
                  <Send v-else :size="18" />
                </button>
              </div>
              <p v-if="messageSendError" class="message-send-error" role="alert">{{ messageSendError }}</p>
            </form>
          </div>
        </section>

        <!-- BOOKS -->
        <section v-else-if="activeTab === 'books'" class="section-content books-section">
          <div class="books-header">
            <div>
              <span class="section-kicker">Library</span>
              <h2>Books</h2>
              <p>Resources shared with this Book Club.</p>
            </div>

            <span v-if="books.length" class="books-count">{{ books.length }}</span>
          </div>

          <div v-if="canManageBooks && isMember" class="book-manager">
            <div class="book-search-row">
              <div class="book-search">
                <Search :size="17" />
                <input
                  v-model="bookSearch"
                  type="text"
                  placeholder="Search Follia Library..."
                  autocomplete="off"
                  @keyup.enter="searchBooks"
                />

                <button
                  v-if="bookSearch"
                  type="button"
                  class="clear-search"
                  aria-label="Clear search"
                  @click="clearBookSearch"
                >
                  <X :size="15" />
                </button>
              </div>

              <button
                type="button"
                class="book-search-button"
                :disabled="searchingBooks"
                @click="searchBooks"
              >
                <LoaderCircle v-if="searchingBooks" class="spin" :size="16" />
                <Search v-else :size="16" />
                <span>{{ searchingBooks ? 'Searching...' : 'Search' }}</span>
              </button>
            </div>

            <p v-if="bookManagerError" class="book-manager-message error" role="alert">{{ bookManagerError }}</p>
            <p v-else-if="bookManagerNotice" class="book-manager-message" role="status">{{ bookManagerNotice }}</p>

            <div v-if="bookSearchResults.length" class="search-results">
              <div class="search-results-title">Follia Library</div>

              <article
                v-for="resource in bookSearchResults"
                :key="resource.id"
                class="library-search-result"
              >
                <div class="library-result-cover">
                  <img
                    v-if="getResourceCoverUrl(resource) && !isResourceCoverFailed(resource.id)"
                    :src="getResourceCoverUrl(resource)"
                    :alt="resource.title"
                    @error="markResourceCoverFailed(resource.id)"
                  />
                  <BookOpen v-else :size="21" />
                </div>

                <div class="library-result-info">
                  <h3>{{ resource.title }}</h3>
                  <p>
                    {{ resource.profiles?.display_name || resource.profiles?.username || 'Unknown author' }}
                  </p>
                  <span v-if="resource.category">{{ resource.category }}</span>
                </div>

                <button
                  type="button"
                  class="add-book-button"
                  :disabled="Boolean(addingBookId) || isBookAlreadyAdded(resource.id)"
                  @click="addBook(resource)"
                >
                  <LoaderCircle v-if="addingBookId === resource.id" class="spin" :size="14" />
                  <Check v-else-if="isBookAlreadyAdded(resource.id)" :size="14" />
                  <Plus v-else :size="14" />
                  <span>
                    {{
                      addingBookId === resource.id
                        ? 'Adding'
                        : isBookAlreadyAdded(resource.id)
                          ? 'Added'
                          : 'Add'
                    }}
                  </span>
                </button>
              </article>
            </div>

            <div v-else-if="hasSearchedBooks && !searchingBooks" class="search-empty">
              <Search :size="20" />
              <p>No published resources found.</p>
            </div>
          </div>

          <div v-if="!isMember" class="books-member-card">
            <div class="books-member-icon">
              <Lock :size="21" />
            </div>
            <div>
              <h3>Join to view books</h3>
              <p>Join this Book Club to access its shared library.</p>
            </div>
            <button type="button" class="join-books-button" @click="joinClub">Join</button>
          </div>

          <div v-else-if="booksLoading" class="books-loading">
            <LoaderCircle class="spin" :size="22" />
            <span>Loading books...</span>
          </div>

          <div v-else-if="books.length === 0" class="empty-section books-empty">
            <div class="empty-section-icon">
              <BookOpen :size="27" />
            </div>
            <h2>No books yet</h2>
            <p>
              {{
                canManageBooks
                  ? 'Search the Follia Library and add books to this club.'
                  : 'Books shared with this Book Club will appear here.'
              }}
            </p>
          </div>

          <div v-else class="club-books">
            <article v-for="book in books" :key="book.id" class="club-book-card">
              <div class="club-book-cover">
                <img
                  v-if="getResourceCoverUrl(book.resources) && !isResourceCoverFailed(book.resource_id)"
                  :src="getResourceCoverUrl(book.resources)"
                  :alt="book.resources?.title || 'Resource cover'"
                  @error="markResourceCoverFailed(book.resource_id)"
                />
                <BookOpen v-else :size="25" />
              </div>

              <div class="club-book-info">
                <h3>{{ book.resources?.title || 'Untitled resource' }}</h3>
                <p>
                  {{
                    book.resources?.profiles?.display_name ||
                    book.resources?.profiles?.username ||
                    'Unknown author'
                  }}
                </p>
                <span v-if="book.resources?.category">{{ book.resources.category }}</span>
              </div>

              <div class="club-book-actions">
                <button
                  type="button"
                  class="download-book-button"
                  :disabled="downloadingBookId === book.resource_id"
                  @click="downloadBook(book)"
                >
                  <LoaderCircle
                    v-if="downloadingBookId === book.resource_id"
                    class="spin"
                    :size="16"
                  />
                  <Download v-else :size="16" />
                  <span>
                    {{ downloadingBookId === book.resource_id ? 'Preparing...' : 'Download' }}
                  </span>
                </button>

                <button
                  v-if="canManageBooks"
                  type="button"
                  class="remove-book-button"
                  @click="removeBook(book.resource_id)"
                >
                  <Trash2 :size="16" />
                  <span>Remove</span>
                </button>
              </div>
            </article>
          </div>
        </section>

        <!-- ABOUT -->
        <section v-else-if="activeTab === 'about'" class="section-content">
          <div class="about-card">
            <div class="about-section">
              <div class="about-heading">
                <div>
                  <span class="section-kicker">Book Club</span>
                  <h2>About this club</h2>
                </div>
              </div>

              <p v-if="club.description">{{ club.description }}</p>
              <p v-else class="muted-text">No description has been added yet.</p>
            </div>

            <div class="about-section">
              <div class="members-heading">
                <div>
                  <span class="section-kicker">Community</span>
                  <h2>Members</h2>
                </div>
                <span class="member-count">{{ club.book_club_members?.length || 0 }}</span>
              </div>

              <div class="members-list">
                <div
                  v-for="member in club.book_club_members || []"
                  :key="member.id"
                  class="member-row"
                >
                  <div class="member-avatar">
                    <UserAvatar :src="member.profiles?.avatar_url || member.profiles?.avatar" :alt="getProfileName(member.profiles)" :icon-size="16" />
                  </div>

                  <div class="member-info">
                    <strong>{{ getProfileName(member.profiles) }}</strong>
                    <span v-if="member.role === 'owner'">Owner</span>
                    <span v-else-if="member.role === 'admin'">Admin</span>
                  </div>

                  <div v-if="isOwner && member.user_id !== currentUserId" class="member-actions">
                    <button
                      v-if="member.role !== 'admin'"
                      type="button"
                      title="Promote to admin"
                      @click="manageMember(member, 'promote')"
                    >
                      <ShieldCheck :size="15" />
                    </button>

                    <button
                      v-else
                      type="button"
                      title="Remove admin"
                      @click="manageMember(member, 'demote')"
                    >
                      <ShieldOff :size="15" />
                    </button>

                    <button type="button" title="Remove member" @click="manageMember(member, 'remove')">
                      <UserMinus :size="15" />
                    </button>
                  </div>
                </div>
              </div>

              <button
                v-if="isMember && !isOwner"
                type="button"
                class="leave-club-button"
                @click="leaveClub"
              >
                <LogOut :size="16" />
                <span>Leave Book Club</span>
              </button>
            </div>
          </div>
        </section>

        <!-- OWNER EDIT MODAL -->
        <div v-if="showEditModal && isOwner" class="modal-backdrop" @click.self="showEditModal = false">
          <div class="edit-modal">
            <div class="modal-header">
              <div>
                <span class="section-kicker">Settings</span>
                <h2>Edit Book Club</h2>
              </div>
              <button type="button" aria-label="Close settings" @click="closeEditModal">
                <X :size="20" />
              </button>
            </div>

            <form @submit.prevent="saveClubChanges">
              <div class="edit-avatar">
                <img
                  v-if="editAvatarPreview && !editAvatarFailed"
                  :src="resolveMediaUrl(editAvatarPreview)"
                  alt="Book Club avatar"
                  @error="editAvatarFailed = true"
                />
                <div v-else class="edit-avatar-placeholder">
                  <Users :size="28" />
                </div>

                <label class="avatar-upload">
                  Change image
                  <input type="file" accept="image/*" @change="handleAvatarChange" />
                </label>
              </div>

              <label class="form-field">
                <span>Club name</span>
                <input v-model="editName" type="text" required maxlength="120" />
              </label>

              <label class="form-field">
                <span>Description</span>
                <textarea v-model="editDescription" rows="4" maxlength="500"></textarea>
              </label>

              <div class="modal-actions">
                <button type="button" class="cancel-button" @click="closeEditModal">Cancel</button>

                <button type="submit" class="save-button" :disabled="savingClub">
                  <LoaderCircle v-if="savingClub" class="spin" :size="17" />
                  <span v-else>Save changes</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </template>
    </div>
  </MainLayout>
</template>

<script setup>
import { resolveMediaUrl } from '../utils/media'

import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

import {
  ArrowLeft,
  BookOpen,
  Check,
  Copy,
  Download,
  LoaderCircle,
  Lock,
  LogOut,
  MessageCircle,
  MoreHorizontal,
  Pin,
  Plus,
  Reply,
  Search,
  Send,
  Share2,
  ShieldCheck,
  ShieldOff,
  Trash2,
  UserMinus,
  Users,
  X,
} from 'lucide-vue-next'

import {
  getBookClub,
  getBookClubMessages,
  joinBookClub,
  leaveBookClub,
  sendBookClubMessage,
  deleteBookClubMessage,
  toggleBookClubMessagePin,
  manageBookClubMember,
  updateBookClub,
  subscribeToBookClubMessages,
  isBookClubMember,
  getBookClubBooks,
  searchBookClubResources,
  addBookToBookClub,
  removeBookFromBookClub,
} from '../services/bookClubService'

import { getCurrentUserId } from '../services/profileService'
import UserAvatar from '../components/UserAvatar.vue'

const route = useRoute()
const router = useRouter()

function getResourceCoverUrl(resource) {
  if (!resource) return null
  return resolveMediaUrl(resource.cover_url || resource.cover)
}

/*
|--------------------------------------------------------------------------
| State
|--------------------------------------------------------------------------
*/

const loading = ref(true)
const messagesLoading = ref(true)
const error = ref('')

const club = ref(null)
const messages = ref([])

/*
|--------------------------------------------------------------------------
| Image error fallbacks
|--------------------------------------------------------------------------
*/

const clubAvatarFailed = ref(false)
const editAvatarFailed = ref(false)
const failedResourceCoverIds = ref(new Set())

const clubAvatarUrl = computed(() =>
  resolveMediaUrl(club.value?.avatar_url || club.value?.avatar),
)

function isResourceCoverFailed(id) {
  return failedResourceCoverIds.value.has(id)
}

function markResourceCoverFailed(id) {
  failedResourceCoverIds.value = new Set([...failedResourceCoverIds.value, id])
}

/*
|--------------------------------------------------------------------------
| User / membership
|--------------------------------------------------------------------------
*/

const currentUserId = ref(null)
const isMember = ref(false)
const isOwner = ref(false)

/*
|--------------------------------------------------------------------------
| Tabs
|--------------------------------------------------------------------------
*/

const activeTab = ref('chat')

/*
|--------------------------------------------------------------------------
| Messages
|--------------------------------------------------------------------------
*/

const messageText = ref('')
const sendingMessage = ref(false)
const messageSendError = ref('')
const replyingTo = ref(null)
const messagesContainer = ref(null)
const activeMessageMenu = ref(null)
const messageMenu = ref(null)

const messageMenuStyle = ref({
  top: '0px',
  left: '0px',
})

/*
|--------------------------------------------------------------------------
| Edit club
|--------------------------------------------------------------------------
*/

const showEditModal = ref(false)
const savingClub = ref(false)
const editName = ref('')
const editDescription = ref('')
const editAvatarFile = ref(null)
const editAvatarPreview = ref('')

/*
|--------------------------------------------------------------------------
| Books
|--------------------------------------------------------------------------
*/

const books = ref([])
const booksLoading = ref(false)
const bookSearch = ref('')
const bookSearchResults = ref([])
const searchingBooks = ref(false)
const addingBookId = ref(null)
const downloadingBookId = ref(null)
const hasSearchedBooks = ref(false)
const bookManagerError = ref('')
const bookManagerNotice = ref('')

let realtimeChannel = null

/*
|--------------------------------------------------------------------------
| Computed
|--------------------------------------------------------------------------
*/

const isMessageEmpty = computed(() => {
  const value = typeof messageText.value === 'string' ? messageText.value : ''
  return value.trim().length === 0
})

const currentMember = computed(() => {
  if (!club.value?.book_club_members || !currentUserId.value) return null

  return club.value.book_club_members.find(
    (member) => member.user_id === currentUserId.value,
  )
})

const isAdmin = computed(() => currentMember.value?.role === 'admin')
const canManageBooks = computed(() => isOwner.value || isAdmin.value)

/*
|--------------------------------------------------------------------------
| Load club
|--------------------------------------------------------------------------
*/

async function loadClub() {
  loading.value = true
  error.value = ''
  clubAvatarFailed.value = false

  try {
    currentUserId.value = await getCurrentUserId()
    club.value = await getBookClub(route.params.id)

    isOwner.value = currentUserId.value === club.value.owner_id

    if (currentUserId.value) {
      isMember.value = Boolean(await isBookClubMember(route.params.id))
    } else {
      isMember.value = false
    }

    editName.value = club.value.name || ''
    editDescription.value = club.value.description || ''
    editAvatarPreview.value = club.value.avatar_url || club.value.avatar || ''
    editAvatarFailed.value = false
  } catch (err) {
    console.error('Load book club error:', err)
    error.value = err?.message || 'Unable to load this Book Club.'
  } finally {
    loading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Load messages
|--------------------------------------------------------------------------
*/

async function loadMessages(shouldScroll = false) {
  if (!isMember.value) {
    messages.value = []
    messagesLoading.value = false
    return
  }

  messagesLoading.value = true

  try {
    messages.value = await getBookClubMessages(route.params.id)

    if (shouldScroll) {
      await scrollToBottom(true)
    }
  } catch (err) {
    console.error('Load messages error:', err)
  } finally {
    messagesLoading.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Books
|--------------------------------------------------------------------------
*/

async function loadBooks() {
  if (!route.params.id || !isMember.value) {
    books.value = []
    return
  }

  booksLoading.value = true

  try {
    books.value = await getBookClubBooks(route.params.id)
  } catch (err) {
    console.error('Load Book Club books error:', err)
    books.value = []
  } finally {
    booksLoading.value = false
  }
}

async function searchBooks() {
  if (!canManageBooks.value || !isMember.value) return

  searchingBooks.value = true
  bookManagerError.value = ''
  bookManagerNotice.value = ''
  hasSearchedBooks.value = true
  failedResourceCoverIds.value = new Set()

  try {
    bookSearchResults.value = await searchBookClubResources(bookSearch.value)
  } catch (err) {
    console.error('Search Book Club resources error:', err)
    bookSearchResults.value = []
    window.alert(err?.message || 'Unable to search the Follia Library.')
  } finally {
    searchingBooks.value = false
  }
}

function isBookAlreadyAdded(resourceId) {
  return books.value.some((book) => book.resource_id === resourceId)
}

async function addBook(resource) {
  if (!canManageBooks.value || !isMember.value || !resource?.id || addingBookId.value) return
  if (isBookAlreadyAdded(resource.id)) return

  addingBookId.value = resource.id
  bookManagerError.value = ''
  bookManagerNotice.value = ''

  try {
    const added = await addBookToBookClub(route.params.id, resource.id)
    if (!isBookAlreadyAdded(resource.id)) books.value = [...books.value, added]

    bookSearchResults.value = bookSearchResults.value.filter(
      (item) => item.id !== resource.id,
    )
    bookManagerNotice.value = added?.created ? 'Book added to this Book Club.' : 'This book is already in the Book Club.'
  } catch (err) {
    console.error('Add Book Club book error:', err)
    bookManagerError.value = err?.message || 'Unable to add this book.'
  } finally {
    addingBookId.value = null
  }
}

async function removeBook(resourceId) {
  if (!canManageBooks.value || !isMember.value || !resourceId) return

  const confirmed = window.confirm('Remove this book from the Book Club?')
  if (!confirmed) return

  try {
    await removeBookFromBookClub(route.params.id, resourceId)

    // Remove only the club relationship; keep the library resource.
    books.value = books.value.filter((book) => book.resource_id !== resourceId)
  } catch (err) {
    console.error('Remove Book Club book error:', err)
    window.alert(err?.message || 'Unable to remove this book.')
  }
}

async function downloadBook(book) {
  const resource = book?.resources
  const fileUrl = resolveMediaUrl(resource?.file_url || resource?.file)

  if (!fileUrl) {
    window.alert('This resource does not have a downloadable file.')
    return
  }

  downloadingBookId.value = book.resource_id || resource?.id || null

  try {
    const link = document.createElement('a')
    link.href = fileUrl
    link.target = '_blank'
    link.rel = 'noopener noreferrer'

    if (resource?.file_name) {
      link.download = resource.file_name
    }

    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (err) {
    console.error('Download Book Club book error:', err)
    window.alert(err?.message || 'Unable to download this resource.')
  } finally {
    downloadingBookId.value = null
  }
}

/*
|--------------------------------------------------------------------------
| Join
|--------------------------------------------------------------------------
*/

async function joinClub() {
  try {
    await joinBookClub(route.params.id)

    isMember.value = true

    await loadClub()
    await loadMessages(true)
    await loadBooks()

    if (!realtimeChannel) {
      await subscribeToMessages()
    }
  } catch (err) {
    console.error('Join club error:', err)
    window.alert(err?.message || 'Unable to join this club.')
  }
}

/*
|--------------------------------------------------------------------------
| Leave
|--------------------------------------------------------------------------
*/

async function leaveClub() {
  if (isOwner.value) return

  const confirmed = window.confirm('Leave this Book Club?')
  if (!confirmed) return

  try {
    await leaveBookClub(route.params.id)

    isMember.value = false
    messages.value = []
    books.value = []
    replyingTo.value = null
    messageText.value = ''

    closeMessageMenu()

    if (realtimeChannel) {
      await realtimeChannel.unsubscribe()
      realtimeChannel = null
    }

    await loadClub()
    activeTab.value = 'about'
  } catch (err) {
    console.error('Leave club error:', err)
    window.alert(err?.message || 'Unable to leave this Book Club.')
  }
}

/*
|--------------------------------------------------------------------------
| Send message
|--------------------------------------------------------------------------
*/

async function sendMessage() {
  const value = typeof messageText.value === 'string' ? messageText.value : ''
  const content = value.trim()

  if (!content || sendingMessage.value) return

  sendingMessage.value = true
  messageSendError.value = ''

  try {
    const replyToId = replyingTo.value?.id || null

    const sentMessage = await sendBookClubMessage({
      bookClubId: route.params.id,
      content,
      replyToId,
    })

    upsertMessage(sentMessage)

    messageText.value = ''
    replyingTo.value = null
    closeMessageMenu()

    await nextTick()
    await scrollToBottom(true)
  } catch (err) {
    console.error('Send message error:', err)
    messageSendError.value = err?.message || 'Unable to send message. Try again.'
  } finally {
    sendingMessage.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Reply
|--------------------------------------------------------------------------
*/

function startReply(message) {
  replyingTo.value = message
  messageText.value = ''
  closeMessageMenu()

  nextTick(() => {
    document.querySelector('.composer-row input')?.focus()
  })
}

function cancelReply() {
  replyingTo.value = null
}

/*
|--------------------------------------------------------------------------
| Message menu
|--------------------------------------------------------------------------
*/

function openMessageMenu(event, message) {
  event.stopPropagation()

  const rect = event.currentTarget?.getBoundingClientRect?.()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const menuWidth = 170
  const menuHeight = 170

  let left = rect ? rect.left : 20
  let top = rect ? rect.bottom + 6 : 80

  if (left + menuWidth > viewportWidth - 12) {
    left = viewportWidth - menuWidth - 12
  }

  if (top + menuHeight > viewportHeight - 12) {
    top = (rect?.top || 100) - menuHeight - 6
  }

  left = Math.max(12, left)
  top = Math.max(12, top)

  activeMessageMenu.value = { message }
  messageMenuStyle.value = {
    top: `${top}px`,
    left: `${left}px`,
  }
}

function closeMessageMenu() {
  activeMessageMenu.value = null
}

async function handleMessageAction(action) {
  const message = activeMessageMenu.value?.message
  if (!message) return

  closeMessageMenu()

  if (action === 'reply') {
    startReply(message)
    return
  }

  if (action === 'copy') {
    await copyMessage(getMessageText(message))
    return
  }

  if (action === 'pin') {
    await togglePin(message)
    return
  }

  if (action === 'delete') {
    await deleteMessage(message.id)
  }
}

/*
|--------------------------------------------------------------------------
| Copy
|--------------------------------------------------------------------------
*/

async function copyMessage(content) {
  const value = typeof content === 'string' ? content : ''
  if (!value) return

  try {
    await navigator.clipboard.writeText(value)
    window.alert('Message copied.')
  } catch (err) {
    console.error('Copy message error:', err)
  }
}

/*
|--------------------------------------------------------------------------
| Delete
|--------------------------------------------------------------------------
*/

async function deleteMessage(messageId) {
  const confirmed = window.confirm('Delete this message?')
  if (!confirmed) return

  try {
    await deleteBookClubMessage(messageId, route.params.id)
    messages.value = messages.value.filter((message) => message.id !== messageId)
  } catch (err) {
    console.error('Delete message error:', err)
    window.alert(err?.message || 'Unable to delete message.')
  }
}

/*
|--------------------------------------------------------------------------
| Pin
|--------------------------------------------------------------------------
*/

async function togglePin(message) {
  try {
    await toggleBookClubMessagePin({
      messageId: message.id,
      bookClubId: route.params.id,
      isPinned: !message.is_pinned,
    })

    await loadMessages(false)
  } catch (err) {
    console.error('Toggle pin error:', err)
    window.alert(err?.message || 'Unable to update pin.')
  }
}

/*
|--------------------------------------------------------------------------
| Share
|--------------------------------------------------------------------------
*/

async function shareBookClub() {
  if (!club.value) return

  const url = window.location.href

  try {
    if (navigator.share) {
      await navigator.share({
        title: `${club.value.name} — Follia Library`,
        text: `Join "${club.value.name}" on Follia Library.`,
        url,
      })
      return
    }

    await navigator.clipboard.writeText(url)
    window.alert('Book Club link copied.')
  } catch (err) {
    if (err?.name === 'AbortError') return

    try {
      await navigator.clipboard.writeText(url)
      window.alert('Book Club link copied.')
    } catch (clipboardError) {
      console.error('Copy Book Club link error:', clipboardError)
      window.alert('Unable to share the Book Club link.')
    }
  }
}

/*
|--------------------------------------------------------------------------
| Members
|--------------------------------------------------------------------------
*/

async function manageMember(member, action) {
  let confirmed = true

  if (action === 'remove') {
    confirmed = window.confirm('Remove this member from the Book Club?')
  }

  if (!confirmed) return

  try {
    await manageBookClubMember({
      bookClubId: route.params.id,
      memberUserId: member.user_id,
      action,
    })

    await loadClub()
  } catch (err) {
    console.error('Manage member error:', err)
    window.alert(err?.message || 'Unable to update member.')
  }
}

/*
|--------------------------------------------------------------------------
| Edit modal / avatar
|--------------------------------------------------------------------------
*/

function openEditModal() {
  editName.value = club.value?.name || ''
  editDescription.value = club.value?.description || ''
  editAvatarFile.value = null
  editAvatarPreview.value = club.value?.avatar_url || club.value?.avatar || ''
  editAvatarFailed.value = false
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false

  if (editAvatarPreview.value?.startsWith('blob:')) {
    URL.revokeObjectURL(editAvatarPreview.value)
  }

  editAvatarFile.value = null
  editAvatarPreview.value = club.value?.avatar_url || club.value?.avatar || ''
  editAvatarFailed.value = false
}

function handleAvatarChange(event) {
  const file = event.target.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    window.alert('Please choose an image file.')
    event.target.value = ''
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    window.alert('Please choose an image smaller than 5 MB.')
    event.target.value = ''
    return
  }

  if (editAvatarPreview.value?.startsWith('blob:')) {
    URL.revokeObjectURL(editAvatarPreview.value)
  }

  editAvatarFile.value = file
  editAvatarPreview.value = URL.createObjectURL(file)
  editAvatarFailed.value = false
}

/*
|--------------------------------------------------------------------------
| Save club
|--------------------------------------------------------------------------
*/

async function saveClubChanges() {
  if (savingClub.value) return

  savingClub.value = true

  try {
    await updateBookClub({
      bookClubId: route.params.id,
      name: typeof editName.value === 'string' ? editName.value.trim() : '',
      description: typeof editDescription.value === 'string'
        ? editDescription.value.trim()
        : '',
      avatarFile: editAvatarFile.value,
    })

    showEditModal.value = false

    if (editAvatarPreview.value?.startsWith('blob:')) {
      URL.revokeObjectURL(editAvatarPreview.value)
    }

    editAvatarFile.value = null
    editAvatarPreview.value = ''
    await loadClub()
  } catch (err) {
    console.error('Update Book Club error:', err)
    window.alert(err?.message || 'Unable to update Book Club.')
  } finally {
    savingClub.value = false
  }
}

/*
|--------------------------------------------------------------------------
| Formatting
|--------------------------------------------------------------------------
*/

function getProfileName(profile) {
  if (!profile) return 'User'
  return profile.display_name || profile.username || 'User'
}

function getMessageText(message) {
  return typeof message?.content === 'string' ? message.content : ''
}

function getReplyText(message) {
  return typeof message?.reply_to?.content === 'string'
    ? message.reply_to.content
    : ''
}

function formatMessageTime(date) {
  if (!date) return ''

  const parsedDate = new Date(date)
  if (Number.isNaN(parsedDate.getTime())) return ''

  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  }).format(parsedDate)
}

function formatMessageDay(date) {
  if (!date) return ''

  const parsedDate = new Date(date)
  if (Number.isNaN(parsedDate.getTime())) return ''

  const now = new Date()
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const startOfMessage = new Date(
    parsedDate.getFullYear(),
    parsedDate.getMonth(),
    parsedDate.getDate(),
  )

  const diff = Math.floor((startOfToday - startOfMessage) / 86400000)

  if (diff === 0) return 'Today'
  if (diff === 1) return 'Yesterday'

  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    year: parsedDate.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  }).format(parsedDate)
}

function shouldShowDate(message, index) {
  if (index === 0) return true

  const previous = messages.value[index - 1]
  if (!previous) return true

  const currentDate = new Date(message.created_at)
  const previousDate = new Date(previous.created_at)

  return currentDate.toDateString() !== previousDate.toDateString()
}

/*
|--------------------------------------------------------------------------
| Scroll
|--------------------------------------------------------------------------
*/

async function scrollToBottom(smooth = false) {
  await nextTick()

  const container = messagesContainer.value
  if (!container) return

  container.scrollTo({
    top: container.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto',
  })
}

/*
|--------------------------------------------------------------------------
| Realtime
|--------------------------------------------------------------------------
*/

async function subscribeToMessages() {
  if (!route.params.id || realtimeChannel) return

  realtimeChannel = await subscribeToBookClubMessages(
    route.params.id,
    async (event) => {
      if (!event) return

      if (event.type === 'insert' && event.message) {
        const inserted = upsertMessage(event.message)
        if (inserted) await scrollToBottom(true)
      }

      if (event.type === 'delete' && event.message?.id) {
        messages.value = messages.value.filter(
          (message) => message.id !== event.message.id,
        )
      }

      if (event.type === 'update' && event.message) {
        const index = messages.value.findIndex(
          (message) => message.id === event.message.id,
        )

        if (index !== -1) {
          messages.value[index] = event.message
        }
      }
    },
  )
}

function upsertMessage(message) {
  if (!message?.id) return false
  const index = messages.value.findIndex((item) => item.id === message.id)
  if (index >= 0) {
    messages.value[index] = { ...messages.value[index], ...message }
    return false
  }
  messages.value.push(message)
  messages.value.sort((a, b) => {
    const timeDifference = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    return timeDifference || Number(a.id) - Number(b.id)
  })
  return true
}

/*
|--------------------------------------------------------------------------
| Watchers
|--------------------------------------------------------------------------
*/

watch(
  () => messages.value.length,
  async () => {
    if (activeTab.value === 'chat') {
      await scrollToBottom(false)
    }
  },
)

watch(activeTab, async (tab) => {
  if (tab === 'chat' && isMember.value) {
    await nextTick()
    await scrollToBottom(false)
  }

  if (tab === 'books' && isMember.value) {
    await loadBooks()
  }
})

/*
|--------------------------------------------------------------------------
| Lifecycle
|--------------------------------------------------------------------------
*/

onMounted(async () => {
  await loadClub()
  await loadMessages(true)

  if (isMember.value) {
    await loadBooks()
    await subscribeToMessages()
  }

  window.addEventListener('resize', closeMessageMenu)
})

onBeforeUnmount(async () => {
  if (realtimeChannel) {
    await realtimeChannel.unsubscribe()
  }

  if (editAvatarPreview.value?.startsWith('blob:')) {
    URL.revokeObjectURL(editAvatarPreview.value)
  }

  window.removeEventListener('resize', closeMessageMenu)
})

function clearBookSearch() {
  bookSearch.value = ''
  bookSearchResults.value = []
  hasSearchedBooks.value = false
}
</script>

<style scoped>
/* Page */
.book-club-page {
  width: 100%;
  min-height: 100%;
  padding-bottom: 90px;
}

.state-card {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.state-card p { margin: 0; }
.error-state { color: var(--text-main); }

.retry-button,
.join-button,
.save-button {
  border: 0;
  border-radius: 12px;
  padding: 10px 16px;
  background: var(--primary-bg);
  color: var(--primary-text);
  font-weight: 700;
  cursor: pointer;
}

/* Header */
.club-header {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 12px 15px;
  border-bottom: 1px solid var(--border-soft);
  background: var(--card-bg);
  backdrop-filter: blur(16px);
}

.header-icon-button {
  width: 39px;
  height: 39px;
  flex: 0 0 39px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--card-soft);
  color: var(--text-main);
  cursor: pointer;
  transition: background 0.15s ease, transform 0.15s ease;
}

.header-icon-button:hover { background: var(--icon-bg); }
.header-icon-button:active { transform: scale(0.96); }

.club-header-avatar {
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 50%;
  background: var(--icon-bg);
  color: var(--text-secondary);
}

.club-header-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.club-header-info { min-width: 0; flex: 1; }

.club-header-info h1 {
  margin: 0;
  overflow: hidden;
  color: var(--text-main);
  font-size: 15px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.club-header-info p {
  margin: 3px 0 0;
  color: var(--text-tertiary);
  font-size: 11px;
}

.club-header-actions { display: flex; align-items: center; gap: 5px; }

/* Tabs */
.club-tabs {
  position: sticky;
  top: 65px;
  z-index: 25;
  display: flex;
  gap: 4px;
  padding: 7px 12px;
  border-bottom: 1px solid var(--border-soft);
  background: var(--card-bg);
  backdrop-filter: blur(16px);
}

.club-tabs button {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 0;
  padding: 9px 10px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 750;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.club-tabs button.active {
  background: var(--primary-bg);
  color: var(--primary-text);
}

/* Join */
.join-card {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 18px 15px;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--card-bg);
}

.join-icon {
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 13px;
  background: var(--icon-bg);
  color: var(--text-main);
}

.join-content { min-width: 0; flex: 1; }
.join-content h2 { margin: 0; color: var(--text-main); font-size: 14px; font-weight: 800; }
.join-content p { margin: 4px 0 0; color: var(--text-secondary); font-size: 12px; line-height: 1.5; }
.join-button { flex-shrink: 0; }

/* Chat shell */
.chat-section { width: 100%; }

.chat-shell {
  position: relative;
  height: min(680px, max(180px, calc(100dvh - 260px)));
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background:
    radial-gradient(circle at 10% 15%, color-mix(in srgb, var(--primary-bg) 4%, transparent), transparent 30%),
    var(--card-bg);
}

/* Messages */
.messages-container {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-y;
  scrollbar-width: thin;
}

.messages-list {
  width: min(100%, 920px);
  margin: 0 auto;
  padding: 18px 14px 24px;
}

.message-group { width: 100%; }

.message-row {
  display: flex;
  align-items: flex-end;
  gap: 7px;
  margin: 2px 0 5px;
}

.own-row { justify-content: flex-end; }

/* Date divider */
.date-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 17px 0 12px;
}

.date-divider span {
  padding: 5px 10px;
  border: 1px solid var(--border-soft);
  border-radius: 20px;
  background: var(--card-soft);
  color: var(--text-tertiary);
  font-size: 9px;
  font-weight: 750;
}

/* Message avatars */
.message-avatar-link {
  width: 29px;
  height: 29px;
  flex: 0 0 29px;
  align-self: flex-end;
  text-decoration: none;
}

.message-avatar,
.message-avatar-link img {
  width: 29px;
  height: 29px;
  border-radius: 50%;
}

.message-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--icon-bg);
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 800;
}

.message-avatar-link img { display: block; object-fit: cover; }

/* Message main */
.message-main { min-width: 0; max-width: min(76%, 590px); }

.own-main {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.sender-name {
  margin: 0 0 3px 7px;
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 750;
}

.message-line { display: flex; align-items: flex-end; gap: 2px; }
.own-main .message-line { justify-content: flex-end; }

/* Message bubble */
.message-bubble {
  min-width: 0;
  padding: 8px 10px 5px;
  border: 1px solid var(--border-soft);
  border-radius: 5px 15px 15px 15px;
  background: var(--card-soft);
  color: var(--text-main);
  box-shadow: 0 1px 2px var(--shadow-color);
}

.own-bubble {
  border-color: transparent;
  border-radius: 15px 5px 15px 15px;
  background: var(--primary-bg);
  color: var(--primary-text);
}

.message-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.48;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

/* Message meta */
.message-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 3px;
  min-height: 13px;
  margin-top: 2px;
  color: var(--text-tertiary);
  font-size: 9px;
}

.own-bubble .message-meta { color: color-mix(in srgb, var(--primary-text) 70%, transparent); }
.message-pin { opacity: 0.85; }

/* Reply inside message */
.message-reply {
  margin-bottom: 6px;
  padding: 5px 7px;
  border-left: 3px solid var(--text-main);
  border-radius: 5px;
  background: var(--card-bg);
}

.own-bubble .message-reply {
  border-left-color: var(--primary-text);
  background: rgba(255, 255, 255, 0.09);
}

.reply-name {
  overflow: hidden;
  color: var(--text-main);
  font-size: 9px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.own-bubble .reply-name { color: var(--primary-text); }

.reply-text {
  margin-top: 2px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 10px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.own-bubble .reply-text { color: color-mix(in srgb, var(--primary-text) 72%, transparent); }

/* Message actions */
.message-more {
  width: 27px;
  height: 27px;
  flex: 0 0 27px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease, background 0.15s ease;
}

.message-row:hover .message-more,
.message-more:focus-visible { opacity: 1; }

.message-more:hover { background: var(--icon-bg); color: var(--text-main); }

.pinned-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
  padding: 0 4px;
  border: 0;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 9px;
  cursor: pointer;
}

/* Message menu */
.message-menu {
  position: fixed;
  z-index: 100;
  width: 170px;
  padding: 5px;
  border: 1px solid var(--border-color);
  border-radius: 14px;
  background: var(--card-bg);
  box-shadow: 0 14px 40px var(--shadow-color);
  animation: menu-in 0.12s ease-out;
}

@keyframes menu-in {
  from { opacity: 0; transform: translateY(-4px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.message-menu button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 10px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: var(--text-main);
  font-size: 12px;
  font-weight: 650;
  text-align: left;
  cursor: pointer;
}

.message-menu button:hover { background: var(--card-soft); }
.danger-menu-item { color: #d64b4b !important; }

/* Empty/loading */
.chat-state {
  min-height: 50vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 9px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.chat-empty {
  min-height: 55vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  text-align: center;
}

.chat-empty-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  border-radius: 17px;
  background: var(--icon-bg);
  color: var(--text-secondary);
}

.chat-empty h3 { margin: 0; color: var(--text-main); font-size: 15px; }

.chat-empty p {
  max-width: 260px;
  margin: 6px 0 0;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.6;
}

/* Composer */
.message-composer {
  flex-shrink: 0;
  width: 100%;
  box-sizing: border-box;
  padding: 8px 12px max(12px,env(safe-area-inset-bottom));
  border-top: 1px solid var(--border-soft);
  background: color-mix(in srgb, var(--card-bg) 95%, transparent);
  backdrop-filter: blur(16px);
}
.message-send-error { width:min(100%,920px); margin:7px auto 0; padding:0 8px; color:#a33b30; font-size:11px; }

.composer-row {
  width: min(100%, 920px);
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 5px 5px 13px;
  border: 1px solid var(--border-color);
  border-radius: 24px;
  background: var(--input-bg);
  box-shadow: 0 3px 14px var(--shadow-color);
}

.composer-row input {
  min-width: 0;
  flex: 1;
  height: 35px;
  padding: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text-main);
  font: inherit;
  font-size: 13px;
}

.composer-row input::placeholder { color: var(--text-tertiary); }

.send-button {
  width: 35px;
  height: 35px;
  flex: 0 0 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  background: var(--primary-bg);
  color: var(--primary-text);
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.send-button:hover:not(:disabled) { transform: scale(1.04); }
.send-button:disabled { opacity: 0.4; cursor: not-allowed; }

/* Replying bar */
.replying-bar {
  width: min(100%, 920px);
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 auto 7px;
  padding: 7px 9px;
  border: 1px solid var(--border-soft);
  border-radius: 11px;
  background: var(--card-soft);
}

.replying-accent {
  width: 3px;
  height: 32px;
  flex: 0 0 3px;
  border-radius: 4px;
  background: var(--primary-bg);
}

.replying-info { min-width: 0; flex: 1; }

.replying-info span {
  display: block;
  overflow: hidden;
  color: var(--text-main);
  font-size: 10px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.replying-info p {
  margin: 2px 0 0;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.replying-bar > button {
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
}

.replying-bar > button:hover { background: var(--icon-bg); color: var(--text-main); }

/* Books / About */
.section-content { padding: 16px; }

.books-section {
  width: min(100%, 900px);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.books-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }

.books-header h2 { margin: 0; color: var(--text-main); font-size: 19px; font-weight: 800; }
.books-header p { margin: 5px 0 0; color: var(--text-tertiary); font-size: 12px; }

.books-count {
  min-width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: var(--icon-bg);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 800;
}

.book-manager-message {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 11px;
  background: var(--card-soft);
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.5;
}

.book-manager-message.error {
  border-color: color-mix(in srgb, #b84b40 25%, var(--border-color));
  color: #a33b30;
}

/* Book manager */
.book-manager { display: flex; flex-direction: column; gap: 10px; }
.book-search-row { display: flex; gap: 9px; }

.book-search {
  min-width: 0;
  flex: 1;
  height: 45px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 13px;
  border: 1px solid var(--border-color);
  border-radius: 13px;
  background: var(--input-bg);
  color: var(--text-tertiary);
}

.book-search input {
  min-width: 0;
  flex: 1;
  height: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text-main);
  font: inherit;
  font-size: 12px;
}

.book-search input::placeholder { color: var(--text-tertiary); }

.clear-search {
  width: 25px;
  height: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
}

.clear-search:hover { background: var(--icon-bg); color: var(--text-main); }

.book-search-button {
  min-width: 90px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 14px;
  border: 0;
  border-radius: 13px;
  background: var(--primary-bg);
  color: var(--primary-text);
  font-size: 12px;
  font-weight: 750;
  cursor: pointer;
}

.book-search-button:disabled { opacity: 0.55; cursor: not-allowed; }

/* Search results */
.search-results {
  display: flex;
  flex-direction: column;
  padding: 9px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: var(--card-bg);
}

.search-results-title {
  padding: 5px 6px 9px;
  color: var(--text-tertiary);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.library-search-result {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 9px;
  border-radius: 12px;
  transition: background 0.15s ease;
}

.library-search-result:hover { background: var(--card-soft); }

.library-result-cover {
  width: 45px;
  height: 60px;
  flex: 0 0 45px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 8px;
  background: var(--icon-bg);
  color: var(--text-tertiary);
}

.library-result-cover img { width: 100%; height: 100%; object-fit: cover; }

.library-result-info { min-width: 0; flex: 1; }

.library-result-info h3 {
  margin: 0;
  overflow: hidden;
  color: var(--text-main);
  font-size: 12px;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.library-result-info p {
  margin: 4px 0 3px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.library-result-info span { color: var(--text-tertiary); font-size: 9px; }

.add-book-button {
  min-width: 66px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 8px 10px;
  border: 0;
  border-radius: 9px;
  background: var(--primary-bg);
  color: var(--primary-text);
  font-size: 10px;
  font-weight: 750;
  cursor: pointer;
}

.add-book-button:disabled { opacity: 0.55; cursor: not-allowed; }

.search-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 25px;
  border: 1px dashed var(--border-color);
  border-radius: 15px;
  color: var(--text-tertiary);
  text-align: center;
}

.search-empty p { margin: 0; font-size: 11px; }

/* Books list */
.club-books {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.club-book-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 13px;
  border: 1px solid var(--border-color);
  border-radius: 17px;
  background: var(--card-bg);
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.club-book-card:hover { transform: translateY(-1px); }

.club-book-cover {
  width: 100%;
  height: 190px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 12px;
  background: var(--icon-bg);
  color: var(--text-tertiary);
}

.club-book-cover img { width: 100%; height: 100%; object-fit: cover; }
.club-book-info { min-width: 0; }

.club-book-info h3 {
  margin: 0;
  overflow: hidden;
  color: var(--text-main);
  font-size: 14px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.club-book-info p {
  margin: 5px 0 3px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.club-book-info span { color: var(--text-tertiary); font-size: 9px; }
.club-book-actions { display: flex; gap: 7px; }

.download-book-button,
.remove-book-button {
  flex: 1;
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 750;
  cursor: pointer;
}

.download-book-button { border: 0; background: var(--primary-bg); color: var(--primary-text); }
.download-book-button:disabled { opacity: 0.55; cursor: not-allowed; }

.remove-book-button {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
}

.remove-book-button:hover { background: var(--card-soft); color: #d64b4b; }

.books-loading {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 9px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.books-empty { min-height: 300px; }

/* Join to view books */
.books-member-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: var(--card-bg);
}

.books-member-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--icon-bg);
  color: var(--text-secondary);
}

.books-member-card > div:nth-child(2) { min-width: 0; flex: 1; }
.books-member-card h3 { margin: 0; color: var(--text-main); font-size: 13px; }
.books-member-card p { margin: 4px 0 0; color: var(--text-tertiary); font-size: 11px; line-height: 1.5; }

.join-books-button {
  flex-shrink: 0;
  padding: 9px 13px;
  border: 0;
  border-radius: 10px;
  background: var(--primary-bg);
  color: var(--primary-text);
  font-size: 11px;
  font-weight: 750;
  cursor: pointer;
}

/* About */
.empty-section {
  min-height: 55vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-section-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  border-radius: 18px;
  background: var(--icon-bg);
  color: var(--text-secondary);
}

.empty-section h2 { margin: 0; color: var(--text-main); font-size: 16px; }

.empty-section p {
  max-width: 280px;
  margin: 7px 0 0;
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.6;
}

.about-card {
  width: min(100%, 760px);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.about-section {
  padding: 18px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--card-bg);
}

.about-heading,
.members-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.section-kicker {
  display: block;
  margin-bottom: 3px;
  color: var(--text-tertiary);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.about-section h2 { margin: 0; color: var(--text-main); font-size: 15px; font-weight: 800; }

.about-section > p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.7;
}

.muted-text { color: var(--text-tertiary) !important; }

.member-count {
  min-width: 27px;
  height: 27px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  background: var(--icon-bg);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 800;
}

.members-list { display: flex; flex-direction: column; }

.member-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 0;
  border-bottom: 1px solid var(--border-soft);
}

.member-row:last-child { border-bottom: 0; }

.member-avatar {
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 50%;
  background: var(--icon-bg);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 800;
}

.member-avatar img { width: 100%; height: 100%; object-fit: cover; }
.member-info { min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 2px; }

.member-info strong {
  overflow: hidden;
  color: var(--text-main);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-info span { color: var(--text-tertiary); font-size: 10px; }
.member-actions { display: flex; align-items: center; gap: 3px; }

.member-actions button {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
}

.member-actions button:hover { background: var(--icon-bg); color: var(--text-main); }

/* Leave club */
.leave-club-button {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  margin-top: 18px;
  padding: 11px 14px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: transparent;
  color: #d64b4b;
  font-size: 12px;
  font-weight: 750;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.leave-club-button:hover {
  background: color-mix(in srgb, #d64b4b 7%, transparent);
  border-color: color-mix(in srgb, #d64b4b 25%, var(--border-color));
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 15px;
  background: rgba(0, 0, 0, 0.45);
}

.edit-modal {
  width: min(100%, 560px);
  max-height: 90vh;
  overflow-y: auto;
  padding: 20px;
  border-radius: 22px;
  background: var(--card-bg);
  box-shadow: 0 20px 60px var(--shadow-color);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}

.modal-header h2 { margin: 0; color: var(--text-main); font-size: 17px; }

.modal-header button {
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 10px;
  background: var(--card-soft);
  color: var(--text-secondary);
  cursor: pointer;
}

.edit-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.edit-avatar > img,
.edit-avatar-placeholder {
  width: 86px;
  height: 86px;
  border-radius: 22px;
}

.edit-avatar > img { object-fit: cover; }

.edit-avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--icon-bg);
  color: var(--text-secondary);
}

.avatar-upload {
  position: relative;
  color: var(--text-main);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.avatar-upload input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.form-field { display: flex; flex-direction: column; gap: 7px; margin-bottom: 16px; }
.form-field span { color: var(--text-main); font-size: 12px; font-weight: 800; }

.form-field input,
.form-field textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  outline: none;
  background: var(--input-bg);
  color: var(--text-main);
  font: inherit;
  font-size: 13px;
  resize: vertical;
}

.form-field input:focus,
.form-field textarea:focus { border-color: var(--text-main); }

.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }

.cancel-button {
  padding: 10px 15px;
  border: 1px solid var(--border-color);
  border-radius: 11px;
  background: transparent;
  color: var(--text-main);
  font-weight: 700;
  cursor: pointer;
}

.save-button { display: inline-flex; align-items: center; justify-content: center; gap: 7px; }
.save-button:disabled { opacity: 0.55; cursor: not-allowed; }

/* Animation */
.spin { animation: spin 0.9s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Mobile */
@media (max-width: 640px) {
  .club-books { grid-template-columns: 1fr 1fr; }
  .club-book-cover { height: 190px; }
  .book-search-row { flex-direction: column; }
  .book-search-button { width: 100%; height: 42px; }
}

@media (max-width: 520px) {
  .club-header { padding-left: 10px; padding-right: 10px; }
  .club-header-avatar { width: 40px; height: 40px; flex-basis: 40px; }
  .header-icon-button { width: 37px; height: 37px; flex-basis: 37px; }
  .club-tabs { top: 64px; }
  .chat-shell { height: min(680px, max(180px, calc(100dvh - 260px))); min-height: 0; }
  .messages-list { padding-left: 9px; padding-right: 9px; }
  .message-main { max-width: 83%; }
  .message-text { font-size: 12.5px; }
  .message-more { opacity: 1; }
  .message-menu { width: 160px; }
  .message-composer { padding-left: 8px; padding-right: 8px; padding-bottom: max(12px,env(safe-area-inset-bottom)); }
  .join-card { margin-left: 10px; margin-right: 10px; }
  .section-content { padding: 12px; }
  .books-section { gap: 14px; }
  .club-books { grid-template-columns: 1fr; }

  .club-book-card {
    display: grid;
    grid-template-columns: 72px minmax(0, 1fr);
    column-gap: 12px;
  }

  .club-book-cover { width: 72px; height: 100px; grid-row: span 2; }
  .club-book-info { align-self: center; }
  .club-book-actions { grid-column: 1 / -1; width: 100%; }
  .library-search-result { align-items: flex-start; }
  .add-book-button { flex-shrink: 0; }
  .books-member-card { align-items: flex-start; }
  .join-books-button { align-self: center; }
}

/* Desktop */
@media (min-width: 700px) {
  .club-header { padding-left: 24px; padding-right: 24px; }
  .club-tabs { padding-left: 24px; padding-right: 24px; }
  .messages-list { padding-top: 22px; padding-bottom: 28px; }
  .message-composer { padding-left: 20px; padding-right: 20px; padding-bottom: 16px; }
  .modal-backdrop { align-items: center; }
}
</style>
