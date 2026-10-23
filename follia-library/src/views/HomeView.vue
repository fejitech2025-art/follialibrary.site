<template>
  <MainLayout>
    <div class="home-layout">
      <section class="feed-column">
        <header class="feed-intro">
          <div>
           
    
          </div>
          <RouterLink to="/explore" class="explore-link">Explore <ArrowUpRight :size="16" /></RouterLink>
        </header>

        <button class="quick-compose" @click="router.push('/create')">
          <div class="compose-avatar"><UserAvatar :src="profile?.avatar_url || profile?.avatar" alt="Your profile picture" :icon-size="18" /></div>
          <span>What have you discovered lately?</span>
          <Plus :size="20" />
        </button>

        <div class="feed-tabs" role="tablist" aria-label="Feed">
          <button :class="{ active: activeTab === 'for-you' }" @click="selectTab('for-you')">For you</button>
          <button :class="{ active: activeTab === 'following' }" @click="selectTab('following')">Following</button>
        </div>

        <div v-if="loading" class="feed-loading" aria-label="Loading feed">
          <div v-for="n in 3" :key="n" class="feed-skeleton"><i></i><span></span><b></b></div>
        </div>
        <div v-else-if="error" class="empty-feed">
          <div class="empty-mark"><Compass :size="22" /></div>
          <h2>Your feed is taking a moment.</h2>
          <p>{{ error }}</p>
          <button @click="loadFeed">Try again</button>
        </div>
        <div v-else-if="feed.length" class="feed-list">
          <template v-for="(item, index) in feed" :key="item.kind + '-' + item.id">
            <FeedItemCard :item="item" />
            <section v-if="(index + 1) % 8 === 0 && suggestionProfiles.length" class="feed-suggestions">
              <div class="suggestions-heading"><div><p>MEET SOMEONE NEW</p><h2>People to know</h2></div><span>Scroll to explore</span></div>
              <div class="suggestions-track">
                <article v-for="person in suggestionSetFor(index)" :key="person.user_id || person.id" class="suggestion-card">
                  <RouterLink :to="{ name: 'publisher-detail', params: { id: person.user_id || person.id } }" class="suggested-person">
                    <div class="suggested-avatar"><UserAvatar :src="person.avatar_url || person.avatar" :alt="person.display_name || person.username || 'Profile picture'" :icon-size="20" /></div>
                    <span><strong>{{ person.display_name || person.username }}</strong><small>@{{ person.username }}</small></span>
                  </RouterLink>
                  <p class="suggestion-bio">{{ person.bio || 'A new voice in the Follia community.' }}</p>
                  <button :class="{ following: person.is_following }" @click="toggleSuggestedFollow(person)">{{ person.is_following ? 'Following' : 'Follow' }}</button>
                </article>
              </div>
            </section>
          </template>
          <div ref="feedSentinel" class="feed-sentinel" aria-hidden="true"></div>
          <div v-if="loadingMore" class="feed-more-loading" role="status"><i></i><span>Finding more ideas...</span></div>
          <div v-else-if="loadMoreError" class="feed-more-error" role="status"><span>{{ loadMoreError }}</span><button @click="loadMore">Try again</button></div>
          <p v-else-if="!hasMore" class="feed-end">You’re all caught up.</p>
        </div>
        <div v-else class="empty-feed">
          <div class="empty-mark"><Sparkles :size="22" /></div>
          <h2>{{ activeTab === 'following' ? 'Your circle is just getting started.' : 'A little room for discovery.' }}</h2>
          <p>{{ activeTab === 'following' ? 'Follow a creator to bring their posts and recommendations into this feed.' : 'Explore people, posts, resources and reading communities to find something new.' }}</p>
          <RouterLink to="/explore">Find something new <ArrowUpRight :size="16" /></RouterLink>
        </div>
      </section>

      <aside class="discovery-rail">
        <section class="rail-card motto-card">
          <span class="rail-mark"><Sparkles :size="17" /></span>
          <p class="rail-kicker">A WORLD OF IDEAS</p>
          <h2>Discover anything.</h2>
          <p>Follow a curiosity. See where it takes you.</p>
          <RouterLink to="/explore">Explore Follia <ArrowUpRight :size="15" /></RouterLink>
        </section>

        <section class="rail-card creators-card">
          <div class="rail-heading"><h2>People to know</h2><RouterLink to="/explore">See all</RouterLink></div>
          <p v-if="!creators.length" class="rail-empty">Creators you may like will appear here.</p>
          <div v-for="person in creators" :key="person.id" class="creator-suggestion">
            <RouterLink :to="{ name: 'publisher-detail', params: { id: person.id } }" class="suggested-person">
              <div class="suggested-avatar">
                <UserAvatar :src="person.avatar_url || person.avatar" :alt="person.display_name || person.username || 'Profile picture'" :icon-size="17" />
              </div>
              <span><strong>{{ person.display_name || person.username }}</strong><small>@{{ person.username }}</small></span>
            </RouterLink>
            <button :class="{ following: person.is_following }" @click="toggleSuggestedFollow(person)">
              {{ person.is_following ? 'Following' : 'Follow' }}
            </button>
          </div>
        </section>

        <section class="rail-card ranks-card">
          <div class="rail-heading"><h2>Community ranks</h2><Trophy :size="17" /></div>
          <p>Share useful ideas, join conversations, and see your contribution grow.</p>
          <RouterLink to="/ranks">See the leaderboard <ArrowUpRight :size="15" /></RouterLink>
        </section>
        <footer class="rail-footer"><RouterLink to="/about">About</RouterLink><span>Follia · Discover anything.</span></footer>
      </aside>
    </div>
  </MainLayout>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowUpRight, Compass, Plus, Sparkles, Trophy } from 'lucide-vue-next'
