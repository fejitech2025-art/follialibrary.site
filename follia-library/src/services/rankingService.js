import { api, websocketUrl } from './api'

export function getRanks(period = 'overall') {
  return api('/api/ranks/?period=' + encodeURIComponent(period))
}

export function subscribeToRanks(onChange) {
  let socket = null
  let timer = null
  let attempts = 0
  let closed = false
  let generation = 0

  function connect() {
    if (closed) return
    const current = ++generation
    try { socket = new WebSocket(websocketUrl('/ws/ranks/')) }
    catch { schedule(); return }
    const activeSocket = socket
    activeSocket.addEventListener('open', () => { if (current === generation) attempts = 0 })
    activeSocket.addEventListener('message', (event) => {
      if (current !== generation) return
      try { if (JSON.parse(event.data)?.type === 'ranking_changed') onChange() } catch {}
    })
    activeSocket.addEventListener('close', (event) => {
      if (current !== generation) return
      socket = null
      if (event.code !== 4401 && event.code !== 4403) schedule()
    })
    activeSocket.addEventListener('error', () => activeSocket.close())
  }

  function schedule() {
    if (closed || timer !== null) return
    attempts += 1
    timer = window.setTimeout(() => { timer = null; connect() }, Math.min(1000 * 2 ** Math.min(attempts, 4), 15000))
  }

  connect()
  const poll = window.setInterval(onChange, 30000)
  return {
    unsubscribe() {
      closed = true
      generation += 1
      window.clearInterval(poll)
      if (timer !== null) window.clearTimeout(timer)
      if (socket && socket.readyState < WebSocket.CLOSING) socket.close(1000, 'Ranks page closed')
    },
  }
}
