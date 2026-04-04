import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'
import { wsManager } from '../services/ws'

export const useFlasherStore = defineStore('flasher', () => {
  const activePipeline = ref(null)
  const progress = ref(0)
  const step = ref('')
  
  const vaultFirmwares = ref({
    'RP2040': [],
    'ESP32': []
  })

  let wsUnsubscribeFlash = null
  let wsUnsubscribePipeline = null

  async function fetchFirmwares() {
    try {
      const res = await api.get('/firmware/list')
      // Assuming backend groups by target or returns a flat list
      vaultFirmwares.value = res.data || { 'RP2040': [], 'ESP32': [] }
    } catch(err) {
      console.error('Failed to fetch firmwares', err)
    }
  }

  async function uploadFirmware(file, target) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('target', target)
    
    try {
      await api.post('/firmware/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      await fetchFirmwares()
    } catch(err) {
      console.error('Upload failed', err)
      throw err
    }
  }

  async function deleteFirmware(name) {
    try {
      await api.delete(`/firmware/${name}`)
      await fetchFirmwares()
    } catch(err) {
      console.error('Failed to delete firmware', err)
    }
  }

  async function runPipeline(name) {
    try {
      await api.post(`/pipeline/${name}/start`)
    } catch(err) {
      console.error('Pipeline start failed', err)
    }
  }

  function initRealtime() {
    if (!wsUnsubscribeFlash) {
      wsUnsubscribeFlash = wsManager.subscribe('/flash/progress', (data) => {
        if (data.progress !== undefined) progress.value = data.progress
        if (data.step !== undefined) step.value = data.step
      })
    }
    if (!wsUnsubscribePipeline) {
      wsUnsubscribePipeline = wsManager.subscribe('/pipeline/status', (data) => {
        // Handle pipeline multi-step progress...
      })
    }
  }

  return { 
    activePipeline, progress, step, vaultFirmwares, 
    fetchFirmwares, uploadFirmware, deleteFirmware, runPipeline, initRealtime 
  }
})
