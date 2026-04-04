import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useFlasherStore = defineStore('flasher', () => {
  const activePipeline = ref(null)
  const progress = ref(0)
  const step = ref('')

  function setProgress(p, s) {
    progress.value = p
    step.value = s
  }

  return { activePipeline, progress, step, setProgress }
})
