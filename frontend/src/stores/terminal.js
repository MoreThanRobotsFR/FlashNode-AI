import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTerminalStore = defineStore('terminal', () => {
  // Store reference to xterm.js terminal instances to persist them across component mounts/unmounts
  const terminals = ref({
    system: null,
    serial_esp32: null,
    serial_rp2040: null,
    flash_output: null,
    gdb: null
  })

  function registerTerminal(name, termInstance) {
    terminals.value[name] = termInstance
  }

  function getTerminal(name) {
    return terminals.value[name]
  }

  return { terminals, registerTerminal, getTerminal }
})
