<script setup>
import { onMounted } from 'vue'
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

onMounted(() => {
  hardwareStore.fetchScan()
  hardwareStore.fetchGpioStatus()
  hardwareStore.fetchProbes()
  systemStore.fetchStatus()
  flasherStore.fetchFirmwares()

  hardwareStore.initRealtime()
  systemStore.initRealtime()
  flasherStore.initRealtime()
})
</script>

<template>
  <div class="cockpit-layout">
    <!-- Toast Notifications -->
    <ToastNotifications />

    <!-- Header: Boot Control (Sticky) -->
    <header class="header glass-panel">
      <BootControlPanel />
    </header>

    <!-- Main Workspace: Vertical split (workspace | footer) -->
    <Splitpanes class="default-theme workspace-splitpanes" horizontal>
      <!-- Top: 3 columns -->
      <Pane :size="80" :min-size="50">
        <Splitpanes class="default-theme">
          <!-- Left Sidebar -->
          <Pane :size="20" :min-size="12" :max-size="35">
            <Splitpanes class="default-theme" horizontal>
              <Pane :size="65" :min-size="30">
                <div class="glass-panel pane full-pane">
                  <LiveDeviceTree />
                </div>
              </Pane>
              <Pane :size="35" :min-size="20">
                <div class="glass-panel pane full-pane">
                  <PowerRailControl />
                </div>
              </Pane>
            </Splitpanes>
          </Pane>

          <!-- Center: Pipeline Studio -->
          <Pane :size="45" :min-size="25">
            <div class="glass-panel pane full-pane">
              <PipelineStudio />
            </div>
          </Pane>

          <!-- Right Sidebar -->
          <Pane :size="35" :min-size="18" :max-size="50">
            <Splitpanes class="default-theme" horizontal>
              <Pane :size="60" :min-size="30">
                <div class="glass-panel pane full-pane">
                  <TerminalPanel />
                </div>
              </Pane>
              <Pane :size="40" :min-size="20">
                <div class="glass-panel pane full-pane">
                  <FirmwareVault />
                </div>
              </Pane>
            </Splitpanes>
          </Pane>
        </Splitpanes>
      </Pane>

      <!-- Bottom: Footer -->
      <Pane :size="20" :min-size="10" :max-size="40">
        <div class="glass-panel pane footer-pane">
          <Splitpanes class="default-theme">
            <Pane :size="30" :min-size="15">
              <SystemDashboard />
            </Pane>
            <Pane :size="70" :min-size="30">
              <OperationHistory />
            </Pane>
          </Splitpanes>
        </div>
      </Pane>
    </Splitpanes>
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

.workspace-splitpanes {
  flex: 1;
  min-height: 0;
}

.full-pane {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.pane {
  padding: 12px;
  overflow: auto;
}

.footer-pane {
  height: 100%;
  display: flex;
  padding: 10px 16px;
}
</style>

<!-- Override splitpanes default theme to match cyber-industrial design -->
<style>
/* Splitter bar */
.splitpanes.default-theme .splitpanes__splitter {
  background-color: transparent !important;
  border: none !important;
  position: relative;
}

/* Vertical splitter (horizontal divider bar) */
.splitpanes.default-theme.splitpanes--horizontal > .splitpanes__splitter {
  height: 8px !important;
  min-height: 8px !important;
}

/* Horizontal splitter (vertical divider bar) */
.splitpanes.default-theme.splitpanes--vertical > .splitpanes__splitter {
  width: 8px !important;
  min-width: 8px !important;
}

/* Splitter hover indicator */
.splitpanes.default-theme .splitpanes__splitter::before {
  content: '' !important;
  position: absolute !important;
  background: rgba(94, 234, 212, 0.15) !important;
  border-radius: 2px !important;
  transition: background 0.2s ease !important;
  z-index: 1 !important;
}

.splitpanes.default-theme.splitpanes--horizontal > .splitpanes__splitter::before {
  top: 3px !important;
  bottom: 3px !important;
  left: 20% !important;
  right: 20% !important;
  height: 2px !important;
}

.splitpanes.default-theme.splitpanes--vertical > .splitpanes__splitter::before {
  left: 3px !important;
  right: 3px !important;
  top: 20% !important;
  bottom: 20% !important;
  width: 2px !important;
}

.splitpanes.default-theme .splitpanes__splitter:hover::before {
  background: rgba(94, 234, 212, 0.5) !important;
  box-shadow: 0 0 8px rgba(94, 234, 212, 0.3) !important;
}

.splitpanes.default-theme .splitpanes__splitter::after {
  display: none !important;
}

/* Remove default splitpanes border */
.splitpanes.default-theme .splitpanes__pane {
  background: transparent !important;
}
</style>
