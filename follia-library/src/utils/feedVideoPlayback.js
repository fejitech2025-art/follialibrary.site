const videoStates = new WeakMap()
let activeVideo = null

function stateFor(video) {
  let state = videoStates.get(video)
  if (!state) {
    state = {
      visible: false,
      manualPause: false,
      internalPauses: 0,
      playGeneration: 0,
      pendingAutoPlay: false,
      staleAutoPlay: false,
    }
    videoStates.set(video, state)
  }
  return state
}

function pauseForCoordinator(video) {
  if (!video) return
  const state = stateFor(video)
  state.playGeneration += 1
  if (state.pendingAutoPlay) {
    state.pendingAutoPlay = false
    state.staleAutoPlay = true
  }
  if (!video.paused) {
    state.internalPauses += 1
    video.pause()
  }
}

function claim(video) {
  if (activeVideo && activeVideo !== video) pauseForCoordinator(activeVideo)
  activeVideo = video
}

export function autoplayFeedVideo(video) {
  if (!video) return
  const state = stateFor(video)
  state.visible = true
  if (state.manualPause) return

  claim(video)
  video.muted = true
  video.playsInline = true

  const generation = ++state.playGeneration
  state.pendingAutoPlay = true
  state.staleAutoPlay = false
  video.play().then(() => {
    if (
      generation !== state.playGeneration ||
      activeVideo !== video ||
      !state.visible ||
      state.manualPause
    ) {
      pauseForCoordinator(video)
    }
  }).catch(() => {
    if (generation === state.playGeneration) state.pendingAutoPlay = false
  })
}

export function handleFeedVideoPlay(video) {
  if (!video) return
  const state = stateFor(video)

  if (state.pendingAutoPlay) {
    state.pendingAutoPlay = false
    if (!state.visible || state.manualPause || activeVideo !== video) pauseForCoordinator(video)
    return
  }

  if (state.staleAutoPlay) {
    state.staleAutoPlay = false
    if (!state.visible || state.manualPause || activeVideo !== video) {
      pauseForCoordinator(video)
      return
    }
  }

  state.manualPause = false
  state.visible = true
  claim(video)
}

export function handleFeedVideoPause(video) {
  if (!video) return
  const state = stateFor(video)
  if (state.internalPauses) {
    state.internalPauses -= 1
    return
  }
  state.pendingAutoPlay = false
  state.manualPause = true
  if (activeVideo === video) activeVideo = null
}

export function leaveFeedVideo(video) {
  if (!video) return
  const state = stateFor(video)
  state.visible = false
  state.manualPause = false
  if (activeVideo === video) activeVideo = null
  pauseForCoordinator(video)
}
