<template>
  <div class="user-avatar" role="img" :aria-label="alt || 'Profile picture'">
    <img v-if="imageUrl && !failed" :src="imageUrl" :alt="alt || 'Profile picture'" @error="failed = true" />
    <UserRound v-else :size="iconSize" stroke-width="1.8" aria-hidden="true" />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { UserRound } from 'lucide-vue-next'
import { resolveMediaUrl } from '../utils/media'

const props = defineProps({
  src: { type: String, default: '' },
  alt: { type: String, default: '' },
  iconSize: { type: Number, default: 20 },
})

const failed = ref(false)
const imageUrl = computed(() => resolveMediaUrl(props.src))
watch(imageUrl, () => { failed.value = false })
</script>

<style scoped>
.user-avatar { width:100%; height:100%; display:grid; place-items:center; overflow:hidden; border-radius:inherit; background:var(--icon-bg); color:var(--text-tertiary); }
.user-avatar img { display:block; width:100%; height:100%; object-fit:cover; }
</style>