import MainLayout from '../layouts/MainLayout.vue'
import FeedItemCard from '../components/FeedItemCard.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useAuth } from '../composables/useAuth'
import { getMyProfile } from '../services/profileService'
import { getFeed } from '../services/postService'
import { getSuggestedProfiles } from '../services/postService'
import { followUser, unfollowUser } from '../services/followService'

const router = useRouter()
const { user, initializeAuth } = useAuth()
const activeTab = ref('for-you')
const feed = ref([])
const creators = ref([])
const suggestionProfiles = ref([])
const profile = ref(null)
const page = ref(1)
const hasMore = ref(true)
const loadingMore = ref(false)
const loadMoreError = ref('')
const feedSentinel = ref(null)
const loading = ref(true)
const error = ref('')
let feedRequestId = 0
let feedObserver = null

async function loadFeed() {
  const requestId = ++feedRequestId
  loading.value = true
  error.value = ''
  feed.value = []
  page.value = 1
  hasMore.value = true
  loadMoreError.value = ''
  try {
    const result = await getFeed(activeTab.value, 1)
    if (requestId !== feedRequestId) return
    feed.value = result.results || []
    hasMore.value = Boolean(result.has_more)
  } catch (err) {
    if (requestId === feedRequestId) error.value = err.message || 'The feed is temporarily unavailable.'
  } finally {
    if (requestId === feedRequestId) loading.value = false
  }
}

async function loadMore() {
  if (loading.value || loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  loadMoreError.value = ''
  const requestId = feedRequestId
  const nextPage = page.value + 1
  try {
    const result = await getFeed(activeTab.value, nextPage)
    if (requestId !== feedRequestId) return
    const seen = new Set(feed.value.map((item) => item.kind + ':' + item.id))
    for (const item of result.results || []) {
      const key = item.kind + ':' + item.id
      if (!seen.has(key)) { feed.value.push(item); seen.add(key) }
    }
    page.value = nextPage
    hasMore.value = Boolean(result.has_more)
  } catch (err) {
    if (requestId === feedRequestId) loadMoreError.value = err.message || 'More posts could not be loaded.'
  } finally {
    if (requestId === feedRequestId) loadingMore.value = false
  }
}

async function selectTab(tab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  await loadFeed()
}

async function loadCreators() {
  try {
    const people = await getSuggestedProfiles()
    const currentUserId = String(user.value?.id || '')
    const eligible = people.filter((person) => String(person.user_id || person.id) !== currentUserId)
    const seenKey = 'follia:suggested-profiles:v1'
    let seen = new Set()
    try { seen = new Set(JSON.parse(sessionStorage.getItem(seenKey) || '[]').map(String)) } catch {}
    let fresh = eligible.filter((person) => !seen.has(String(person.user_id || person.id)))
    if (!fresh.length) { seen.clear(); fresh = eligible }
    suggestionProfiles.value = fresh
    creators.value = fresh.slice(0, 4)
    for (const person of fresh) seen.add(String(person.user_id || person.id))
    sessionStorage.setItem(seenKey, JSON.stringify([...seen].slice(-120)))
  } catch {}
}

function suggestionSetFor(index) {
  const profiles = suggestionProfiles.value
  if (!profiles.length) return []
  const start = (Math.floor((index + 1) / 8) * 4) % profiles.length
  return Array.from({ length: Math.min(8, profiles.length) }, (_, offset) => profiles[(start + offset) % profiles.length])
}

async function toggleSuggestedFollow(person) {
  const before = person.is_following
  person.is_following = !before
  const userId = person.user_id || person.id
  try {
    await (before ? unfollowUser(userId) : followUser(userId))
  } catch (err) {
    person.is_following = before
  }
}

onMounted(async () => {
  feedObserver = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) loadMore()
  }, { rootMargin: '700px 0px' })
  watch(feedSentinel, (element, previous) => {
    if (previous) feedObserver?.unobserve(previous)
    if (element) feedObserver?.observe(element)
  }, { flush: 'post', immediate: true })
  await initializeAuth()
  try { profile.value = await getMyProfile() } catch {}
  await Promise.all([loadFeed(), loadCreators()])
})
onBeforeUnmount(() => feedObserver?.disconnect())
</script>

