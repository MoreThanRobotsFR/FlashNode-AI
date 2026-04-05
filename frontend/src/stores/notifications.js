import { defineStore } from 'pinia'
import { ref } from 'vue'

let _nextId = 1

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref([])

  function notify(message, type = 'info', duration = 4000) {
    const id = _nextId++
    notifications.value.push({ id, message, type, visible: true })

    if (duration > 0) {
      setTimeout(() => dismiss(id), duration)
    }
    
    // Cap at 6 visible
    if (notifications.value.length > 6) {
      notifications.value.shift()
    }

    return id
  }

  function success(message, duration = 3000) {
    return notify(message, 'success', duration)
  }

  function error(message, duration = 6000) {
    return notify(message, 'error', duration)
  }

  function warning(message, duration = 5000) {
    return notify(message, 'warning', duration)
  }

  function info(message, duration = 4000) {
    return notify(message, 'info', duration)
  }

  function dismiss(id) {
    const idx = notifications.value.findIndex(n => n.id === id)
    if (idx !== -1) {
      notifications.value[idx].visible = false
      setTimeout(() => {
        notifications.value = notifications.value.filter(n => n.id !== id)
      }, 300) // allow exit animation
    }
  }

  return { notifications, notify, success, error, warning, info, dismiss }
})
