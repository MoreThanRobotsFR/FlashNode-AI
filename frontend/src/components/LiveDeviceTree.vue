<script setup>
import { useHardwareStore } from '../stores/hardware'

const hardwareStore = useHardwareStore()
</script>

<template>
  <div class="panel-container">
    <h3 class="panel-title">📡 Live Device Tree</h3>
    
    <div class="tree">
      <!-- Probes -->
      <div v-for="(probe, i) in hardwareStore.probes" :key="'probe-'+i" class="tree-item">
        <span class="icon">🔌</span>
        <div class="details">
          <div class="name">Debug Probe</div>
          <div class="path">{{ probe }} <span class="tag">SWD Ready</span></div>
        </div>
      </div>

      <!-- Serial Ports -->
      <div v-for="(port, i) in hardwareStore.serialPorts" :key="'serial-'+i" class="tree-item">
        <span class="icon">📟</span>
        <div class="details">
          <div class="name">Serial Device</div>
          <div class="path">{{ port }} <span class="tag">OPEN</span></div>
        </div>
      </div>
      
      <!-- Fallback when nothing connected -->
      <div v-if="!hardwareStore.probes.length && !hardwareStore.serialPorts.length" class="tree-item disabled">
        <span class="icon">⚪</span>
        <div class="details">
          <div class="name">No devices</div>
          <div class="path">Wait for connection</div>
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

.panel-title {
  font-size: 14px;
  text-transform: uppercase;
  color: var(--text-highlight);
  margin-bottom: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 8px;
}

.tree {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tree-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 6px;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.tree-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--border-light);
}

.tree-item.disabled {
  opacity: 0.5;
}

.icon {
  font-size: 18px;
}

.details {
  display: flex;
  flex-direction: column;
}

.name {
  font-weight: 500;
  color: var(--text-main);
  font-size: 13px;
}

.path {
  font-family: var(--font-mono);
  color: var(--text-muted);
  font-size: 11px;
  margin-top: 2px;
}

.tag {
  background: rgba(94, 234, 212, 0.1);
  color: var(--text-highlight);
  padding: 2px 4px;
  border-radius: 3px;
  margin-left: 4px;
}
</style>
