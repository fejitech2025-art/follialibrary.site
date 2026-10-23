<template>
  <MainLayout>
    <section class="profile-page">
      <button class="back-link" type="button" @click="router.back()"><ArrowLeft :size="17" /> Back</button>

      <div v-if="loading" class="profile-state"><LoaderCircle :size="24" class="spin" /><p>Loading profile…</p></div>
      <div v-else-if="error" class="profile-state"><h2>Profile unavailable</h2><p>{{ error }}</p><RouterLink to="/explore">Explore Follia</RouterLink></div>

      <template v-else-if="profile">
        <header class="profile-hero">
          <div class="profile-avatar">
            <UserAvatar :src="profile.avatar_url || profile.avatar" :alt="profile.display_name || profile.username || 'Profile picture'" :icon-size="36" />
          </div>
          <div class="profile-identity">
            <p class="eyebrow">CREATOR PROFILE</p>
            <h1>{{ profile.display_name || profile.username || 'Follia creator' }}</h1>
            <p class="username">@{{ profile.username }}</p>
            <p class="bio">{{ profile.bio || 'Sharing ideas, stories and discoveries with the Follia community.' }}</p>
            <a v-if="profile.website" class="website" :href="profile.website" target="_blank" rel="noopener noreferrer">{{ profile.website }}</a>
            <div class="profile-stats">
              <button @click="activeTab = 'Followers'"><UsersRound :size="15" /><strong>{{ profile.follower_count || 0 }}</strong><span>Followers</span></button>
              <button @click="activeTab = 'Following'"><UserRound :size="15" /><strong>{{ profile.following_count || 0 }}</strong><span>Following</span></button>
              <span class="profile-stat rank-stat"><Trophy :size="15" /><strong>{{ profile.rank_position ? `#${profile.rank_position}` : '—' }}</strong><span>Rank</span></span>
            </div>
          </div>
          <div class="profile-actions">
            <RouterLink v-if="isOwnProfile" to="/account/edit" class="edit-button"><Pencil :size="16" /> Edit profile</RouterLink>
            <template v-else>
              <button class="follow-button" :class="{ following }" :disabled="followLoading" @click="toggleFollow">
                <LoaderCircle v-if="followLoading" :size="16" class="spin" />
                <UserCheck v-else-if="following" :size="16" />
                <UserPlus v-else :size="16" />
                {{ following ? 'Following' : 'Follow' }}
              </button>
              <RouterLink class="message-button" :to="{ name: 'messages', query: { user: profile.user_id || profile.id } }"><MessageCircle :size="16" /><span>Message</span></RouterLink>
              <button class="report-button" aria-label="Report profile" @click="openReport"><Flag :size="16" /><span>Report</span></button>
            </template>
          </div>
        </header>

        <div class="profile-tabs" role="tablist" aria-label="Profile content">
          <button v-for="tab in ['Posts','Resources','Followers','Following']" :key="tab" :class="{ active: activeTab === tab }" @click="activeTab = tab">{{ tab }}</button>
        </div>

        <p v-if="reportSuccess" class="report-success" role="status">{{ reportSuccess }}</p>

        <section v-if="activeTab === 'Posts'" class="profile-content">
          <div v-if="postsLoading" class="profile-state small"><LoaderCircle :size="21" class="spin" /><p>Loading posts…</p></div>
          <div v-else-if="posts.length" class="posts-list"><FeedItemCard v-for="post in posts" :key="post.id" :item="{ ...post, kind: 'post' }" /></div>
          <div v-else class="empty-state"><MessageCircle :size="22" /><h2>No posts yet</h2><p>New ideas and discoveries from this creator will appear here.</p></div>
        </section>

        <section v-else-if="activeTab === 'Resources'" class="profile-content">
          <div v-if="resourcesLoading" class="profile-state small"><LoaderCircle :size="21" class="spin" /><p>Loading resources…</p></div>
          <div v-else-if="resources.length" class="resources-grid">
            <ResourceCard v-for="resource in normalizedResources" :key="resource.id" :resource="resource" />
          </div>
          <div v-else class="empty-state"><BookOpen :size="22" /><h2>No resources yet</h2><p>Books and useful materials shared by this creator will appear here.</p></div>
        </section>

        <section v-else class="profile-content people-list">
          <div v-if="peopleLoading" class="profile-state small"><LoaderCircle :size="21" class="spin" /><p>Loading {{ activeTab.toLowerCase() }}…</p></div>
          <RouterLink v-for="person in people" :key="person.id" :to="{ name: 'publisher-detail', params: { id: person.id } }" class="person-row">
            <div class="person-avatar"><UserAvatar :src="person.avatar_url || person.avatar" :alt="person.display_name || person.username || 'Profile picture'" :icon-size="18" /></div>
            <span><strong>{{ person.display_name || person.username }}</strong><small>@{{ person.username }}</small><p v-if="person.bio">{{ person.bio }}</p></span>
            <ArrowUpRight :size="16" />
          </RouterLink>
          <div v-if="!peopleLoading && !people.length" class="empty-state"><UsersRound :size="22" /><h2>No {{ activeTab.toLowerCase() }} to show</h2><p>This list will grow as people follow creators on Follia.</p></div>
        </section>
      </template>

      <Teleport to="body">
        <div v-if="showReport" class="report-overlay" @click.self="showReport = false">
          <form class="report-modal" @submit.prevent="submitReport">
            <button type="button" class="close-report" aria-label="Close" @click="showReport = false"><X :size="18" /></button>
            <p class="eyebrow">HELP KEEP FOLLIA SAFE</p><h2>Report this profile</h2>
            <label for="reason">Reason</label>
            <select id="reason" v-model="reportReason" required>
              <option value="" disabled>Select a reason</option><option value="spam">Spam</option><option value="impersonation">Impersonation</option><option value="harassment">Harassment</option><option value="inappropriate">Inappropriate content</option><option value="other">Other</option>
            </select>
            <label for="details">More details <span>Optional</span></label>
            <textarea id="details" v-model="reportDescription" rows="4" maxlength="500"></textarea>
            <p v-if="reportError" class="report-error">{{ reportError }}</p>
            <button class="submit-report" :disabled="reportLoading || !reportReason">{{ reportLoading ? 'Sending…' : 'Send report' }}</button>
          </form>
        </div>
      </Teleport>
    </section>
  </MainLayout>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowUpRight, BookOpen, Flag, LoaderCircle, MessageCircle, Pencil, Trophy, UserCheck, UserPlus, UserRound, UsersRound, X } from 'lucide-vue-next'
