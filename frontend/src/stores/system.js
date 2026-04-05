import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'
import { wsManager } from '../services/ws'

export const useSystemStore = defineStore('system', () => {
  const cpu = ref(0)
  const ram = ref(0)
  const ramMax = ref(16000)
  const temp = ref(0)
  const uptime = ref('')
  const ip = ref('')
  const lastOp = ref('')

  const uptimeFormatted = computed(() => {
    if (!uptime.value) return '...'
    // uptime.value can be a seconds timestamp or a formatted string
    return uptime.value
  })

  async function fetchStatus() {
    try {
      const res = await api.get('/system/status')
      updateFromREST(res.data)
    } catch (err) {
      console.error('Failed to fetch system status', err)
    }
  }

  function updateFromREST(data) {
    if (data.cpu_percent !== undefined) cpu.value = Math.round(data.cpu_percent)
    if (data.memory_used_mb !== undefined) ram.value = data.memory_used_mb
    if (data.memory_total_mb !== undefined) ramMax.value = data.memory_total_mb
    if (data.memory_percent !== undefined && !data.memory_used_mb) {
      // Fallback: derive from percent
      ram.value = Math.round((data.memory_percent / 100) * ramMax.value)
    }
    if (data.temperature_c !== undefined && data.temperature_c !== null) temp.value = data.temperature_c
    if (data.ip !== undefined) ip.value = data.ip

    // Format uptime from boot timestamp
    if (data.uptime_s !== undefined) {
      const now = Date.now() / 1000
      const uptimeSec = now - data.uptime_s
      if (uptimeSec > 0) {
        const days = Math.floor(uptimeSec / 86400)
        const hours = Math.floor((uptimeSec % 86400) / 3600)
        const mins = Math.floor((uptimeSec % 3600) / 60)
        uptime.value = days > 0 ? `${days}j ${hours}h` : `${hours}h ${mins}m`
      }
    }
  }

  function updateFromWS(data) {
    // WS /system sends: { cpu, ram_mb, ram_total_mb, temp_c }
    if (data.cpu !== undefined) cpu.value = Math.round(data.cpu)
    if (data.ram_mb !== undefined) ram.value = data.ram_mb
    if (data.ram_total_mb !== undefined) ramMax.value = data.ram_total_mb
    if (data.temp_c !== undefined && data.temp_c !== null) temp.value = data.temp_c
  }

  let wsUnsubscribe = null
  function initRealtime() {
    if (!wsUnsubscribe) {
      wsUnsubscribe = wsManager.subscribe('/system', (data) => {
        updateFromWS(data)
      })
    }
  }

  return { cpu, ram, ramMax, temp, uptime, ip, uptimeFormatted, fetchStatus, initRealtime }
})
