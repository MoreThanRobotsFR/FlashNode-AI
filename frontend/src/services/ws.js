// src/services/ws.js

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

class WSManager {
  constructor() {
    this.sockets = {}
    this.subscribers = {}
  }

  getSocket(path) {
    if (!this.sockets[path] || this.sockets[path].readyState === WebSocket.CLOSED) {
      this.sockets[path] = new WebSocket(`${WS_BASE_URL}${path}`)
      
      this.sockets[path].onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (this.subscribers[path]) {
            this.subscribers[path].forEach(cb => cb(data))
          }
        } catch(e) {
          console.warn('WS non-JSON payload:', event.data)
        }
      }

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
    if (!this.subscribers[path]) {
      this.subscribers[path] = []
    }
    this.subscribers[path].push(callback)
    
    // Ensure socket is open
    this.getSocket(path)
    
    return () => {
      this.subscribers[path] = this.subscribers[path].filter(cb => cb !== callback)
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
