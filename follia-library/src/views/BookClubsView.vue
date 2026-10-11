```vue
<template>
  <MainLayout>
    <section class="clubs-page">
      <div class="clubs-heading">
        <div class="clubs-heading-content">
          <p class="page-kicker">COMMUNITIES</p>

          <h1>Read together.</h1>

          <p class="clubs-description">
            Find your people, share a reading list and keep the conversation going.
          </p>
        </div>

        <div class="club-mark" aria-hidden="true">
          <UsersRound :size="24" />
        </div>
      </div>

      <BookClubExplorer />
    </section>
  </MainLayout>
</template>

<script setup>
import { UsersRound } from 'lucide-vue-next'

import MainLayout from '../layouts/MainLayout.vue'
import BookClubExplorer from '../components/BookClubExplorer.vue'
</script>

<style scoped>
.clubs-page {
  width: 100%;
  max-width: 1040px;
  margin: 0 auto;
  padding-bottom: 34px;
}

.clubs-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin: 5px 0 34px;
}

.clubs-heading-content {
  min-width: 0;
}

.page-kicker {
  margin: 0 0 10px;
  color: var(--text-tertiary);
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.15em;
}

.clubs-heading h1 {
  margin: 0;
  font-family: Manrope, sans-serif;
  font-size: clamp(34px, 5vw, 52px);
  letter-spacing: -0.055em;
}

.clubs-description {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.club-mark {
  width: 58px;
  height: 58px;
  flex: 0 0 58px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  color: var(--primary-text);
  background: var(--primary-bg);
}

@media (max-width: 520px) {
  .clubs-heading {
    align-items: flex-start;
    gap: 16px;
  }

  .club-mark {
    width: 48px;
    height: 48px;
    flex-basis: 48px;
    border-radius: 15px;
  }
}
</style>
```