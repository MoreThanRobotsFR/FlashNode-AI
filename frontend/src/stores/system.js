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
    if (data.cpu !== undefined) cpu.value = data.cpu
    if (data.ram_mb !== undefined) ram.value = data.ram_mb
    if (data.ram_max !== undefined) ramMax.value = data.ram_max
    if (data.temp_c !== undefined) temp.value = data.temp_c
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
