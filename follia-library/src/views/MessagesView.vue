<template>
  <MainLayout>
    <section class="messages-page">
      <header class="messages-page-heading"><div><p>PRIVATE CONVERSATIONS</p><h1>Messages</h1></div><span class="secure-label"><LockKeyhole :size="14" /> Between you and them</span></header>
      <div class="messages-shell">
        <aside class="conversation-rail" :class="{ 'rail-hidden-mobile': currentConversation }">
          <div class="conversation-search"><Search :size="17" /><input v-model="search" placeholder="Find a conversation" aria-label="Find a conversation" /></div>
          <div v-if="listLoading" class="rail-state"><LoaderCircle :size="21" class="spin" />Loading messages…</div>
          <div v-else-if="listError" class="rail-state"><p>{{ listError }}</p><button @click="loadConversations">Try again</button></div>
          <div v-else-if="filteredConversations.length" class="conversation-list">
            <TransitionGroup name="conversation-row">
              <button v-for="conversation in filteredConversations" :key="conversation.id" class="conversation-item" :class="{ selected: currentConversation?.id === conversation.id, typing: typingConversations.has(conversation.id) }" @click="selectConversation(conversation)">
                <span class="conversation-avatar"><UserAvatar :src="conversation.participant.avatar_url" :alt="conversation.participant.display_name + ' profile picture'" :icon-size="20" /></span>
                <span class="conversation-copy"><strong>{{ conversation.participant.display_name || conversation.participant.username }}</strong><small :class="{ 'typing-label': typingConversations.has(conversation.id) }">{{ typingConversations.has(conversation.id) ? 'Typing…' : preview(conversation.last_message) }}</small></span>
                <span class="conversation-meta"><time>{{ formatTime(conversation.last_message_at) }}</time><b v-if="conversation.unread_count">{{ conversation.unread_count > 99 ? '99+' : conversation.unread_count }}</b></span>
              </button>
            </TransitionGroup>
          </div>
          <div v-else class="rail-empty"><span>✉</span><strong>No conversations yet</strong><p>Visit a creator’s profile and choose Message to start a private chat.</p><RouterLink to="/explore">Discover creators <ArrowUpRight :size="15" /></RouterLink></div>
        </aside>

        <section class="chat-panel" :class="{ 'chat-open-mobile': currentConversation }">
          <template v-if="currentConversation">
            <header class="chat-header">
              <button class="chat-back" type="button" aria-label="Back to conversations" @click="closeConversation"><ArrowLeft :size="19" /></button>
              <RouterLink :to="{ name:'publisher-detail', params:{ id:currentConversation.participant.id } }" class="chat-contact-avatar"><UserAvatar :src="currentConversation.participant.avatar_url" :alt="currentConversation.participant.display_name + ' profile picture'" :icon-size="19" /></RouterLink>
              <RouterLink :to="{ name:'publisher-detail', params:{ id:currentConversation.participant.id } }" class="chat-contact-name"><strong>{{ currentConversation.participant.display_name || currentConversation.participant.username }}</strong><small>{{ typingConversations.has(currentConversation.id) ? 'Typing…' : '@' + currentConversation.participant.username }}</small></RouterLink>
              <button v-if="currentConversation.blocked_by_me" class="unblock-control" @click="handleUnblock">Unblock</button>
              <button v-else-if="!currentConversation.blocked_you" class="block-control" @click="handleBlock"><Ban :size="15" /><span>Block</span></button>
              <span v-else class="blocked-label">You’re blocked</span>
            </header>

            <div ref="messageScroller" class="message-scroller">
              <button v-if="hasOlder" class="load-older" :disabled="olderLoading" @click="loadOlder">{{ olderLoading ? 'Loading…' : 'Load older messages' }}</button>
              <div v-if="messageLoading" class="thread-state"><LoaderCircle :size="22" class="spin" /><span>Loading conversation…</span></div>
              <div v-else-if="!messages.length" class="thread-empty"><span>✦</span><strong>Start the conversation</strong><p>Your first message creates a private conversation with {{ currentConversation.participant.display_name || 'this creator' }}.</p></div>
              <div v-else class="message-list">
                <article v-for="message in messages" :key="message.id || message.client_id" class="message-line" :class="{ mine: message.sender_id === currentUserId, failed: message.failed }">
                  <div class="message-bubble">
                    <p v-if="message.message_type === 'text'" class="message-text">{{ message.body }}</p>
                    <div v-else-if="message.message_type === 'sticker'" class="sticker-message">{{ message.body }}</div>
                    <div v-else-if="message.message_type === 'voice'" class="voice-message"><audio controls preload="none" crossorigin="use-credentials" :src="message.attachment_url"></audio><small>{{ formatDuration(message.duration_seconds) }}</small></div>
                    <RouterLink v-else-if="message.message_type === 'post_share'" class="shared-post" :to="message.shared_post_preview?.url || '/explore'">
                      <img v-if="message.shared_post_preview?.media_url" :src="message.shared_post_preview.media_url" alt="Shared post preview" loading="lazy" />
                      <span><small>{{ message.shared_post_preview ? 'POST BY ' + message.shared_post_preview.author : 'SHARED POST' }}</small><strong>{{ message.shared_post_preview?.excerpt || 'This post is no longer available.' }}</strong><b>Open post <ArrowUpRight :size="13" /></b></span>
                    </RouterLink>
                    <footer><time>{{ formatTime(message.created_at) || 'Sending…' }}</time><span v-if="message.pending">Sending</span><span v-else-if="message.failed">Not sent</span><span v-else-if="message.sender_id === currentUserId && message.read_at">Seen</span><button v-if="message.failed" type="button" @click="retryMessage(message)">Retry</button><button v-if="message.sender_id !== currentUserId && message.id" type="button" class="report-message" aria-label="Report message" @click="handleReport(message)"><Flag :size="12" /></button></footer>
                  </div>
                </article>
              </div>
            </div>

            <div v-if="statusMessage" class="chat-status" role="status">{{ statusMessage }}</div>
            <div v-if="currentConversation.blocked || currentConversation.blocked_you" class="blocked-composer">Messaging is unavailable while a block is active.</div>
            <div v-else class="composer-wrap">
              <div v-if="pickerOpen" class="emoji-picker" aria-label="Emoji and sticker picker">
                <section><strong>Emoji</strong><div class="picker-items"><button v-for="emoji in emojis" :key="emoji" @click="insertEmoji(emoji)">{{ emoji }}</button></div></section>
                <section><strong>Stickers</strong><div class="picker-items"><button v-for="sticker in stickers" :key="sticker" class="sticker-choice" @click="sendSticker(sticker)">{{ sticker }}</button></div></section>
              </div>
              <div v-if="recording" class="recording-panel"><span class="recording-dot"></span><strong>Recording voice note</strong><time>{{ formatDuration(recordingSeconds) }}</time><button @click="cancelRecording">Cancel</button><button class="record-send" @click="finishRecording(true)"><Send :size="15" /> Send voice</button></div>
              <div v-else class="composer">
                <button class="composer-tool" aria-label="Open emoji and sticker picker" @click="pickerOpen = !pickerOpen"><Smile :size="19" /></button>
                <button v-if="voiceSupported" class="composer-tool" aria-label="Record a voice note" @click="startRecording"><Mic :size="18" /></button>
                <textarea v-model="draft" rows="1" maxlength="3000" placeholder="Write a message…" aria-label="Write a message" :disabled="currentConversation.blocked || currentConversation.blocked_you" @input="handleTyping" @keydown.enter.exact.prevent="sendText" @blur="stopTyping" />
                <button class="send-button" aria-label="Send message" :disabled="!draft.trim() || sending" @click="sendText"><LoaderCircle v-if="sending" :size="17" class="spin" /><Send v-else :size="17" /></button>
              </div>
            </div>
          </template>
          <div v-else class="chat-placeholder"><div class="placeholder-mark"><MessageCircle :size="27" /></div><h2>Your conversations, in one place.</h2><p>Choose a conversation or message a creator directly from their profile.</p><RouterLink to="/explore">Find someone to message <ArrowUpRight :size="15" /></RouterLink></div>
        </section>
      </div>
    </section>
  </MainLayout>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowUpRight, Ban, Flag, LoaderCircle, LockKeyhole, MessageCircle, Mic, Search, Send, Smile } from 'lucide-vue-next'
