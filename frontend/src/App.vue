<script setup>
import { onMounted, ref } from 'vue'
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import { useHardwareStore } from './stores/hardware'
import { useSystemStore } from './stores/system'
import { useFlasherStore } from './stores/flasher'

import BootControlPanel from './components/BootControlPanel.vue'
import LiveDeviceTree from './components/LiveDeviceTree.vue'
import PowerRailControl from './components/PowerRailControl.vue'
import PipelineStudio from './components/PipelineStudio.vue'
import TerminalPanel from './components/TerminalPanel.vue'
import FirmwareVault from './components/FirmwareVault.vue'
import OperationHistory from './components/OperationHistory.vue'
import SystemDashboard from './components/SystemDashboard.vue'
import ToastNotifications from './components/ToastNotifications.vue'

const hardwareStore = useHardwareStore()
const systemStore = useSystemStore()
const flasherStore = useFlasherStore()

const mounted = ref(false)

onMounted(() => {
  hardwareStore.fetchScan()
  hardwareStore.fetchGpioStatus()
  hardwareStore.fetchProbes()
  systemStore.fetchStatus()
  flasherStore.fetchFirmwares()

  hardwareStore.initRealtime()
  systemStore.initRealtime()
  flasherStore.initRealtime()

  // Delay splitpanes render to avoid null ref race condition
  setTimeout(() => { mounted.value = true }, 50)
})
</script>

<template>
  <div class="cockpit-layout">
    <ToastNotifications />

    <!-- Header -->
    <header class="header glass-panel">
      <BootControlPanel />
    </header>

    <!-- Splitpanes workspace — only render after mount to avoid null ref -->
    <template v-if="mounted">
      <!-- Vertical: workspace (top) | footer (bottom) -->
      <Splitpanes class="default-theme flex-grow" horizontal>
        <Pane :size="80" :min-size="50">
          <!-- Horizontal: left | center | right -->
          <Splitpanes class="default-theme full-h">
            <!-- Left sidebar -->
            <Pane :size="20" :min-size="12" :max-size="35">
              <div class="sidebar-col">
                <div class="glass-panel pane" style="flex: 2">
                  <LiveDeviceTree />
                </div>
                <div class="glass-panel pane" style="flex: 1">
                  <PowerRailControl />
                </div>
              </div>
            </Pane>

            <!-- Center -->
            <Pane :size="45" :min-size="25">
              <div class="glass-panel pane full-pane">
                <PipelineStudio />
              </div>
            </Pane>

            <!-- Right sidebar -->
            <Pane :size="35" :min-size="18" :max-size="50">
              <div class="sidebar-col">
                <div class="glass-panel pane" style="flex: 2">
                  <TerminalPanel />
                </div>
                <div class="glass-panel pane" style="flex: 1">
                  <FirmwareVault />
                </div>
              </div>
            </Pane>
          </Splitpanes>
        </Pane>

        <!-- Footer -->
        <Pane :size="20" :min-size="10" :max-size="40">
          <div class="glass-panel pane footer-pane">
            <SystemDashboard style="flex: 0 0 280px" />
            <div class="footer-divider"></div>
            <OperationHistory style="flex: 1" />
          </div>
        </Pane>
      </Splitpanes>
    </template>

    <!-- Fallback while splitpanes initializes -->
    <div v-else class="flex-grow" style="display: flex; align-items: center; justify-content: center;">
      <span style="color: var(--text-muted)">Initialisation...</span>
    </div>
  </div>
</template>

<style scoped>
.cockpit-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 8px;
  gap: 8px;
  box-sizing: border-box;
}

.header {
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.flex-grow {
  flex: 1;
  min-height: 0;
}

.full-h {
  height: 100%;
}

.full-pane {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-col {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pane {
  padding: 12px;
  overflow: auto;
}

.footer-pane {
  height: 100%;
  display: flex;
  gap: 16px;
  padding: 10px 16px;
  align-items: stretch;
}

.footer-divider {
  width: 1px;
  background: var(--border-light);
  flex-shrink: 0;
}
</style>

<!-- Override splitpanes theme to match cyber-industrial design -->
<style>
.splitpanes.default-theme .splitpanes__splitter {
  background-color: transparent !important;
  border: none !important;
  position: relative;
}

.splitpanes.default-theme.splitpanes--horizontal > .splitpanes__splitter {
  height: 8px !important;
  min-height: 8px !important;
}

.splitpanes.default-theme.splitpanes--vertical > .splitpanes__splitter {
  width: 8px !important;
  min-width: 8px !important;
}

.splitpanes.default-theme .splitpanes__splitter::before {
  content: '' !important;
  position: absolute !important;
  background: rgba(94, 234, 212, 0.12) !important;
  border-radius: 2px !important;
  transition: background 0.2s ease !important;
  z-index: 1 !important;
}

.splitpanes.default-theme.splitpanes--horizontal > .splitpanes__splitter::before {
  top: 3px !important;
  bottom: 3px !important;
  left: 25% !important;
  right: 25% !important;
  height: 2px !important;
}

.splitpanes.default-theme.splitpanes--vertical > .splitpanes__splitter::before {
  left: 3px !important;
  right: 3px !important;
  top: 25% !important;
  bottom: 25% !important;
  width: 2px !important;
}

.splitpanes.default-theme .splitpanes__splitter:hover::before {
  background: rgba(94, 234, 212, 0.5) !important;
  box-shadow: 0 0 8px rgba(94, 234, 212, 0.3) !important;
}

.splitpanes.default-theme .splitpanes__splitter::after {
  display: none !important;
}

.splitpanes.default-theme .splitpanes__pane {
  background: transparent !important;
}
</style>
