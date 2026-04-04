import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useHardwareStore = defineStore('hardware', () => {
  const rails = ref({ '5V': false, '3V3': false })
  const usbDevices = ref([])
  const serialPorts = ref([])

  function setRail(rail, status) {
    rails.value[rail] = status
  }

  return { rails, usbDevices, serialPorts, setRail }
})
