<template>
  <Transition name="pwa-install">
    <aside
      v-if="canInstall && !isInstalled"
      class="pwa-install"
      aria-label="Install Follia Library"
    >
      <div class="pwa-install-icon">
        <img :src="logo" alt="Follia Library" />
      </div>

      <div class="pwa-install-content">
        <strong>Install Follia Library</strong>
        <span>Get a faster, app-like library experience.</span>
      </div>

      <div class="pwa-install-actions">
        <button type="button" class="pwa-install-button" @click="handleInstall">Install</button>

        <button
          type="button"
          class="pwa-dismiss"
          aria-label="Dismiss install prompt"
          @click="dismissInstallPrompt"
        >
          <X :size="18" />
        </button>
      </div>
    </aside>
  </Transition>
</template>

<script setup>
import { X } from 'lucide-vue-next'
import logo from '../assets/logo/image.png'
import { usePwaInstall } from '../composables/usePwaInstall'

const { canInstall, isInstalled, installPwa, dismissInstallPrompt } = usePwaInstall()

async function handleInstall() {
  await installPwa()
}
</script>

<style scoped>
.pwa-install {
  position: fixed;
  left: 24px;
  right: 24px;
  bottom: 24px;
  z-index: 9999;

  display: flex;
  align-items: center;
  gap: 14px;

  max-width: 520px;
  margin: 0 auto;

  padding: 14px 16px;

  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 18px;

  box-shadow: 0 14px 40px var(--shadow-color);

  color: var(--text-main);
}

.pwa-install-icon {
  flex: 0 0 46px;
  width: 46px;
  height: 46px;

  display: flex;
  align-items: center;
  justify-content: center;

  overflow: hidden;
  border-radius: 12px;

  background: var(--card-soft);
}

.pwa-install-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.pwa-install-content {
  min-width: 0;
  flex: 1;

  display: flex;
  flex-direction: column;
  gap: 3px;
}

.pwa-install-content strong {
  font-size: 14px;
  font-weight: 750;
  line-height: 1.25;
}

.pwa-install-content span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.4;
}

.pwa-install-actions {
  flex: 0 0 auto;

  display: flex;
  align-items: center;
  gap: 6px;
}

.pwa-install-button {
  border: 0;
  border-radius: 10px;

  padding: 9px 14px;

  background: var(--primary-bg);
  color: var(--primary-text);

  font: inherit;
  font-size: 12px;
  font-weight: 750;

  cursor: pointer;
  white-space: nowrap;

  transition:
    transform 0.18s ease,
    opacity 0.18s ease;
}

.pwa-install-button:hover {
  opacity: 0.9;
}

.pwa-install-button:active {
  transform: scale(0.97);
}

.pwa-dismiss {
  width: 32px;
  height: 32px;

  display: flex;
  align-items: center;
  justify-content: center;

  border: 0;
  border-radius: 9px;

  background: transparent;
  color: var(--text-secondary);

  cursor: pointer;
}

.pwa-dismiss:hover {
  background: var(--card-soft);
  color: var(--text-main);
}

/* Transition */

.pwa-install-enter-active,
.pwa-install-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease;
}

.pwa-install-enter-from,
.pwa-install-leave-to {
  opacity: 0;
  transform: translateY(18px);
}

/* Mobile */

@media (max-width: 640px) {
  .pwa-install {
    left: 12px;
    right: 12px;
    bottom: 12px;

    padding: 12px;
    border-radius: 16px;
  }

  .pwa-install-icon {
    width: 42px;
    height: 42px;
    flex-basis: 42px;
  }

  .pwa-install-content strong {
    font-size: 13px;
  }

  .pwa-install-content span {
    font-size: 11px;
  }

  .pwa-install-button {
    padding: 8px 11px;
  }
}
</style>
