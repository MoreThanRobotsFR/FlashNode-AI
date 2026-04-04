<script setup>
import BootControlPanel from './components/BootControlPanel.vue'
import LiveDeviceTree from './components/LiveDeviceTree.vue'
import PowerRailControl from './components/PowerRailControl.vue'
import PipelineStudio from './components/PipelineStudio.vue'
import TerminalPanel from './components/TerminalPanel.vue'
import FirmwareVault from './components/FirmwareVault.vue'
import OperationHistory from './components/OperationHistory.vue'
import SystemDashboard from './components/SystemDashboard.vue'
</script>

<template>
  <div class="cockpit-layout">
    <!-- Header: Boot Control (Sticky) -->
    <header class="header glass-panel">
      <BootControlPanel />
    </header>

    <!-- Main Workspace -->
    <div class="workspace">
      
      <!-- Left Sidebar: Context & Hardware -->
      <aside class="sidebar-left">
        <LiveDeviceTree class="glass-panel pane" style="flex: 2" />
        <PowerRailControl class="glass-panel pane" style="flex: 1" />
      </aside>

      <!-- Center: Execution Engine -->
      <main class="center-content glass-panel pane">
        <PipelineStudio />
      </main>

      <!-- Right Sidebar: Output & State -->
      <aside class="sidebar-right">
        <TerminalPanel class="glass-panel pane" style="flex: 2" />
        <FirmwareVault class="glass-panel pane" style="flex: 1" />
      </aside>
      
    </div>

    <!-- Footer: System / History -->
    <footer class="footer glass-panel">
      <SystemDashboard style="flex: 1" />
      <OperationHistory style="flex: 2" />
    </footer>
  </div>
</template>

<style scoped>
.cockpit-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 10px;
  gap: 10px;
  box-sizing: border-box;
}

.header {
  height: 60px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.workspace {
  display: flex;
  flex: 1;
  gap: 10px;
  min-height: 0; /* Important for flex child scroll */
}

.sidebar-left, .sidebar-right {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.sidebar-right {
  width: 400px; /* Needs more space for xterm */
}

.center-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.footer {
  height: 120px;
  flex-shrink: 0;
  display: flex;
  gap: 20px;
  padding: 10px 20px;
}

.pane {
  padding: 15px;
  overflow: auto;
}
</style>
