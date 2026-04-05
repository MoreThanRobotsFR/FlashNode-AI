import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'
import { wsManager } from '../services/ws'
import { useNotificationStore } from './notifications'

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
      vaultFirmwares.value = res.data || { 'RP2040': [], 'ESP32': [] }
    } catch (err) {
      console.error('Failed to fetch firmwares', err)
    }
  }

  async function fetchPipelines() {
    try {
      const res = await api.get('/pipeline/list')
      availablePipelines.value = res.data || []
    } catch (err) {
      console.error('Failed to fetch pipelines', err)
    }
  }

  async function uploadFirmware(file, target) {
    const notifStore = useNotificationStore()
    const formData = new FormData()
    formData.append('file', file)
    formData.append('target', target)

    try {
      await api.post('/firmware/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      await fetchFirmwares()
      notifStore.success(`Firmware ${file.name} uploadé vers ${target}`)
    } catch (err) {
      console.error('Upload failed', err)
      notifStore.error(`Échec upload ${file.name}`)
      throw err
    }
  }

  async function deleteFirmware(target, filename) {
    const notifStore = useNotificationStore()
    try {
      await api.delete(`/firmware/${target}/${filename}`)
      await fetchFirmwares()
      notifStore.success(`${filename} supprimé`)
    } catch (err) {
      console.error('Failed to delete firmware', err)
      notifStore.error(`Échec suppression ${filename}`)
    }
  }

  async function flashFirmware(target, filename, tool = 'picotool') {
    const notifStore = useNotificationStore()
    try {
      notifStore.info(`Flash ${target} en cours...`)
      const res = await api.post('/action/flash', {
        tool: tool,
        target: target,
        firmware: filename,
        baudrate: 921600
      })
      if (res.data?.status === 'success') {
        notifStore.success(`Flash ${target} terminé (${res.data.duration_s}s)`)
      } else {
        notifStore.error(`Flash ${target} échoué`)
      }
    } catch (err) {
      console.error('Flash failed', err)
      notifStore.error(`Flash ${target} échoué`)
    }
  }

  async function runPipeline(name) {
    const notifStore = useNotificationStore()
    try {
      await api.post('/pipeline/start', { pipeline_name: name })
      notifStore.info(`Pipeline ${name} démarré`)
    } catch (err) {
      console.error('Pipeline start failed', err)
      notifStore.error(`Échec démarrage pipeline ${name}`)
    }
  }

  async function stopPipeline() {
    const notifStore = useNotificationStore()
    try {
      await api.post('/pipeline/stop')
      notifStore.warning('Pipeline arrêté')
    } catch (err) {
      console.error('Pipeline stop failed', err)
      notifStore.error('Échec arrêt pipeline')
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
        if (data.step_idx !== undefined && data.total_steps) {
          progress.value = Math.floor(((data.step_idx - 1) / data.total_steps) * 100)

          if (data.status === 'completed') {
            progress.value = 100
            const notifStore = useNotificationStore()
            notifStore.success(`Pipeline ${data.pipeline_id} terminé avec succès`)
          } else if (data.status === 'failed' || data.status === 'error') {
            const notifStore = useNotificationStore()
            notifStore.error(`Pipeline ${data.pipeline_id} échoué à l'étape ${data.step_idx}`)
          }

          activePipeline.value = {
            id: data.pipeline_id,
            currentStep: data.step_idx,
            totalSteps: data.total_steps,
            status: data.status,
            details: data.step_details
          }
        }
      })
    }
  }

  return {
    activePipeline, availablePipelines, progress, step, vaultFirmwares,
    fetchFirmwares, fetchPipelines, uploadFirmware, deleteFirmware, flashFirmware,
    runPipeline, stopPipeline, initRealtime
  }
})
