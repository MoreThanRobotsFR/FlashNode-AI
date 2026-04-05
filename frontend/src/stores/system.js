import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'
import { wsManager } from '../services/ws'

export const useSystemStore = defineStore('system', () => {
  const cpu = ref(0)
  const ram = ref(0)
  const ramMax = ref(16000)
  const temp = ref(0)
  const uptime = ref('')
  
  async function fetchStatus() {
    try {
      const res = await api.get('/system/status')
      updateFromPayload(res.data)
    } catch (err) {
      console.error('Failed to fetch system status', err)
    }
  }

  function updateFromPayload(data) {
    if (data.cpu_percent !== undefined) cpu.value = data.cpu_percent
    if (data.memory_percent !== undefined) {
      // Backend returns % only, let's derive approx absolute usage if max is known
      ram.value = (data.memory_percent / 100) * ramMax.value
    }
    if (data.temperature_c !== undefined && data.temperature_c !== null) temp.value = data.temperature_c
    if (data.uptime !== undefined) uptime.value = data.uptime
  }

  let wsUnsubscribe = null
  function initRealtime() {
    if (!wsUnsubscribe) {
      wsUnsubscribe = wsManager.subscribe('/system', (data) => {
        updateFromPayload(data)
      })
    }
  }

  return { cpu, ram, ramMax, temp, uptime, fetchStatus, initRealtime }
})
