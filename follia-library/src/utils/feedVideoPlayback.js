
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
  if (activeVideo && activeVideo !== video) {
    pauseForCoordinator(activeVideo)
  }

  activeVideo = video
}

export function autoplayFeedVideo(video) {
  if (!video) return

  const state = stateFor(video)

  state.visible = true

  // Do not restart a video the user manually paused.
  if (state.manualPause) return

  // Pause any other feed video before playing this one.
  claim(video)

  // Allow inline playback on mobile.
  video.playsInline = true

  // Do not force the video to be muted.
  // Preserve the current sound preference.

  const generation = ++state.playGeneration

  state.pendingAutoPlay = true
  state.staleAutoPlay = false

  video.play()
    .then(() => {
      // Stop playback if the video is no longer the active,
      // visible video, or the user has paused it.
      if (
        generation !== state.playGeneration ||
        activeVideo !== video ||
        !state.visible ||
        state.manualPause
      ) {
        pauseForCoordinator(video)
      }
    })
    .catch(() => {
      // Browsers may block autoplay with sound.
      // The user can press Play to start playback.
      if (generation === state.playGeneration) {
        state.pendingAutoPlay = false
      }
    })
}

export function handleFeedVideoPlay(video) {
  if (!video) return

  const state = stateFor(video)

  if (state.pendingAutoPlay) {
    state.pendingAutoPlay = false

    if (
      !state.visible ||
      state.manualPause ||
      activeVideo !== video
    ) {
      pauseForCoordinator(video)
    }

    return
  }

  if (state.staleAutoPlay) {
    state.staleAutoPlay = false

    if (
      !state.visible ||
      state.manualPause ||
      activeVideo !== video
    ) {
      pauseForCoordinator(video)
      return
    }
  }

  // The user has started playback manually.
  state.manualPause = false
  state.visible = true

  claim(video)
}

export function handleFeedVideoPause(video) {
  if (!video) return

  const state = stateFor(video)

  // Ignore pauses triggered internally when switching videos
  // or scrolling away from a video.
  if (state.internalPauses > 0) {
    state.internalPauses -= 1
    return
  }

  // Treat a normal pause event as the user's pause action.
  state.pendingAutoPlay = false
  state.manualPause = true

  if (activeVideo === video) {
    activeVideo = null
  }
}

export function leaveFeedVideo(video) {
  if (!video) return

  const state = stateFor(video)

  state.visible = false
  state.manualPause = false

  if (activeVideo === video) {
    activeVideo = null
  }

  // Pause the video when it leaves the visible feed area.
  pauseForCoordinator(video)
}
