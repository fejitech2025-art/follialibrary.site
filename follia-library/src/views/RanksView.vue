<template>
  <MainLayout>
    <main class="ranks-page">
      <header class="ranks-header">
        <div>
          <p class="ranks-kicker">FOLLIA COMMUNITY</p>
          <h1>Ranks <span>✦</span></h1>
          <p class="ranks-intro">A little recognition for showing up, sharing what you know, and helping ideas travel.</p>
        </div>
        <div class="period-switch" role="tablist" aria-label="Leaderboard period">
          <button :class="{ active: period === 'daily' }" @click="selectPeriod('daily')">Today</button>
          <button :class="{ active: period === 'overall' }" @click="selectPeriod('overall')">All time</button>
        </div>
      </header>

      <section v-if="!loading && !error && me" class="my-rank-card">
        <div class="my-rank-avatar"><UserAvatar :src="profile?.avatar_url || profile?.avatar" :alt="profile?.display_name || 'Your profile picture'" :icon-size="22" /></div>
        <div class="my-rank-copy"><span>YOUR PLACE</span><strong>{{ me.rank ? `#${me.rank}` : 'Unranked' }}</strong></div>
        <div class="my-rank-score"><strong>{{ me.score }}</strong><span>points {{ period === 'daily' ? 'today' : 'overall' }}</span></div>
        <RouterLink to="/create" class="rank-contribute">Share an idea <ArrowUpRight :size="16" /></RouterLink>
      </section>

      <section v-if="loading" class="rank-state" aria-label="Loading leaderboard"><LoaderCircle :size="25" class="spin" /><p>Finding the community leaders...</p></section>
      <section v-else-if="error" class="rank-state rank-error" role="alert"><Trophy :size="25" /><h2>Ranks are taking a moment.</h2><p>{{ error }}</p><button @click="loadRanks">Try again</button></section>
      <section v-else-if="!leaders.length" class="rank-state rank-empty"><div class="empty-trophy">✦</div><h2>The first chapter is yours.</h2><p>Share something useful and the leaderboard will grow with you.</p><RouterLink to="/create">Publish your first post <ArrowUpRight :size="15" /></RouterLink></section>
      <template v-else>
        <section v-if="leaders.length >= 3" class="podium" aria-label="Top three community ranks">
          <article v-for="person in podium" :key="person.user_id" class="podium-card" :class="`place-${person.rank}`">
            <div class="podium-crown" aria-hidden="true">{{ person.rank === 1 ? '👑' : person.rank === 2 ? '🥈' : '🥉' }}</div>
            <RouterLink :to="{ name: 'publisher-detail', params: { id: person.user_id } }" class="podium-avatar">
              <UserAvatar :src="person.avatar_url" :alt="person.display_name + ' profile picture'" :icon-size="30" />
            </RouterLink>
            <span class="podium-rank">#{{ person.rank }}</span>
            <RouterLink :to="{ name: 'publisher-detail', params: { id: person.user_id } }" class="podium-name">{{ person.display_name }}</RouterLink>
            <small>@{{ person.username }}</small>
            <strong class="podium-score">{{ person.score.toLocaleString() }} <span>pts</span></strong>
          </article>
        </section>

        <section v-if="rest.length" class="leaderboard-panel">
          <div class="leaderboard-heading"><div><p>THE COMMUNITY</p><h2>{{ period === 'daily' ? 'Today’s standouts' : 'Keep rising' }}</h2></div><span>Updates live <i></i></span></div>
          <TransitionGroup name="rank-row" tag="div" class="leaderboard-list">
            <article v-for="person in rest" :key="person.user_id" class="leader-row" :class="{ 'is-me': person.is_me }">
              <span class="row-rank">{{ person.rank }}</span>
              <RouterLink :to="{ name: 'publisher-detail', params: { id: person.user_id } }" class="row-avatar"><UserAvatar :src="person.avatar_url" :alt="person.display_name + ' profile picture'" :icon-size="18" /></RouterLink>
              <RouterLink :to="{ name: 'publisher-detail', params: { id: person.user_id } }" class="row-person"><strong>{{ person.display_name }} <span v-if="person.is_me">YOU</span></strong><small>@{{ person.username }}</small></RouterLink>
              <strong class="row-score">{{ person.score.toLocaleString() }} <small>pts</small></strong>
            </article>
          </TransitionGroup>
        </section>

        <section v-if="leaders.length < 3" class="leaderboard-panel compact-leaderboard">
          <div class="leaderboard-heading"><div><p>THE COMMUNITY</p><h2>{{ period === 'daily' ? 'Today’s standouts' : 'Keep rising' }}</h2></div><span>Updates live <i></i></span></div>
          <TransitionGroup name="rank-row" tag="div" class="leaderboard-list">
            <article v-for="person in leaders" :key="person.user_id" class="leader-row" :class="{ 'is-me': person.is_me }">
              <span class="row-rank">{{ person.rank }}</span><RouterLink :to="{ name: 'publisher-detail', params: { id: person.user_id } }" class="row-avatar"><UserAvatar :src="person.avatar_url" :alt="person.display_name + ' profile picture'" :icon-size="18" /></RouterLink>
              <RouterLink :to="{ name: 'publisher-detail', params: { id: person.user_id } }" class="row-person"><strong>{{ person.display_name }} <span v-if="person.is_me">YOU</span></strong><small>@{{ person.username }}</small></RouterLink><strong class="row-score">{{ person.score.toLocaleString() }} <small>pts</small></strong>
            </article>
          </TransitionGroup>
        </section>
      </template>

      <aside class="rank-rules"><span class="rules-icon">✧</span><div><strong>How points grow</strong><p>Publish a post <b>+{{ rules.post }}</b> · Receive a real like <b>+{{ rules.like_received }}</b> · Write a thoughtful comment <b>+{{ rules.comment_written }}</b>. Comments count up to {{ rules.comment_daily_limit }} times a day. Your own likes and short comments do not earn points.</p></div></aside>
    </main>
  </MainLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArrowUpRight, LoaderCircle, Trophy } from 'lucide-vue-next'
