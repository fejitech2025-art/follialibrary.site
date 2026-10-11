import { ref, onMounted, onBeforeUnmount } from 'vue'

const deferredPrompt = ref(null)
const canInstall = ref(false)
const isInstalled = ref(false)

function checkIfInstalled() {
  return (
    window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true
  )
}

function handleBeforeInstallPrompt(event) {
  event.preventDefault()

  deferredPrompt.value = event

  if (!checkIfInstalled()) {
    canInstall.value = true
  }
}

function handleAppInstalled() {
  deferredPrompt.value = null
  canInstall.value = false
  isInstalled.value = true
}

export function usePwaInstall() {
  onMounted(() => {
    isInstalled.value = checkIfInstalled()

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

    window.addEventListener('appinstalled', handleAppInstalled)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

    window.removeEventListener('appinstalled', handleAppInstalled)
  })

  async function installPwa() {
    if (!deferredPrompt.value) {
      return false
    }

    const promptEvent = deferredPrompt.value

    promptEvent.prompt()

    const { outcome } = await promptEvent.userChoice

    deferredPrompt.value = null
    canInstall.value = false

    if (outcome === 'accepted') {
      isInstalled.value = true
      return true
    }

    return false
  }

  function dismissInstallPrompt() {
    canInstall.value = false
  }

  return {
    canInstall,
    isInstalled,
    installPwa,
    dismissInstallPrompt,
  }
}