<style scoped>
.home-layout { display:grid; grid-template-columns:minmax(0,680px) 300px; align-items:start; justify-content:center; gap:42px; max-width:1080px; margin:0 auto; padding:0 0 32px; }
.feed-column { min-width:0; }
.feed-intro { display:flex; align-items:flex-end; justify-content:space-between; gap:18px; padding:8px 2px 22px; }
.feed-kicker,.rail-kicker { margin:0 0 11px; color:var(--text-tertiary); font-size:10px; font-weight:750; letter-spacing:.15em; }
.feed-intro h1 { margin:0; font:800 clamp(30px,4.2vw,44px)/1.08 Manrope,sans-serif; letter-spacing:-.055em; }
.feed-intro h1 span { color:var(--text-secondary); }
.feed-description { margin:9px 0 0; color:var(--text-secondary); font-size:13px; line-height:1.5; }
.explore-link { flex-shrink:0; display:flex; align-items:center; gap:6px; margin-bottom:2px; color:var(--text-main); font-size:12px; font-weight:700; }
.quick-compose { width:100%; min-height:64px; display:flex; align-items:center; gap:12px; padding:10px 14px; border:1px solid var(--border-color); border-radius:17px; background:var(--card-bg); color:var(--text-tertiary); text-align:left; box-shadow:0 3px 14px color-mix(in srgb,var(--shadow-color) 40%,transparent); }
.quick-compose span { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:12px; }
.quick-compose > svg { color:var(--text-secondary); }
.compose-avatar { width:38px; height:38px; flex:0 0 38px; display:grid; place-items:center; border-radius:50%; background:var(--icon-bg); color:var(--text-main); font-weight:750; }
.feed-tabs { position:sticky; top:78px; z-index:4; display:flex; margin:17px 0 13px; border-bottom:1px solid var(--border-color); background:var(--page-bg); }
.feed-tabs button { position:relative; min-width:95px; padding:12px 17px; background:transparent; color:var(--text-tertiary); font-size:12px; font-weight:650; }
.feed-tabs button.active { color:var(--text-main); }
.feed-tabs button.active::after { content:''; position:absolute; left:18px; right:18px; bottom:-1px; height:2px; border-radius:2px; background:var(--text-main); }
.feed-list { display:grid; gap:13px; }
.feed-suggestions { min-width:0; padding:16px; border:1px solid var(--border-color); border-radius:18px; background:var(--card-bg); }
.suggestions-heading { display:flex; align-items:flex-end; justify-content:space-between; gap:12px; margin-bottom:12px; }
.suggestions-heading p { margin:0 0 4px; color:var(--text-tertiary); font-size:9px; font-weight:750; letter-spacing:.13em; }
.suggestions-heading h2 { margin:0; font:750 17px Manrope,sans-serif; }
.suggestions-heading > span { color:var(--text-tertiary); font-size:10px; }
.suggestions-track { display:flex; gap:9px; overflow-x:auto; padding-bottom:3px; scroll-snap-type:x mandatory; scrollbar-width:thin; }
.suggestion-card { flex:0 0 min(210px,75vw); display:grid; align-content:start; gap:10px; min-height:143px; padding:12px; border:1px solid var(--border-soft); border-radius:14px; background:var(--card-soft); scroll-snap-align:start; }
.suggestion-card .suggested-person { gap:9px; }
.suggestion-card .suggested-person strong { max-width:145px; }
.suggestion-bio { min-height:30px; margin:0; color:var(--text-secondary); font-size:10px; line-height:1.5; }
.suggestion-card > button { justify-self:start; min-height:29px; padding:0 11px; border-radius:999px; background:var(--text-main); color:var(--card-bg); font-size:10px; font-weight:700; }
.suggestion-card > button.following { border:1px solid var(--border-color); background:transparent; color:var(--text-secondary); }
.feed-sentinel { height:1px; }
.feed-more-loading,.feed-more-error { min-height:47px; display:flex; align-items:center; justify-content:center; gap:11px; color:var(--text-tertiary); font-size:12px; }
.feed-more-loading i { width:18px; height:18px; border:2px solid var(--border-color); border-top-color:var(--accent); border-radius:50%; animation:feed-spin .7s linear infinite; }
.feed-more-error button { min-height:34px; padding:0 12px; border-radius:10px; background:var(--hover-bg); color:var(--text-main); font-weight:700; }
.feed-end { margin:7px 0; color:var(--text-tertiary); font-size:11px; text-align:center; }
@keyframes feed-spin { to { transform:rotate(360deg); } }
.empty-feed { display:flex; flex-direction:column; align-items:center; margin-top:12px; padding:50px 28px; border:1px dashed var(--border-color); border-radius:20px; background:var(--card-bg); text-align:center; }
.empty-mark { width:48px; height:48px; display:grid; place-items:center; border-radius:15px; background:var(--icon-bg); color:var(--text-secondary); }
.empty-feed h2 { margin:17px 0 0; font:750 19px Manrope,sans-serif; letter-spacing:-.03em; }
.empty-feed p { max-width:380px; margin:8px 0 18px; color:var(--text-secondary); font-size:12px; line-height:1.6; }
.empty-feed button,.empty-feed a { display:inline-flex; align-items:center; gap:7px; min-height:38px; padding:0 12px; border-radius:11px; background:var(--primary-bg); color:var(--primary-text); font-size:11px; font-weight:700; }
.feed-skeleton { display:grid; grid-template-columns:40px 1fr; gap:10px 12px; padding:19px; border:1px solid var(--border-color); border-radius:18px; background:var(--card-bg); }
.feed-skeleton i { width:40px; height:40px; border-radius:50%; background:var(--icon-bg); }
.feed-skeleton span,.feed-skeleton b { border-radius:7px; background:var(--icon-bg); }
.feed-skeleton span { width:55%; height:14px; align-self:center; }
.feed-skeleton b { grid-column:1/-1; height:88px; margin-top:8px; }
.discovery-rail { position:sticky; top:98px; display:grid; gap:13px; padding-top:8px; }
.rail-card { padding:18px; border:1px solid var(--border-color); border-radius:18px; background:var(--card-bg); }
.motto-card { background:linear-gradient(145deg,var(--card-bg),var(--card-soft)); }
.rail-mark { width:32px; height:32px; display:grid; place-items:center; margin-bottom:17px; border-radius:10px; background:var(--icon-bg); }
.rail-kicker { margin-bottom:7px; font-size:9px; }
.motto-card h2 { margin:0; font:800 22px Manrope,sans-serif; letter-spacing:-.045em; }
.motto-card > p:not(.rail-kicker),.ranks-card > p { margin:7px 0 15px; color:var(--text-secondary); font-size:12px; line-height:1.55; }
.rail-card > a { display:inline-flex; align-items:center; gap:6px; color:var(--text-main); font-size:11px; font-weight:700; }
.rail-heading { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.rail-heading h2 { margin:0; font:750 14px Manrope,sans-serif; letter-spacing:-.02em; }
.rail-heading > a { color:var(--text-tertiary); font-size:10px; font-weight:650; }
.rail-heading > svg { color:var(--text-tertiary); }
.creator-suggestion { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-top:16px; }
.suggested-person { display:flex; min-width:0; align-items:center; gap:9px; }
.suggested-avatar { width:36px; height:36px; flex:0 0 36px; display:grid; place-items:center; overflow:hidden; border-radius:50%; background:var(--icon-bg); font-size:11px; font-weight:700; }
.suggested-avatar img { width:100%; height:100%; object-fit:cover; }
.suggested-person span { min-width:0; }
.suggested-person strong,.suggested-person small { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.suggested-person strong { max-width:130px; font-size:11px; }
.suggested-person small { margin-top:3px; color:var(--text-tertiary); font-size:10px; }
.creator-suggestion button { flex-shrink:0; padding:7px 10px; border:1px solid var(--border-color); border-radius:999px; background:var(--text-main); color:var(--card-bg); font-size:10px; font-weight:700; }
.creator-suggestion button.following { background:transparent; color:var(--text-secondary); }
.rail-empty { margin:16px 0 0; color:var(--text-tertiary); font-size:11px; line-height:1.5; }
.rail-footer { display:flex; gap:12px; padding:3px 4px; color:var(--text-tertiary); font-size:10px; }
.rail-footer span { margin-left:auto; }
@media(max-width:980px) { .home-layout { grid-template-columns:minmax(0,680px); } .discovery-rail { display:none; } }
@media(max-width:700px) { .home-layout { display:block; } .feed-intro { align-items:flex-start; padding:3px 1px 17px; } .feed-intro h1 { font-size:34px; } .feed-description { font-size:12px; } .feed-tabs { top:68px; } .explore-link { font-size:11px; } }
@media(max-width:390px) { .feed-intro h1 { font-size:30px; } .feed-description { max-width:255px; } .quick-compose { min-height:58px; padding:8px 10px; gap:9px; } .quick-compose span { font-size:11px; } }
</style>