import MainLayout from '../layouts/MainLayout.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { getMyProfile } from '../services/profileService'
import { getRanks, subscribeToRanks } from '../services/rankingService'

const period = ref('overall')
const leaders = ref([])
const me = ref(null)
const profile = ref(null)
const loading = ref(true)
const error = ref('')
const rules = ref({ post: 10, like_received: 2, comment_written: 1, comment_daily_limit: 10 })
const podium = computed(() => [leaders.value[1], leaders.value[0], leaders.value[2]].filter(Boolean))
const rest = computed(() => leaders.value.slice(3))
let requestId = 0
let subscription = null

async function loadRanks() {
  const current = ++requestId
  loading.value = true
  error.value = ''
  try {
    const response = await getRanks(period.value)
    if (current !== requestId) return
    leaders.value = response.leaderboard || []
    me.value = response.me
    rules.value = response.rules || rules.value
  } catch (err) {
    if (current === requestId) error.value = err.message || 'The leaderboard is unavailable.'
  } finally {
    if (current === requestId) loading.value = false
  }
}

function selectPeriod(value) { if (period.value !== value) period.value = value }
watch(period, loadRanks)
onMounted(async () => {
  try { profile.value = await getMyProfile() } catch {}
  await loadRanks()
  subscription = subscribeToRanks(() => loadRanks())
})
onBeforeUnmount(() => { requestId += 1; subscription?.unsubscribe() })
</script>

