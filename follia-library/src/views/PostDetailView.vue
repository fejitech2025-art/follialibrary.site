<template>
  <MainLayout>
    <section class="post-detail">
      <RouterLink to="/" class="back"><ArrowLeft :size="17" /> Back to feed</RouterLink>
      <div v-if="loading" class="state"><LoaderCircle :size="23" class="spin" /> Loading post…</div>
      <div v-else-if="error" class="state"><h2>Post unavailable</h2><p>{{ error }}</p><RouterLink to="/explore">Keep exploring</RouterLink></div>
      <FeedItemCard v-else-if="post" :item="{ ...post, kind: 'post' }" />
    </section>
  </MainLayout>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, LoaderCircle } from 'lucide-vue-next'
import MainLayout from '../layouts/MainLayout.vue'
import FeedItemCard from '../components/FeedItemCard.vue'
import { getPost } from '../services/postService'

const route = useRoute()
const post = ref(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try { post.value = await getPost(route.params.id) }
  catch (err) { error.value = err.message || 'We could not find this post.' }
  finally { loading.value = false }
}
watch(() => route.params.id, load)
onMounted(load)
</script>

<style scoped>
.post-detail { width:min(680px,100%); margin:0 auto; padding-bottom:28px; }
.back { display:inline-flex; align-items:center; gap:7px; margin:4px 0 17px; color:var(--text-secondary); font-size:12px; font-weight:650; }
.state { min-height:230px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:9px; border:1px solid var(--border-color); border-radius:18px; background:var(--card-bg); color:var(--text-secondary); text-align:center; }
.state h2 { margin:0; color:var(--text-main); }
.state p { margin:0; font-size:12px; }
.state a { color:var(--text-main); font-size:12px; font-weight:700; }
.spin { animation:spin 1s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
</style>
