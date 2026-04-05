<script setup>
import { useHardwareStore } from '../stores/hardware'

const hardwareStore = useHardwareStore()
</script>

<template>
  <div class="panel-container">
    <h3 class="panel-title">📡 Live Device Tree</h3>
    
    <div class="tree">
      <!-- USB Devices -->
      <div class="section-label" v-if="hardwareStore.usbDevices.length > 0">🔌 Périphériques USB</div>
      <div v-for="(dev, i) in hardwareStore.usbDevices" :key="'usb-'+i" class="tree-item">
        <span class="icon">🔌</span>
        <div class="details">
          <div class="name">{{ dev.description || 'Appareil USB' }}</div>
          <div class="path">{{ dev.device_node || 'USB' }} <span class="tag">Actif</span></div>
        </div>
      </div>

      <!-- Serial Ports -->
      <div class="section-label" v-if="hardwareStore.serialPorts.length > 0">📟 Ports Série</div>
      <div v-for="(port, i) in hardwareStore.serialPorts" :key="'serial-'+i" class="tree-item">
        <span class="icon">📟</span>
        <div class="details">
          <div class="name">{{ port.type !== 'Unknown' ? port.type : (port.description || 'Port Série') }}</div>
          <div class="path">{{ port.port }} <span class="tag">OPEN</span></div>
        </div>
      </div>

      <!-- Debug Probes -->
      <div class="section-label" v-if="hardwareStore.probes.length > 0">🔬 Sondes de Débogage</div>
      <div v-for="(probe, i) in hardwareStore.probes" :key="'probe-'+i" class="tree-item probe">
        <span class="icon">🔬</span>
        <div class="details">
          <div class="name">{{ probe.type }}</div>
          <div class="path">{{ probe.port }} <span class="tag probe-tag">{{ probe.interface }}</span></div>
        </div>
      </div>

      <!-- GPIO & Power Rails -->
      <div class="section-label">⚡ GPIO & Alimentation</div>
      <div class="tree-item gpio-item">
        <span class="icon">⚡</span>
        <div class="details">
          <div class="gpio-row">
            <span class="gpio-name">Rail 5V</span>
            <span :class="['gpio-indicator', { on: hardwareStore.rails['5V'] }]"></span>
          </div>
          <div class="gpio-row">
            <span class="gpio-name">Rail 3.3V</span>
            <span :class="['gpio-indicator', { on: hardwareStore.rails['3V3'] }]"></span>
          </div>
        </div>
      </div>
      
      <!-- Fallback when nothing connected -->
      <div v-if="!hardwareStore.usbDevices.length && !hardwareStore.serialPorts.length" class="tree-item disabled">
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
  margin-bottom: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 8px;
}

.tree {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
}

.section-label {
  font-family: var(--font-mono);
  font-size: 10px;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 1px;
  margin-top: 8px;
  margin-bottom: 2px;
  opacity: 0.7;
}

.tree-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
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

.tree-item.probe {
  border-left: 2px solid var(--info);
}

.icon {
  font-size: 16px;
  flex-shrink: 0;
}

.details {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.name {
  font-weight: 500;
  color: var(--text-main);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.path {
  font-family: var(--font-mono);
  color: var(--text-muted);
  font-size: 10px;
  margin-top: 1px;
}

.tag {
  background: rgba(94, 234, 212, 0.1);
  color: var(--text-highlight);
  padding: 1px 4px;
  border-radius: 3px;
  margin-left: 4px;
  font-size: 9px;
}

.probe-tag {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

/* GPIO mini status */
.gpio-item {
  padding: 8px;
}

.gpio-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 3px;
}

.gpio-name {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.gpio-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #333;
  transition: all 0.3s;
}

.gpio-indicator.on {
  background: var(--success);
  box-shadow: 0 0 6px var(--success);
}
</style>