<style scoped>
.ranks-page { width:min(930px,100%); margin:0 auto; padding-bottom:35px; }
.ranks-header { display:flex; justify-content:space-between; align-items:end; gap:25px; margin:5px 0 25px; }
.ranks-kicker,.leaderboard-heading p { margin:0 0 8px; color:var(--text-tertiary); font-size:10px; font-weight:800; letter-spacing:.15em; }
.ranks-header h1 { margin:0; font:850 clamp(36px,6vw,56px)/1 Manrope,sans-serif; letter-spacing:-.06em; }
.ranks-header h1 span { color:var(--accent); font-size:.65em; }
.ranks-intro { max-width:530px; margin:11px 0 0; color:var(--text-secondary); font-size:14px; line-height:1.6; }
.period-switch { display:flex; gap:4px; padding:4px; border:1px solid var(--border-color); border-radius:14px; background:var(--card-bg); }
.period-switch button { min-height:38px; padding:0 13px; border-radius:10px; background:transparent; color:var(--text-secondary); font-size:11px; font-weight:700; }
.period-switch button.active { background:var(--primary-bg); color:var(--primary-text); }
.my-rank-card { display:flex; align-items:center; gap:13px; margin-bottom:24px; padding:14px 17px; border:1px solid color-mix(in srgb,var(--accent) 35%,var(--border-color)); border-radius:17px; background:linear-gradient(110deg,color-mix(in srgb,var(--accent) 12%,var(--card-bg)),var(--card-bg) 65%); }
.my-rank-avatar,.podium-avatar,.row-avatar { display:grid; place-items:center; overflow:hidden; border-radius:50%; background:var(--icon-bg); }
.my-rank-avatar { width:43px; height:43px; flex:0 0 43px; }
.my-rank-avatar img,.podium-avatar img,.row-avatar img { width:100%; height:100%; object-fit:cover; }
.my-rank-copy { display:grid; gap:2px; }.my-rank-copy span { color:var(--text-tertiary); font-size:9px; font-weight:800; letter-spacing:.1em; }.my-rank-copy strong { font:800 16px Manrope,sans-serif; }
.my-rank-score { display:grid; gap:1px; margin-left:auto; text-align:right; }.my-rank-score strong { font-size:17px; font-weight:850; }.my-rank-score span { color:var(--text-tertiary); font-size:10px; }
.rank-contribute { min-height:38px; display:inline-flex; align-items:center; gap:7px; margin-left:12px; padding:0 12px; border-radius:11px; background:var(--primary-bg); color:var(--primary-text); font-size:11px; font-weight:750; }
.podium { display:grid; grid-template-columns:1fr 1.12fr 1fr; align-items:end; gap:13px; margin:10px 0 28px; }
.podium-card { position:relative; min-width:0; min-height:245px; display:flex; flex-direction:column; align-items:center; padding:26px 12px 18px; border:1px solid var(--border-color); border-radius:22px; background:linear-gradient(155deg,var(--card-bg),var(--card-soft)); box-shadow:0 12px 38px var(--shadow-color); text-align:center; animation:podium-in .45s cubic-bezier(.2,.8,.2,1) both; }
.podium-card.place-1 { min-height:286px; padding-top:35px; border-color:color-mix(in srgb,#e8c547 65%,var(--border-color)); background:radial-gradient(ellipse at 50% 0,color-mix(in srgb,#efcc53 20%,var(--card-bg)),var(--card-bg) 60%); box-shadow:0 18px 48px color-mix(in srgb,#d2a82b 18%,var(--shadow-color)); }
.podium-card.place-2 { border-color:color-mix(in srgb,#b8c0cc 50%,var(--border-color)); }.podium-card.place-3 { border-color:color-mix(in srgb,#bd8256 50%,var(--border-color)); }
.podium-crown { position:absolute; top:-16px; left:50%; transform:translateX(-50%); font-size:24px; filter:drop-shadow(0 4px 9px rgba(0,0,0,.14)); }
.podium-avatar { width:68px; height:68px; border:3px solid color-mix(in srgb,var(--accent) 70%,var(--card-bg)); box-shadow:0 0 0 5px color-mix(in srgb,var(--accent) 15%,transparent); }
.place-2 .podium-avatar { border-color:#b7c0ce; box-shadow:0 0 0 5px rgba(183,192,206,.15); }.place-3 .podium-avatar { border-color:#bd8256; box-shadow:0 0 0 5px rgba(189,130,86,.14); }
.podium-rank { margin-top:11px; color:var(--text-tertiary); font-size:10px; font-weight:850; letter-spacing:.1em; }.podium-name { max-width:100%; margin-top:4px; overflow:hidden; color:var(--text-main); font:800 16px Manrope,sans-serif; text-overflow:ellipsis; white-space:nowrap; }.podium-card small { max-width:100%; margin-top:3px; overflow:hidden; color:var(--text-tertiary); font-size:10px; text-overflow:ellipsis; white-space:nowrap; }
.podium-score { margin-top:14px; color:var(--text-main); font-size:18px; font-weight:850; }.podium-score span { color:var(--text-tertiary); font-size:10px; font-weight:650; }
.leaderboard-panel { overflow:hidden; border:1px solid var(--border-color); border-radius:20px; background:var(--card-bg); box-shadow:0 8px 26px var(--shadow-color); }
.leaderboard-heading { display:flex; justify-content:space-between; align-items:center; gap:20px; padding:21px 22px 15px; border-bottom:1px solid var(--border-soft); }.leaderboard-heading p { margin-bottom:4px; font-size:9px; }.leaderboard-heading h2 { margin:0; font:800 20px Manrope,sans-serif; letter-spacing:-.03em; }.leaderboard-heading > span { display:inline-flex; align-items:center; gap:7px; color:var(--text-tertiary); font-size:10px; }.leaderboard-heading i { width:7px; height:7px; border-radius:50%; background:#78c99b; box-shadow:0 0 0 3px rgba(120,201,155,.12); }
.leaderboard-list { display:grid; }.leader-row { min-height:70px; display:flex; align-items:center; gap:13px; padding:10px 20px; border-bottom:1px solid var(--border-soft); transition:background .2s, transform .22s; }.leader-row:last-child { border-bottom:0; }.leader-row:hover { background:var(--card-soft); }.leader-row.is-me { background:color-mix(in srgb,var(--accent) 9%,var(--card-bg)); }
.row-rank { width:24px; flex:0 0 24px; color:var(--text-tertiary); font-size:12px; font-weight:800; text-align:center; }.row-avatar { width:42px; height:42px; flex:0 0 42px; }.row-person { min-width:0; display:grid; gap:3px; }.row-person strong { overflow:hidden; color:var(--text-main); font-size:12px; text-overflow:ellipsis; white-space:nowrap; }.row-person strong span { margin-left:5px; padding:3px 5px; border-radius:5px; background:var(--accent); color:#111; font-size:8px; }.row-person small { color:var(--text-tertiary); font-size:10px; }.row-score { margin-left:auto; white-space:nowrap; font-size:13px; font-weight:850; }.row-score small { color:var(--text-tertiary); font-size:9px; font-weight:650; }
.rank-row-move { transition:transform .35s cubic-bezier(.2,.8,.2,1); }.rank-row-enter-active,.rank-row-leave-active { transition:opacity .2s,transform .2s; }.rank-row-enter-from,.rank-row-leave-to { opacity:0; transform:translateY(8px); }
.rank-state { min-height:250px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:10px; padding:28px; border:1px solid var(--border-color); border-radius:20px; background:var(--card-bg); color:var(--text-tertiary); text-align:center; }.rank-state p { max-width:420px; margin:0; color:var(--text-secondary); font-size:12px; line-height:1.6; }.rank-state h2 { margin:4px 0 0; color:var(--text-main); font:800 21px Manrope,sans-serif; }.rank-error button,.rank-empty a { min-height:38px; display:inline-flex; align-items:center; gap:7px; margin-top:7px; padding:0 13px; border-radius:11px; background:var(--primary-bg); color:var(--primary-text); font-size:11px; font-weight:750; }.empty-trophy { width:52px; height:52px; display:grid; place-items:center; border-radius:16px; background:color-mix(in srgb,var(--accent) 25%,var(--card-bg)); color:#a99700; font-size:27px; }
.rank-rules { display:flex; gap:12px; margin-top:19px; padding:15px 17px; border:1px solid var(--border-color); border-radius:16px; background:var(--card-soft); }.rules-icon { color:#b49b14; font-size:20px; }.rank-rules strong { font-size:11px; }.rank-rules p { margin:4px 0 0; color:var(--text-secondary); font-size:10px; line-height:1.6; }.rank-rules b { color:var(--text-main); }
.spin { animation:spin 1s linear infinite; } @keyframes spin { to { transform:rotate(360deg); } } @keyframes podium-in { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
@media(max-width:650px) { .ranks-header { align-items:flex-start; flex-direction:column; gap:16px; }.ranks-intro { font-size:12px; }.period-switch { width:100%; }.period-switch button { flex:1; }.podium { gap:7px; }.podium-card { min-height:216px; padding:23px 7px 13px; border-radius:17px; }.podium-card.place-1 { min-height:248px; padding-top:30px; }.podium-avatar { width:56px; height:56px; }.podium-name { font-size:12px; }.podium-card small { font-size:9px; }.podium-score { font-size:14px; }.leaderboard-heading { padding:17px 15px 13px; }.leader-row { min-height:64px; gap:9px; padding:9px 12px; }.row-avatar { width:37px; height:37px; flex-basis:37px; }.my-rank-card { flex-wrap:wrap; }.rank-contribute { margin-left:auto; }.my-rank-score { margin-left:auto; } }
@media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms!important; animation-iteration-count:1!important; scroll-behavior:auto!important; transition-duration:.01ms!important; } }
</style>
