import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'
import { wsManager } from '../services/ws'

export const useFlasherStore = defineStore('flasher', () => {
  const activePipeline = ref(null)
  const availablePipelines = ref([])
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

  async function fetchPipelines() {
    try {
      const res = await api.get('/pipeline/list')
      availablePipelines.value = res.data || []
    } catch(err) {
      console.error('Failed to fetch pipelines', err)
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

  async function deleteFirmware(target, filename) {
    try {
      await api.delete(`/firmware/${target}/${filename}`)
      await fetchFirmwares()
    } catch(err) {
      console.error('Failed to delete firmware', err)
    }
  }

  async function flashFirmware(target, filename, tool = 'picotool') {
    try {
      await api.post('/action/flash', {
        tool: tool,
        target: target,
        firmware: filename,
        baudrate: 921600
      })
    } catch(err) {
        console.error('Flash failed', err)
    }
  }

  async function runPipeline(name) {
    try {
      await api.post('/pipeline/start', { pipeline_name: name })
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
        console.log("[WS] Pipeline status received:", data)
        if (data.step_idx !== undefined && data.total_steps) {
          progress.value = Math.floor(((data.step_idx - 1) / data.total_steps) * 100)
          
          if (data.status === 'completed') {
             progress.value = 100
          }
          
          activePipeline.value = {
            id: data.pipeline_id,
            currentStep: data.step_idx,
            totalSteps: data.total_steps,
            status: data.status,
            details: data.step_details
          }
          console.log("[WS] activePipeline updated:", activePipeline.value)
        }
      })
    }
  }

  return { 
    activePipeline, availablePipelines, progress, step, vaultFirmwares, 
    fetchFirmwares, fetchPipelines, uploadFirmware, deleteFirmware, flashFirmware, runPipeline, initRealtime 
  }
})