import MainLayout from '../layouts/MainLayout.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useAuth } from '../composables/useAuth'
import { blockUser, createClientId, getConversationMessages, getConversations, markConversationRead, reportMessage, sendMessage, startConversation, unblockUser } from '../services/messageService'
import { subscribeUserEvents } from '../services/userEvents'

const route = useRoute()
const router = useRouter()
const { user, initializeAuth } = useAuth()
const currentUserId = computed(() => Number(user.value?.id || 0))
const conversations = ref([])
const currentConversation = ref(null)
const messages = ref([])
const listLoading = ref(true)
const listError = ref('')
const messageLoading = ref(false)
const olderLoading = ref(false)
const hasOlder = ref(false)
const nextBefore = ref(null)
const search = ref('')
const draft = ref('')
const sending = ref(false)
const pickerOpen = ref(false)
const recording = ref(false)
const recordingSeconds = ref(0)
const statusMessage = ref('')
const typingConversations = ref(new Set())
const emojis = ['😀','😂','🥹','😍','🤔','👏','🙏','✨','💛','📚','☕','🌱']
const stickers = ['📚','✨','💛','🎉','🤔','☕','🦊','🐈','🌱','🌟','👏','❤️']
const filteredConversations = computed(() => conversations.value.filter((item) => {
  const value = `${item.participant.display_name} ${item.participant.username}`.toLowerCase()
  return value.includes(search.value.toLowerCase().trim())
}))
const voiceSupported = computed(() => typeof MediaRecorder !== 'undefined' && !!navigator.mediaDevices?.getUserMedia)
const messageScroller = ref(null)
let messageRequestId = 0
let subscription = null
let pollingTimer = null
let recordingStream = null
let recorder = null
let recorderChunks = []
let recordingStartedAt = 0
let recordingTimer = null
let typingTimer = null
let typingSent = false
const typingTimers = new Map()
const pendingPayloads = new Map()

