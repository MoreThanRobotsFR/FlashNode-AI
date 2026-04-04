<script setup>
import { useHardwareStore } from '../stores/hardware'
const hardwareStore = useHardwareStore()
</script>

<template>
  <div class="panel-container">
    <h3 class="panel-title">⚡ Power Rails</h3>
    
    <div class="rails">
      <div class="rail">
        <div class="rail-info">
          <span :class="['indicator', { active: hardwareStore.rails['5V'] }]"></span>
          <span class="name">Rail 5V</span>
        </div>
        <button class="glow-btn" @click="hardwareStore.toggleRail('5V')">
          {{ hardwareStore.rails['5V'] ? 'OFF' : 'ON' }}
        </button>
      </div>

      <div class="rail">
        <div class="rail-info">
          <span :class="['indicator', { active: hardwareStore.rails['3V3'] }]"></span>
          <span class="name">Rail 3.3V</span>
        </div>
        <button class="glow-btn" @click="hardwareStore.toggleRail('3V3')">
          {{ hardwareStore.rails['3V3'] ? 'OFF' : 'ON' }}
        </button>
      </div>
      
      <div class="actions">
         <button class="glow-btn warning-btn" style="width: 100%; margin-top: 10px;" @click="hardwareStore.triggerSequence('power_cycle')">⚠ POWER CYCLE</button>
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
  color: var(--warning);
  margin-bottom: 15px;
  font-weight: 600;
  border-bottom: 1px solid rgba(245, 158, 11, 0.2);
  padding-bottom: 8px;
}

.rails {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.rail {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rail-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #333;
}

.indicator.active {
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}

.name {
  font-family: var(--font-mono);
  font-size: 13px;
}

.warning-btn {
  color: var(--warning);
  border-color: rgba(245, 158, 11, 0.5);
  background: rgba(245, 158, 11, 0.1);
}

.warning-btn:hover {
  background: rgba(245, 158, 11, 0.2);
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
}
</style>
