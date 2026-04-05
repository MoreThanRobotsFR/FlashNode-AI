import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'
import { wsManager } from '../services/ws'
import { useNotificationStore } from './notifications'

export const useHardwareStore = defineStore('hardware', () => {
  const rails = ref({ '5V': false, '3V3': false })
  const usbDevices = ref([])
  const serialPorts = ref([])
  const probes = ref([])
  const gpioStatus = ref({}) // Full GPIO pin states

  // Actions
  async function fetchScan() {
    try {
      const response = await api.get('/devices/scan')
      usbDevices.value = response.data.usb || []
      serialPorts.value = response.data.serial || []
    } catch (error) {
      console.error('Failed to fetch devices scan:', error)
    }
  }

  async function fetchProbes() {
    try {
      const response = await api.get('/devices/probes')
      probes.value = response.data || []
    } catch (error) {
      console.error('Failed to fetch probes:', error)
    }
  }

  async function fetchGpioStatus() {
    try {
      const response = await api.get('/gpio/status')
      const data = response.data || {}
      // Backend returns {"5V": true/false, "3V3": true/false}
      if (data['5V'] !== undefined) rails.value['5V'] = data['5V']
      if (data['3V3'] !== undefined) rails.value['3V3'] = data['3V3']
    } catch (error) {
      console.error('Failed to fetch GPIO status', error)
    }
  }

  async function toggleRail(railName, forceState = null) {
    const notifStore = useNotificationStore()
    const currentState = rails.value[railName]
    const newState = forceState !== null ? forceState : !currentState
    const action = newState ? 'on' : 'off'
    const endpointParam = railName === '5V' ? '5v' : '3v3'

    try {
      await api.post(`/gpio/rail/${endpointParam}/${action}`)
      rails.value[railName] = newState
      notifStore.success(`Rail ${railName} → ${action.toUpperCase()}`)
    } catch (error) {
      console.error(`Failed to toggle rail ${railName}`, error)
      notifStore.error(`Échec commande rail ${railName}`)
    }
  }

  async function triggerSequence(sequenceName) {
    const notifStore = useNotificationStore()
    try {
      await api.post(`/gpio/sequence/${sequenceName}`)
      notifStore.success(`Séquence ${sequenceName} exécutée`)
    } catch (error) {
      console.error(`Failed to trigger sequence ${sequenceName}`, error)
      notifStore.error(`Échec séquence ${sequenceName}`)
    }
  }

  // Subscribe to WebSocket updates
  let wsUnsubscribeGpio = null
  let wsUnsubscribeDevices = null

  function initRealtime() {
    if (!wsUnsubscribeGpio) {
      wsUnsubscribeGpio = wsManager.subscribe('/gpio', (data) => {
        if (data.label === 'Rail 5V') rails.value['5V'] = (data.value === 1)
        if (data.label === 'Rail 3.3V') rails.value['3V3'] = (data.value === 1)
      })
    }
    if (!wsUnsubscribeDevices) {
      wsUnsubscribeDevices = wsManager.subscribe('/devices', (data) => {
        fetchScan()
      })
    }
  }

  return { rails, usbDevices, serialPorts, probes, gpioStatus, toggleRail, triggerSequence, fetchScan, fetchProbes, fetchGpioStatus, initRealtime }
})
