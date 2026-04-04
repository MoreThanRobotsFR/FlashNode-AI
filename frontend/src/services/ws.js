// src/services/ws.js

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

class WSManager {
  constructor() {
    this.sockets = {}
  }

  getSocket(path) {
    if (!this.sockets[path] || this.sockets[path].readyState === WebSocket.CLOSED) {
      this.sockets[path] = new WebSocket(`${WS_BASE_URL}${path}`)
      
      this.sockets[path].onclose = () => {
        console.log(`WebSocket closed: ${path}. Reconnecting in 3s...`)
        setTimeout(() => this.getSocket(path), 3000)
      }
      
      this.sockets[path].onerror = (err) => {
        console.error(`WebSocket Error on ${path}:`, err)
      }
      
      this.sockets[path].onopen = () => {
         console.log(`WebSocket connected: ${path}`)
      }
    }
    return this.sockets[path]
  }

  // Subscribe to JSON messages from a specific WebSocket path
  subscribe(path, callback) {
    const ws = this.getSocket(path)
    
    if (!ws.subscribers) {
      ws.subscribers = []
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          ws.subscribers.forEach(cb => cb(data))
        } catch(e) {
          console.warn('WS non-JSON payload:', event.data)
        }
      }
    }
    ws.subscribers.push(callback)
    
    return () => {
      ws.subscribers = ws.subscribers.filter(cb => cb !== callback)
    }
  }

  closeAll() {
    Object.values(this.sockets).forEach(ws => {
      ws.onclose = null // Prevent auto-reconnect on explicit close
      ws.close()
    })
    this.sockets = {}
  }
}

export const wsManager = new WSManager()