import MainLayout from '../layouts/MainLayout.vue'
import FeedItemCard from '../components/FeedItemCard.vue'
import ResourceCard from '../components/ResourceCard.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useAuth } from '../composables/useAuth'
import { getPublisher, getPublisherResources } from '../services/publisherService'
import { getPosts } from '../services/postService'
import { getFollowers, getFollowing, followUser, unfollowUser } from '../services/followService'
import { reportPublisher } from '../services/reportService'

const route = useRoute()
const router = useRouter()
const { user, initializeAuth } = useAuth()
const profile = ref(null)
const posts = ref([])
const resources = ref([])
const people = ref([])
const activeTab = ref('Posts')
const loading = ref(true)
const postsLoading = ref(false)
const resourcesLoading = ref(false)
const peopleLoading = ref(false)
const followLoading = ref(false)
const following = ref(false)
const error = ref('')
const showReport = ref(false)
const reportReason = ref('')
const reportDescription = ref('')
const reportError = ref('')
const reportLoading = ref(false)
const reportSuccess = ref('')
const isOwnProfile = computed(() => String(user.value?.id || '') === String(profile.value?.user_id || profile.value?.id || ''))
const normalizedResources = computed(() => resources.value.map((item) => ({ ...item, cover: item.cover_url, free: item.is_free, author: item.profiles?.display_name || item.profiles?.username || 'Follia creator', authorProfile: '/profile/' + item.author_id })))

async function loadProfile() {
  loading.value = true
  error.value = ''
  await initializeAuth()
  try {
    profile.value = await getPublisher(route.params.id)
    following.value = Boolean(profile.value.is_following)
  } catch (err) {
    error.value = err.message || 'We could not load this profile.'
  } finally {
    loading.value = false
  }
  await Promise.all([loadPosts(), loadResources()])
}

async function loadPosts() {
  postsLoading.value = true
  try { posts.value = await getPosts({ author: route.params.id }) }
  catch { posts.value = [] }
  finally { postsLoading.value = false }
}

async function loadResources() {
  resourcesLoading.value = true
  try { resources.value = await getPublisherResources(route.params.id) }
  catch { resources.value = [] }
  finally { resourcesLoading.value = false }
}

async function loadPeople() {
  peopleLoading.value = true
  try { people.value = activeTab.value === 'Followers' ? await getFollowers(route.params.id) : await getFollowing(route.params.id) }
  catch { people.value = [] }
  finally { peopleLoading.value = false }
}

