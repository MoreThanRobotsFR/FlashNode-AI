import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'
import { wsManager } from '../services/ws'

export const useHardwareStore = defineStore('hardware', () => {
  const rails = ref({ '5V': false, '3V3': false })
  const usbDevices = ref([])
  const serialPorts = ref([])
  const probes = ref([])

  // Actions
  async function fetchScan() {
    try {
      const response = await api.get('/devices/scan')
      usbDevices.value = response.data.usb || []
      serialPorts.value = response.data.serial || []
      probes.value = [] // Probes filtering logic can be added later
      
      // Update hardware rails from GPIO state if available in scan 
      // or we can fetch a specific /gpio/status endpoint
    } catch (error) {
      console.error('Failed to fetch devices scan:', error)
    }
  }

  async function fetchGpioStatus() {
    try {
      const response = await api.get('/gpio/status')
      const statuses = response.data.pins || {}
      // Map hardware names from backend to our frontend model
      // We expect backend to give 'Rail 5V', etc. or pin logic.
      // E.g. find the 5V rail status
      const rail5v = Object.values(statuses).find(p => p.label === 'Rail 5V')
      if (rail5v) rails.value['5V'] = (rail5v.value === 1)
      
      const rail3v3 = Object.values(statuses).find(p => p.label === 'Rail 3.3V')
      if (rail3v3) rails.value['3V3'] = (rail3v3.value === 1)
    } catch (error) {
      console.error('Failed to fetch GPIO status', error)
    }
  }

  async function toggleRail(railName, forceState = null) {
    const currentState = rails.value[railName]
    const newState = forceState !== null ? forceState : !currentState
    const action = newState ? 'on' : 'off'
    const endpointParam = railName === '5V' ? '5v' : '3v3'
    
    try {
      await api.post(`/gpio/rail/${endpointParam}/${action}`)
      rails.value[railName] = newState // Optmistic UI update, WS will confirm
    } catch (error) {
      console.error(`Failed to toggle rail ${railName}`, error)
    }
  }

  async function triggerSequence(sequenceName) {
    try {
      await api.post(`/gpio/sequence/${sequenceName}`)
    } catch (error) {
      console.error(`Failed to trigger sequence ${sequenceName}`, error)
    }
  }

  // Subscribe to WebSocket updates
  let wsUnsubscribeGpio = null
  let wsUnsubscribeDevices = null

  function initRealtime() {
    if (!wsUnsubscribeGpio) {
      wsUnsubscribeGpio = wsManager.subscribe('/gpio', (data) => {
        // e.g. {"pin":"GPIO1_B3","value":1,"label":"Rail 5V"}
        if (data.label === 'Rail 5V') rails.value['5V'] = (data.value === 1)
        if (data.label === 'Rail 3.3V') rails.value['3V3'] = (data.value === 1)
      })
    }
    if (!wsUnsubscribeDevices) {
      wsUnsubscribeDevices = wsManager.subscribe('/devices', (data) => {
        // e.g. {"event":"add","device":"/dev/ttyUSB0"}
        // Simple strategy: anytime there's a device event, re-fetch the scan
        fetchScan()
      })
    }
  }

  return { rails, usbDevices, serialPorts, probes, toggleRail, triggerSequence, fetchScan, fetchGpioStatus, initRealtime }
})