function preview(message) {
  if (!message) return 'Start a conversation'
  if (message.message_type === 'voice') return '🎙 Voice note'
  if (message.message_type === 'sticker') return message.body + ' Sticker'
  if (message.message_type === 'post_share') return 'Shared a post'
  return message.body || 'Message'
}

function formatTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const today = new Date()
  if (date.toDateString() === today.toDateString()) return date.toLocaleTimeString([], { hour:'numeric', minute:'2-digit' })
  return date.toLocaleDateString([], { month:'short', day:'numeric' })
}

function formatDuration(value) {
  const seconds = Math.max(0, Math.floor(Number(value || 0)))
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2,'0')}`
}

async function loadConversations() {
  listLoading.value = true
  listError.value = ''
  try {
    conversations.value = await getConversations()
    if (currentConversation.value) {
      const fresh = conversations.value.find((item) => item.id === currentConversation.value.id)
      if (fresh) currentConversation.value = fresh
    }
  } catch (error) {
    listError.value = error.message || 'Your conversations could not be loaded.'
  } finally { listLoading.value = false }
}

async function openForUser(targetId) {
  if (!targetId) return
  try {
    const result = await startConversation(targetId)
    currentConversation.value = result
    await loadMessages(result.id)
    router.replace({ name:'messages', query:{} })
  } catch (error) { statusMessage.value = error.message || 'Unable to start this conversation.' }
}

async function selectConversation(conversation) {
  currentConversation.value = conversation
  pickerOpen.value = false
  statusMessage.value = ''
  await loadMessages(conversation.id)
}

function closeConversation() {
  stopTyping()
  currentConversation.value = null
  messages.value = []
  router.replace({ name:'messages', query:{} })
}

async function loadMessages(conversationId) {
  const requestId = ++messageRequestId
  messageLoading.value = true
  messages.value = []
  try {
    const result = await getConversationMessages(conversationId)
    if (requestId !== messageRequestId) return
    messages.value = result.messages || []
    hasOlder.value = Boolean(result.has_more)
    nextBefore.value = result.next_before
    await nextTick()
    scrollToBottom()
    await markConversationRead(conversationId)
    await loadConversations()
  } catch (error) { statusMessage.value = error.message || 'Unable to load messages.' }
  finally { if (requestId === messageRequestId) messageLoading.value = false }
}

async function loadOlder() {
  if (!currentConversation.value || !nextBefore.value || olderLoading.value) return
  olderLoading.value = true
  const before = nextBefore.value
  const height = messageScroller.value?.scrollHeight || 0
  try {
    const result = await getConversationMessages(currentConversation.value.id, before)
    const keys = new Set(messages.value.map((item) => String(item.id || item.client_id)))
    const older = (result.messages || []).filter((item) => !keys.has(String(item.id || item.client_id)))
    messages.value = [...older, ...messages.value]
    hasOlder.value = Boolean(result.has_more)
    nextBefore.value = result.next_before
    await nextTick()
    if (messageScroller.value) messageScroller.value.scrollTop = messageScroller.value.scrollHeight - height
  } catch (error) { statusMessage.value = error.message || 'Older messages could not be loaded.' }
  finally { olderLoading.value = false }
}

function scrollToBottom() {
  if (messageScroller.value) messageScroller.value.scrollTop = messageScroller.value.scrollHeight
}

function addMessage(message) {
  if (!message || !currentConversation.value) return
  const exists = messages.value.some((item) => (message.id && item.id === message.id) || (message.client_id && item.client_id === message.client_id))
  if (!exists) messages.value.push(message)
  else if (message.id) {
    const index = messages.value.findIndex((item) => item.client_id === message.client_id || item.id === message.id)
    if (index >= 0) messages.value[index] = message
  }
  nextTick(scrollToBottom)
}

function optimisticMessage(payload) {
  const message = { id:null, client_id:payload.client_id, conversation_id:currentConversation.value.id, sender_id:currentUserId.value,
    message_type:payload.message_type, body:payload.body || '', duration_seconds:payload.duration_seconds, attachment_url:payload.url || '',
    shared_post_preview:payload.shared_post_preview || null, created_at:new Date().toISOString(), pending:true, failed:false }
  pendingPayloads.set(payload.client_id, payload)
  messages.value.push(message)
  nextTick(scrollToBottom)
  return message
}

async function sendPayload(payload) {
  if (!currentConversation.value || sending.value || currentConversation.value.blocked || currentConversation.value.blocked_you) return
  sending.value = true
  statusMessage.value = ''
  const optimistic = optimisticMessage(payload)
  try {
    const message = await sendMessage(currentConversation.value.id, payload)
    addMessage(message)
    pendingPayloads.delete(payload.client_id)
    await loadConversations()
  } catch (error) {
    optimistic.pending = false
    optimistic.failed = true
    statusMessage.value = error.message || 'Your message was not sent. Retry when you’re connected.'
  } finally { sending.value = false }
}

async function sendText() {
  const body = draft.value.trim()
  if (!body || sending.value) return
  const payload = { client_id:createClientId(), message_type:'text', body }
  draft.value = ''
  stopTyping()
  await sendPayload(payload)
}

function retryMessage(message) {
  const payload = pendingPayloads.get(message.client_id)
  if (!payload) return
  message.failed = false
  message.pending = true
  sendMessage(currentConversation.value.id, payload).then((result) => {
    addMessage(result)
    pendingPayloads.delete(message.client_id)
    statusMessage.value = ''
    loadConversations()
  }).catch((error) => {
    message.pending = false
    message.failed = true
    statusMessage.value = error.message || 'The message could not be sent. Try again.'
  })
}

function insertEmoji(emoji) { draft.value += emoji; pickerOpen.value = false }
function sendSticker(sticker) { pickerOpen.value = false; sendPayload({ client_id:createClientId(), message_type:'sticker', body:sticker }) }

function handleTyping() {
  if (!currentConversation.value) return
  if (!typingSent) {
    subscription?.send({ type:'typing', conversation_id:currentConversation.value.id, active:true })
    typingSent = true
  }
  window.clearTimeout(typingTimer)
  typingTimer = window.setTimeout(stopTyping, 1800)
}

function stopTyping() {
  window.clearTimeout(typingTimer)
  if (typingSent && currentConversation.value) subscription?.send({ type:'typing', conversation_id:currentConversation.value.id, active:false })
  typingSent = false
}

function handleRealtime(event) {
  if (event.type === 'typing') {
    const conversationId = Number(event.conversation_id)
    const updated = new Set(typingConversations.value)
    if (event.active) updated.add(conversationId)
    else updated.delete(conversationId)
    typingConversations.value = updated
    window.clearTimeout(typingTimers.get(conversationId))
    if (event.active) typingTimers.set(conversationId, window.setTimeout(() => {
      const next = new Set(typingConversations.value); next.delete(conversationId); typingConversations.value = next
    }, 4500))
  }
  if (event.type === 'message_new') {
    if (Number(event.conversation_id) === currentConversation.value?.id) {
      addMessage(event.message)
      if (event.message.sender_id !== currentUserId.value) markConversationRead(event.conversation_id)
    }
    loadConversations()
  }
  if (event.type === 'read_receipt' && Number(event.conversation_id) === currentConversation.value?.id) {
    for (const message of messages.value) if (message.sender_id === currentUserId.value && !message.read_at) message.read_at = event.read_at
  }
  if (event.type === 'user_blocked' && event.user_id === currentConversation.value?.participant.id) {
    currentConversation.value.blocked_you = true
    currentConversation.value.blocked = true
  }
  if (event.type === 'user_unblocked' && event.user_id === currentConversation.value?.participant.id) {
    currentConversation.value.blocked_you = false
    currentConversation.value.blocked = false
  }
}

async function startRecording() {
  statusMessage.value = ''
  try {
    recordingStream = await navigator.mediaDevices.getUserMedia({ audio:true })
    const mimeType = ['audio/webm;codecs=opus','audio/ogg;codecs=opus','audio/webm','audio/ogg'].find((type) => MediaRecorder.isTypeSupported(type))
    if (!mimeType) throw new Error('This browser cannot record a supported voice note.')
    recorderChunks = []
    recorder = new MediaRecorder(recordingStream, { mimeType })
    recorder.addEventListener('dataavailable', (event) => { if (event.data.size) recorderChunks.push(event.data) })
    recorder.start(250)
    recordingStartedAt = Date.now()
    recordingSeconds.value = 0
    recording.value = true
    recordingTimer = window.setInterval(() => { recordingSeconds.value = Math.floor((Date.now() - recordingStartedAt) / 1000) }, 300)
  } catch (error) { statusMessage.value = error.message || 'Microphone access is unavailable. Check your browser permissions.'; stopRecordingResources() }
}

function stopRecordingResources() {
  if (recordingTimer) window.clearInterval(recordingTimer)
  recordingTimer = null
  for (const track of recordingStream?.getTracks?.() || []) track.stop()
  recordingStream = null
}

function cancelRecording() {
  if (recorder?.state === 'recording') recorder.stop()
  recorder = null
  recorderChunks = []
  recording.value = false
  stopRecordingResources()
}

function finishRecording(shouldSend) {
  if (!recorder) return
  const activeRecorder = recorder
  const duration = Math.max(1, Math.min(180, Math.floor((Date.now() - recordingStartedAt) / 1000)))
  activeRecorder.addEventListener('stop', () => {
    const blob = new Blob(recorderChunks, { type:activeRecorder.mimeType || 'audio/webm' })
    recorderChunks = []
    stopRecordingResources()
    if (shouldSend && blob.size) {
      const file = new File([blob], `voice-note-${Date.now()}.webm`, { type:blob.type })
      sendPayload({ client_id:createClientId(), message_type:'voice', file, duration_seconds:duration })
    }
  }, { once:true })
  if (activeRecorder.state === 'recording') activeRecorder.stop()
  recorder = null
  recording.value = false
}

async function handleBlock() {
  if (!currentConversation.value) return
  try {
    await blockUser(currentConversation.value.participant.id)
    currentConversation.value.blocked = true
    currentConversation.value.blocked_by_me = true
    statusMessage.value = 'This person is blocked. You can unblock them from this chat.'
    await loadConversations()
  } catch (error) { statusMessage.value = error.message || 'Unable to block this person.' }
}

async function handleUnblock() {
  try {
    await unblockUser(currentConversation.value.participant.id)
    currentConversation.value.blocked = false
    currentConversation.value.blocked_by_me = false
    statusMessage.value = 'This person is unblocked.'
    await loadConversations()
  } catch (error) { statusMessage.value = error.message || 'Unable to unblock this person.' }
}

async function handleReport(message) {
  try {
    const result = await reportMessage(message.id)
    statusMessage.value = result.duplicate ? 'You already reported this message.' : 'Thanks. The message was reported.'
  } catch (error) { statusMessage.value = error.message || 'Unable to report this message.' }
}

async function syncLatest() {
  if (!currentConversation.value || document.visibilityState === 'hidden') return
  try {
    const result = await getConversationMessages(currentConversation.value.id)
    for (const message of result.messages || []) addMessage(message)
    await loadConversations()
  } catch {}
}

watch(() => route.query.user, async (userId) => {
  if (userId) await openForUser(userId)
})

onMounted(async () => {
  await initializeAuth()
  await loadConversations()
  subscription = subscribeUserEvents(handleRealtime)
  if (route.query.user) await openForUser(route.query.user)
  pollingTimer = window.setInterval(syncLatest, 20000)
})

onBeforeUnmount(() => {
  messageRequestId += 1
  subscription?.unsubscribe()
  if (pollingTimer) window.clearInterval(pollingTimer)
  for (const timer of typingTimers.values()) window.clearTimeout(timer)
  stopTyping()
  cancelRecording()
})
</script>

<style scoped>
.messages-page { max-width:1120px; margin:0 auto; padding-bottom:35px; }
.messages-page-heading { display:flex; justify-content:space-between; align-items:end; gap:20px; margin:4px 0 21px; }.messages-page-heading p { margin:0 0 7px; color:var(--text-tertiary); font-size:9px; font-weight:800; letter-spacing:.15em; }.messages-page-heading h1 { margin:0; font:850 clamp(30px,4vw,42px)/1.1 Manrope,sans-serif; letter-spacing:-.05em; }.secure-label { display:flex; align-items:center; gap:6px; color:var(--text-tertiary); font-size:10px; }
.messages-shell { height:min(720px,calc(100dvh - 230px)); min-height:450px; display:grid; grid-template-columns:330px minmax(0,1fr); overflow:hidden; border:1px solid var(--border-color); border-radius:22px; background:var(--card-bg); box-shadow:0 14px 42px var(--shadow-color); }
.conversation-rail { min-width:0; display:flex; flex-direction:column; border-right:1px solid var(--border-color); background:var(--card-bg); }.conversation-search { height:60px; flex:0 0 60px; display:flex; align-items:center; gap:10px; margin:0 13px; border-bottom:1px solid var(--border-soft); color:var(--text-tertiary); }.conversation-search input { width:100%; border:0; outline:0; background:transparent; color:var(--text-main); font-size:12px; }.conversation-list { min-height:0; overflow:auto; padding:7px; }.conversation-item { position:relative; width:100%; min-height:72px; display:flex; align-items:center; gap:11px; padding:10px; border-radius:14px; background:transparent; text-align:left; transition:background .18s,box-shadow .25s,transform .2s; }.conversation-item:hover { background:var(--card-soft); }.conversation-item.selected { background:color-mix(in srgb,var(--accent) 12%,var(--card-bg)); }.conversation-item.typing { box-shadow:inset 0 0 0 1px color-mix(in srgb,#d8b440 32%,transparent),0 0 17px color-mix(in srgb,#d8b440 13%,transparent); }.conversation-avatar { width:46px; height:46px; flex:0 0 46px; display:grid; place-items:center; overflow:hidden; border-radius:50%; background:var(--icon-bg); }.conversation-avatar img,.chat-contact-avatar img { width:100%; height:100%; object-fit:cover; }.conversation-copy { min-width:0; flex:1; display:grid; gap:4px; }.conversation-copy strong { overflow:hidden; color:var(--text-main); font-size:12px; text-overflow:ellipsis; white-space:nowrap; }.conversation-copy small { overflow:hidden; color:var(--text-tertiary); font-size:10px; text-overflow:ellipsis; white-space:nowrap; }.conversation-copy .typing-label { color:#ad8b23; font-weight:750; }.conversation-meta { height:40px; display:flex; flex-direction:column; align-items:flex-end; justify-content:space-between; flex:0 0 auto; }.conversation-meta time { color:var(--text-tertiary); font-size:9px; }.conversation-meta b { min-width:17px; height:17px; display:grid; place-items:center; padding:0 4px; border-radius:999px; background:var(--accent); color:#111; font-size:9px; }
.rail-state,.rail-empty { min-height:220px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:9px; padding:25px; color:var(--text-tertiary); text-align:center; }.rail-state p,.rail-empty p { margin:0; color:var(--text-secondary); font-size:11px; line-height:1.5; }.rail-state button { color:var(--text-main); font-size:11px; font-weight:700; }.rail-empty > span { font-size:27px; }.rail-empty strong { color:var(--text-main); font-size:13px; }.rail-empty a,.chat-placeholder a { display:inline-flex; align-items:center; gap:6px; color:var(--text-main); font-size:11px; font-weight:750; }
.chat-panel { min-width:0; display:grid; grid-template-rows:66px minmax(0,1fr) auto auto; background:radial-gradient(ellipse at 50% 100%,color-mix(in srgb,var(--accent) 3%,var(--card-bg)),var(--card-bg) 55%); }.chat-header { min-width:0; display:flex; align-items:center; gap:10px; padding:0 17px; border-bottom:1px solid var(--border-soft); background:var(--card-bg); }.chat-back { display:none; width:34px; height:34px; place-items:center; border-radius:10px; background:var(--icon-bg); color:var(--text-main); }.chat-contact-avatar { width:39px; height:39px; flex:0 0 39px; display:grid; place-items:center; overflow:hidden; border-radius:50%; background:var(--icon-bg); }.chat-contact-name { min-width:0; flex:1; display:grid; gap:3px; }.chat-contact-name strong { overflow:hidden; color:var(--text-main); font-size:12px; text-overflow:ellipsis; white-space:nowrap; }.chat-contact-name small { color:var(--text-tertiary); font-size:10px; }.block-control,.unblock-control { min-height:34px; display:flex; align-items:center; gap:6px; padding:0 10px; border:1px solid var(--border-color); border-radius:10px; background:transparent; color:var(--text-secondary); font-size:10px; }.blocked-label { color:var(--text-tertiary); font-size:10px; }
.message-scroller { min-height:0; overflow:auto; padding:17px clamp(14px,4vw,40px); overscroll-behavior:contain; }.message-list { display:flex; flex-direction:column; gap:10px; }.message-line { display:flex; align-items:flex-end; }.message-line.mine { justify-content:flex-end; }.message-bubble { max-width:min(78%,530px); min-width:70px; padding:10px 12px 7px; border:1px solid var(--border-color); border-radius:16px 16px 16px 5px; background:var(--card-soft); box-shadow:0 2px 8px color-mix(in srgb,var(--shadow-color) 35%,transparent); animation:bubble-in .18s ease-out; }.message-line.mine .message-bubble { border-color:color-mix(in srgb,var(--accent) 27%,var(--border-color)); border-radius:16px 16px 5px 16px; background:color-mix(in srgb,var(--accent) 14%,var(--card-bg)); }.message-line.failed .message-bubble { border-color:#dc8277; }.message-text { margin:0; color:var(--text-main); font-size:13px; line-height:1.5; white-space:pre-wrap; overflow-wrap:anywhere; }.message-bubble footer { min-height:15px; display:flex; justify-content:flex-end; align-items:center; gap:7px; margin-top:3px; color:var(--text-tertiary); font-size:8px; }.message-bubble footer button { color:#a53f34; font-size:9px; font-weight:700; }.message-bubble footer .report-message { display:grid; place-items:center; padding:2px; color:var(--text-tertiary); }.sticker-message { font-size:48px; line-height:1.12; }.voice-message { display:flex; align-items:center; gap:7px; }.voice-message audio { width:min(280px,55vw); height:36px; }.voice-message small { color:var(--text-tertiary); font-size:9px; }.shared-post { width:min(320px,60vw); display:grid; overflow:hidden; border:1px solid var(--border-color); border-radius:11px; background:var(--card-bg); }.shared-post > img { width:100%; max-height:150px; object-fit:cover; }.shared-post > span { display:grid; gap:5px; padding:10px; }.shared-post small { color:var(--text-tertiary); font-size:8px; font-weight:800; letter-spacing:.08em; }.shared-post strong { display:-webkit-box; overflow:hidden; color:var(--text-main); font-size:10px; font-weight:600; line-height:1.45; -webkit-line-clamp:3; -webkit-box-orient:vertical; }.shared-post b { display:flex; align-items:center; gap:5px; color:var(--text-secondary); font-size:9px; }
.load-older { min-height:31px; display:block; margin:0 auto 14px; padding:0 11px; border:1px solid var(--border-color); border-radius:999px; background:var(--card-bg); color:var(--text-secondary); font-size:9px; }.load-older:disabled { opacity:.55; }.thread-state,.thread-empty { min-height:280px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:10px; color:var(--text-tertiary); text-align:center; }.thread-empty > span { width:45px; height:45px; display:grid; place-items:center; border-radius:14px; background:color-mix(in srgb,var(--accent) 18%,var(--card-bg)); color:#ad9d21; font-size:22px; }.thread-empty strong { color:var(--text-main); font-size:14px; }.thread-empty p { max-width:330px; margin:0; color:var(--text-secondary); font-size:11px; line-height:1.6; }.chat-status { padding:6px 15px; color:#a54c3f; font-size:10px; text-align:center; }.blocked-composer { padding:15px; border-top:1px solid var(--border-soft); color:var(--text-tertiary); font-size:11px; text-align:center; }
.composer-wrap { position:relative; padding:12px 15px max(12px,env(safe-area-inset-bottom)); border-top:1px solid var(--border-soft); background:var(--card-bg); }.composer { display:flex; align-items:flex-end; gap:8px; min-height:46px; padding:5px 6px; border:1px solid var(--border-color); border-radius:15px; background:var(--input-bg); }.composer-tool,.send-button { width:34px; height:34px; flex:0 0 34px; display:grid; place-items:center; border-radius:10px; background:transparent; color:var(--text-tertiary); }.composer-tool:hover { background:var(--hover-bg); color:var(--text-main); }.composer textarea { flex:1; min-width:0; max-height:115px; resize:vertical; padding:8px 3px; border:0; outline:0; background:transparent; color:var(--text-main); font:500 12px/1.45 'DM Sans',sans-serif; }.send-button { background:var(--primary-bg); color:var(--primary-text); }.send-button:disabled { opacity:.42; }.emoji-picker { position:absolute; bottom:calc(100% - 5px); left:15px; z-index:3; width:min(300px,calc(100vw - 40px)); display:grid; gap:12px; padding:13px; border:1px solid var(--border-color); border-radius:15px; background:var(--card-bg); box-shadow:0 14px 42px var(--shadow-color); }.emoji-picker section { display:grid; gap:8px; }.emoji-picker section strong { color:var(--text-secondary); font-size:9px; }.picker-items { display:flex; flex-wrap:wrap; gap:5px; }.picker-items button { width:32px; height:32px; border-radius:9px; background:var(--card-soft); font-size:17px; }.picker-items .sticker-choice { font-size:20px; }.recording-panel { min-height:46px; display:flex; align-items:center; gap:9px; padding:5px 7px; border:1px solid var(--border-color); border-radius:14px; background:var(--input-bg); }.recording-panel strong { color:var(--text-main); font-size:10px; }.recording-panel time { color:var(--text-tertiary); font-size:10px; }.recording-panel button { min-height:32px; margin-left:auto; padding:0 8px; border-radius:9px; background:transparent; color:var(--text-secondary); font-size:9px; }.recording-panel .record-send { display:flex; align-items:center; gap:5px; background:var(--primary-bg); color:var(--primary-text); font-weight:750; }.recording-dot { width:8px; height:8px; border-radius:50%; background:#df554d; animation:record-pulse 1.2s infinite; }.chat-placeholder { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:11px; padding:25px; text-align:center; }.placeholder-mark { width:58px; height:58px; display:grid; place-items:center; border-radius:18px; background:color-mix(in srgb,var(--accent) 20%,var(--card-bg)); }.chat-placeholder h2 { max-width:380px; margin:2px 0 0; font:800 22px Manrope,sans-serif; letter-spacing:-.04em; }.chat-placeholder p { max-width:365px; margin:0; color:var(--text-secondary); font-size:12px; line-height:1.6; }
.conversation-row-move { transition:transform .28s cubic-bezier(.2,.8,.2,1); }.conversation-row-enter-active,.conversation-row-leave-active { transition:opacity .18s,transform .18s; }.conversation-row-enter-from,.conversation-row-leave-to { opacity:0; transform:translateY(-6px); }
@keyframes bubble-in { from { opacity:0; transform:translateY(5px) scale(.99); } to { opacity:1; transform:translateY(0) scale(1); } } @keyframes record-pulse { 50% { box-shadow:0 0 0 5px rgba(223,85,77,.15); } }
@media(max-width:720px) { .messages-page-heading { align-items:center; }.secure-label { font-size:0; }.messages-shell { height:calc(100dvh - 225px); min-height:470px; grid-template-columns:1fr; position:relative; }.conversation-rail { border-right:0; }.chat-panel { display:none; }.chat-panel.chat-open-mobile { position:absolute; inset:0; display:grid; z-index:2; }.chat-back { display:grid; }.message-scroller { padding:15px 12px; }.message-bubble { max-width:86%; }.voice-message audio { width:min(245px,52vw); }.composer-wrap { padding-inline:9px; }.conversation-item { min-height:68px; } }
@media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms!important; animation-iteration-count:1!important; transition-duration:.01ms!important; } }
</style>