async function toggleFollow() {
  followLoading.value = true
  const before = following.value
  following.value = !before
  try {
    const profileUserId = profile.value.user_id || profile.value.id
    await (before ? unfollowUser(profileUserId) : followUser(profileUserId))
    profile.value.follower_count = Math.max(0, (profile.value.follower_count || 0) + (before ? -1 : 1))
  } catch (err) {
    following.value = before
    error.value = err.message || 'Unable to update following.'
  } finally {
    followLoading.value = false
  }
}

function openReport() {
  reportError.value = ''
  reportSuccess.value = ''
  reportReason.value = ''
  reportDescription.value = ''
  showReport.value = true
}

async function submitReport() {
  reportLoading.value = true
  reportError.value = ''
  try {
    const result = await reportPublisher({ reportedUserId: profile.value.user_id || profile.value.id, reason: reportReason.value, description: reportDescription.value })
    showReport.value = false
    reportReason.value = ''
    reportDescription.value = ''
    reportSuccess.value = result?.duplicate ? 'You have already reported this profile.' : 'Thanks. Your report was sent.'
  } catch (err) {
    reportError.value = err.message || 'Unable to submit your report.'
  } finally {
    reportLoading.value = false
  }
}

watch(activeTab, (tab) => { if (tab === 'Followers' || tab === 'Following') loadPeople() })
watch(() => route.params.id, loadProfile)
onMounted(loadProfile)
</script>

