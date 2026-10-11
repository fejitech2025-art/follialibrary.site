<template>
  <div class="section-header">
    <div>
      <p v-if="eyebrow" class="section-eyebrow">
        {{ eyebrow }}
      </p>

      <h2>{{ title }}</h2>
    </div>

    <RouterLink v-if="linkText" :to="linkTo" class="section-link">
      {{ linkText }}
      <ArrowRight :size="16" />
    </RouterLink>
  </div>
</template>

<script setup>
import { ArrowRight } from 'lucide-vue-next'

defineProps({
  title: {
    type: String,
    required: true,
  },

  eyebrow: {
    type: String,
    default: '',
  },

  linkText: {
    type: String,
    default: '',
  },

  linkTo: {
    type: String,
    default: '/',
  },
})
</script>
