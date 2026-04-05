<script setup>
import { useFlasherStore } from '../stores/flasher'
import { computed, ref, onMounted } from 'vue'

const flasherStore = useFlasherStore()
const selectedPipeline = ref('')

onMounted(() => {
  flasherStore.fetchPipelines().then(() => {
    if (flasherStore.availablePipelines.length > 0) {
      selectedPipeline.value = flasherStore.availablePipelines[0].id
    }
  })
})

const startPipeline = () => {
  if (selectedPipeline.value) {
    flasherStore.runPipeline(selectedPipeline.value)
  }
}

const stopPipeline = () => {
  flasherStore.stopPipeline()
}

const isRunning = computed(() => {
  return flasherStore.activePipeline?.status === 'running'
})

const globalProgress = computed(() => {
  if (!flasherStore.activePipeline) return 0
  const { currentStep, totalSteps, status } = flasherStore.activePipeline
  if (status === 'completed') return 100
  if (!totalSteps) return 0
  return Math.floor(((currentStep - 1) / totalSteps) * 100)
})

const globalLabel = computed(() => {
  if (!flasherStore.activePipeline) return ''
  const { currentStep, totalSteps, status } = flasherStore.activePipeline
  if (status === 'completed') return '✅ Terminé'
  if (status === 'failed' || status === 'error') return '❌ Échoué'
  if (status === 'cancelled' || status === 'stopped') return '⏹ Arrêté'
  return `Étape ${currentStep}/${totalSteps}`
})

// Derive steps to display
const displayedSteps = computed(() => {
  const currentDef = flasherStore.availablePipelines.find(p => p.id === selectedPipeline.value)
  if (!currentDef) return []

  return currentDef.steps.map((step, index) => {
    const stepNum = index + 1
    let statusClass = 'pending'
    let statusText = 'Pending'
    let isSpinner = false

    if (flasherStore.activePipeline && flasherStore.activePipeline.id === currentDef.id) {
      if (flasherStore.activePipeline.status === 'completed') {
        statusClass = 'success'
        statusText = '✅ OK'
      } else if (flasherStore.activePipeline.status === 'failed' || flasherStore.activePipeline.status === 'error') {
        if (stepNum < flasherStore.activePipeline.currentStep) {
          statusClass = 'success'
          statusText = '✅ OK'
        } else if (stepNum === flasherStore.activePipeline.currentStep) {
          statusClass = 'failed'
          statusText = '❌ Échoué'
        }
      } else if (flasherStore.activePipeline.status === 'running') {
        if (stepNum < flasherStore.activePipeline.currentStep) {
          statusClass = 'success'
          statusText = '✅ OK'
        } else if (stepNum === flasherStore.activePipeline.currentStep) {
          statusClass = 'active'
          statusText = '⚡ En cours...'
          isSpinner = true
        }
      }
    }

    return {
      num: stepNum,
      name: step.description || step.action,
      statusClass,
      statusText,
      isSpinner,
      details: step
    }
  })
})
</script>

