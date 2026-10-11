<template>
  <div class="app-shell">
    <AppHeader />

    <main class="main-content">
      <slot />
    </main>

    <BottomNav />
    <PwaInstallPrompt />
  </div>
</template>

<script setup>
import AppHeader from '../components/AppHeader.vue'
import BottomNav from '../components/BottomNav.vue'
import PwaInstallPrompt from '../components/PwaInstallPrompt.vue'
</script>