<style scoped>
.profile-page { max-width:900px; margin:0 auto; padding-bottom:35px; }
.report-success { margin:12px 0; padding:10px 13px; border:1px solid var(--border-color); border-radius:10px; background:var(--card-bg); color:var(--text-secondary); font-size:11px; }
.back-link { display:inline-flex; align-items:center; gap:7px; margin:2px 0 18px; background:transparent; color:var(--text-secondary); font-size:12px; font-weight:650; }
.profile-hero { display:grid; grid-template-columns:106px minmax(0,1fr) auto; align-items:start; gap:22px; padding:24px; border:1px solid var(--border-color); border-radius:22px; background:var(--card-bg); }
.profile-avatar { width:106px; height:106px; display:grid; place-items:center; overflow:hidden; border-radius:50%; background:var(--icon-bg); font-size:27px; font-weight:750; }
.profile-avatar img { width:100%; height:100%; object-fit:cover; }
.profile-identity { min-width:0; }
.eyebrow { margin:1px 0 8px; color:var(--text-tertiary); font-size:9px; font-weight:750; letter-spacing:.14em; }
.profile-identity h1 { margin:0; font:800 clamp(26px,4vw,36px)/1.1 Manrope,sans-serif; letter-spacing:-.05em; }
.username { margin:5px 0 0; color:var(--text-tertiary); font-size:12px; }
.bio { margin:13px 0 0; color:var(--text-secondary); font-size:13px; line-height:1.6; white-space:pre-wrap; }
.website { display:inline-block; margin-top:7px; color:var(--text-main); font-size:11px; text-decoration:underline; text-underline-offset:3px; }
.profile-stats { display:flex; flex-wrap:wrap; gap:19px; margin-top:18px; }
.profile-stats button,.profile-stat { display:flex; align-items:center; gap:6px; padding:0; background:transparent; color:var(--text-main); }
.profile-stats button { cursor:pointer; }
.profile-stats svg { flex:0 0 auto; color:var(--text-tertiary); }
.profile-stats strong { font-size:13px; font-weight:750; }
.profile-stats span { color:var(--text-secondary); font-size:11px; }
.profile-actions { display:flex; align-items:center; gap:8px; }
.follow-button,.message-button,.edit-button { min-height:40px; display:inline-flex; align-items:center; justify-content:center; gap:7px; padding:0 13px; border:1px solid var(--border-color); border-radius:12px; background:var(--primary-bg); color:var(--primary-text); font-size:11px; font-weight:700; }
.follow-button.following { background:transparent; color:var(--text-main); }
.report-button { min-height:40px; display:inline-flex; align-items:center; gap:7px; padding:0 11px; border:1px solid var(--border-color); border-radius:12px; background:transparent; color:var(--text-secondary); font-size:11px; }
.profile-tabs { display:flex; gap:23px; margin:20px 0 17px; border-bottom:1px solid var(--border-color); overflow:auto; }
.profile-tabs button { position:relative; flex-shrink:0; padding:12px 3px; background:transparent; color:var(--text-tertiary); font-size:12px; font-weight:650; }
.profile-tabs button.active { color:var(--text-main); }
.profile-tabs button.active::after { content:''; position:absolute; left:0; right:0; bottom:-1px; height:2px; border-radius:2px; background:var(--text-main); }
.profile-content { min-height:200px; }
.posts-list { display:grid; gap:12px; max-width:700px; }
.resources-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:15px; }
.empty-state,.profile-state { min-height:190px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:7px; padding:30px; border:1px dashed var(--border-color); border-radius:18px; background:var(--card-bg); color:var(--text-tertiary); text-align:center; }
.empty-state h2 { margin:5px 0 0; color:var(--text-main); font:750 18px Manrope,sans-serif; }
.empty-state p,.profile-state p { margin:0; color:var(--text-secondary); font-size:12px; }
.profile-state.small { min-height:100px; flex-direction:row; }
.profile-state h2 { margin:5px 0; color:var(--text-main); font:750 19px Manrope,sans-serif; }
.profile-state a { margin-top:8px; color:var(--text-main); font-size:12px; font-weight:700; }
.person-row { display:flex; align-items:center; gap:12px; padding:13px 4px; border-bottom:1px solid var(--border-soft); }
.person-avatar { width:43px; height:43px; flex:0 0 43px; display:grid; place-items:center; overflow:hidden; border-radius:50%; background:var(--icon-bg); font-size:12px; font-weight:700; }
.person-avatar img { width:100%; height:100%; object-fit:cover; }
.person-row > span { flex:1; min-width:0; }
.person-row strong,.person-row small { display:block; }
.person-row strong { font-size:12px; }
.person-row small { margin-top:3px; color:var(--text-tertiary); font-size:10px; }
.person-row p { margin:4px 0 0; overflow:hidden; color:var(--text-secondary); font-size:11px; text-overflow:ellipsis; white-space:nowrap; }
.person-row > svg { color:var(--text-tertiary); }
.report-overlay { position:fixed; inset:0; z-index:300; display:grid; place-items:center; padding:18px; background:rgba(15,15,15,.52); backdrop-filter:blur(5px); }
.report-modal { position:relative; width:min(440px,100%); display:grid; gap:10px; padding:25px; border:1px solid var(--border-color); border-radius:20px; background:var(--card-bg); box-shadow:0 20px 70px rgba(0,0,0,.2); }
.close-report { position:absolute; top:15px; right:15px; width:34px; height:34px; display:grid; place-items:center; border-radius:10px; background:var(--icon-bg); }
.report-modal h2 { margin:-2px 0 8px; font:750 22px Manrope,sans-serif; }
.report-modal label { margin-top:6px; font-size:11px; font-weight:700; }
.report-modal label span { margin-left:4px; color:var(--text-tertiary); font-weight:400; }
.report-modal select,.report-modal textarea { width:100%; padding:11px; border:1px solid var(--border-color); border-radius:11px; background:var(--input-bg); color:var(--text-main); font-size:12px; }
.report-modal textarea { resize:vertical; }
.submit-report { min-height:42px; margin-top:5px; border-radius:11px; background:var(--primary-bg); color:var(--primary-text); font-size:12px; font-weight:700; }
.submit-report:disabled { opacity:.5; }
.report-error { margin:0; color:#a33b30; font-size:11px; }
.spin { animation:spin 1s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
@media(max-width:740px) {
  .profile-hero { grid-template-columns:minmax(0,1fr); justify-items:center; gap:15px; padding:22px 17px; text-align:center; }
  .profile-avatar { width:88px; height:88px; font-size:22px; border-radius:50%; }
  .profile-identity { width:100%; }
  .profile-identity h1 { font-size:clamp(21px,6vw,28px); overflow-wrap:anywhere; }
  .profile-identity .bio { margin-top:10px; font-size:12px; }
  .profile-actions { grid-column:auto; justify-content:center; flex-wrap:wrap; }
  .profile-stats { justify-content:center; gap:17px; margin-top:15px; }
  .profile-stats button,.profile-stat { min-width:0; flex-wrap:wrap; gap:5px; }
  .profile-stats span { font-size:10px; }
  .website { max-width:100%; overflow-wrap:anywhere; }
  .resources-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:11px; }
  .profile-tabs { gap:19px; }
}
@media(max-width:400px) {
  .profile-hero { grid-template-columns:minmax(0,1fr); gap:12px; padding:16px 12px; }
  .profile-avatar { width:76px; height:76px; font-size:19px; }
  .profile-actions { gap:7px; }
  .profile-actions > * { flex:1; }
  .report-button { justify-content:center; }
  .report-button span { display:none; }
}
</style>