<template>
  <div class="panel-container">
    <div class="header-row">
      <h3 class="panel-title">📋 Pipeline Studio</h3>
      <div class="pipeline-selector">
        <select v-model="selectedPipeline" class="custom-select">
          <option v-for="pipe in flasherStore.availablePipelines" :key="pipe.id" :value="pipe.id">
            {{ pipe.name }}
          </option>
        </select>
        <button v-if="!isRunning" class="glow-btn" @click="startPipeline">▶ LAUNCH</button>
        <button v-else class="glow-btn stop-btn" @click="stopPipeline">⏹ STOP</button>
      </div>
    </div>

    <!-- Global progress bar -->
    <div class="global-progress" v-if="flasherStore.activePipeline">
      <div class="progress-info">
        <span class="progress-label">{{ globalLabel }}</span>
        <span class="progress-pct">{{ globalProgress }}%</span>
      </div>
      <div class="progress-bar-container global">
        <div
          class="progress-bar"
          :class="{ completed: flasherStore.activePipeline?.status === 'completed', failed: flasherStore.activePipeline?.status === 'failed' }"
          :style="{ width: globalProgress + '%' }"
        ></div>
      </div>
    </div>

    <div class="pipeline-steps">
      <div v-for="step in displayedSteps" :key="step.num" :class="['step', step.statusClass]">
        <div class="step-header">
          <span class="step-num">[{{ step.num }}]</span>
          <span class="step-name">{{ step.name }}</span>
          <span :class="['step-status', { spinner: step.isSpinner }]">{{ step.statusText }}</span>
        </div>

        <div class="step-details" v-if="step.details.tool || step.details.port || step.details.target">
          <div v-if="step.details.tool">Outil: <span class="val">{{ step.details.tool }}</span></div>
          <div v-if="step.details.firmware">Firmware: <span class="val">{{ step.details.firmware }}</span></div>
          <div v-if="step.details.port">Port: <span class="val">{{ step.details.port }}</span></div>
        </div>

        <div class="progress-bar-container" v-if="step.statusClass === 'active'">
          <div class="progress-bar indeterminate"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.panel-title {
  font-size: 15px;
  text-transform: uppercase;
  color: var(--text-main);
  font-weight: 700;
  letter-spacing: 1px;
}

.pipeline-selector {
  display: flex;
  gap: 8px;
}

.custom-select {
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--border-light);
  color: var(--text-main);
  padding: 5px 10px;
  border-radius: 4px;
  outline: none;
  font-family: var(--font-mono);
  font-size: 12px;
}

.stop-btn {
  color: var(--error) !important;
  border-color: rgba(239, 68, 68, 0.5) !important;
  background: rgba(239, 68, 68, 0.1) !important;
}

.stop-btn:hover {
  background: rgba(239, 68, 68, 0.2) !important;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.3) !important;
}

/* Global progress */
.global-progress {
  margin-bottom: 15px;
  padding: 10px 12px;
  background: rgba(0,0,0,0.15);
  border-radius: 6px;
  border: 1px solid var(--border-light);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.progress-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main);
}

.progress-pct {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-highlight);
}

.progress-bar-container {
  height: 4px;
  background: rgba(0,0,0,0.5);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar-container.global {
  height: 6px;
}

.progress-bar {
  height: 100%;
  background: var(--info);
  box-shadow: 0 0 10px var(--info);
  transition: width 0.5s ease;
}

.progress-bar.completed {
  background: var(--success);
  box-shadow: 0 0 10px var(--success);
}

.progress-bar.failed {
  background: var(--error);
  box-shadow: 0 0 10px var(--error);
}

.progress-bar.indeterminate {
  width: 30% !important;
  animation: indeterminate 1.5s infinite linear;
}

.pipeline-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding-right: 5px;
}

.step {
  border: 1px solid var(--border-light);
  background: rgba(0,0,0,0.2);
  border-radius: 6px;
  padding: 12px;
  transition: all 0.3s;
}

.step.active {
  border-color: var(--info);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.15);
  background: rgba(59, 130, 246, 0.05);
}

.step.success {
  border-left: 3px solid var(--success);
}

.step.failed {
  border-left: 3px solid var(--error);
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.05);
}

.step.pending {
  opacity: 0.5;
}

.step-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.step-num {
  font-family: var(--font-mono);
  color: var(--text-muted);
  margin-right: 10px;
}

.step-name {
  font-weight: 600;
  flex: 1;
}

.step-status {
  font-size: 12px;
}

.spinner {
  animation: pulseGlow 1s infinite alternate;
}

.step-details {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
}

.val {
  color: var(--text-highlight);
}

@keyframes indeterminate {
  0% { transform: translateX(-100%); width: 30%; }
  100% { transform: translateX(300%); width: 30%; }
}
</style>
