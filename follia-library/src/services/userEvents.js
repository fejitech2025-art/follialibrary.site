import { websocketUrl } from './api'

const listeners = new Set()
let socket = null
let reconnectTimer = null
let attempts = 0
let stopped = true
let generation = 0

function connect() {
  if (stopped || !listeners.size) return
  const currentGeneration = ++generation
  try {
    socket = new WebSocket(websocketUrl('/ws/messages/'))
  } catch {
    scheduleReconnect()
    return
  }
  const currentSocket = socket
  currentSocket.addEventListener('open', () => {
    if (currentGeneration === generation) attempts = 0
  })
  currentSocket.addEventListener('message', (event) => {
    if (currentGeneration !== generation) return
    try {
      const payload = JSON.parse(event.data)
      for (const listener of listeners) listener(payload)
    } catch (error) {
      console.error('Unable to read a live Follia event.', error)
    }
  })
  currentSocket.addEventListener('close', (event) => {
    if (currentGeneration !== generation) return
    socket = null
    if (event.code !== 4401 && event.code !== 4403) scheduleReconnect()
  })
  currentSocket.addEventListener('error', () => currentSocket.close())
}

function scheduleReconnect() {
  if (stopped || reconnectTimer !== null || !listeners.size) return
  attempts += 1
  const delay = Math.min(1000 * 2 ** Math.min(attempts - 1, 4), 15000)
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    connect()
  }, delay)
}

function stop() {
  stopped = true
  generation += 1
  if (reconnectTimer !== null) window.clearTimeout(reconnectTimer)
  reconnectTimer = null
  const currentSocket = socket
  socket = null
  if (currentSocket && currentSocket.readyState < WebSocket.CLOSING) currentSocket.close(1000, 'No event listeners')
}

export function subscribeUserEvents(listener) {
  listeners.add(listener)
  if (stopped) {
    stopped = false
    connect()
  }
  return {
    unsubscribe() {
      listeners.delete(listener)
      if (!listeners.size) stop()
    },
    get socket() { return socket },
    send(payload) {
      if (socket?.readyState !== WebSocket.OPEN) return false
      socket.send(JSON.stringify(payload))
      return true
    },
  }
}
