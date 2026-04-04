<script setup>
import { useHardwareStore } from '../stores/hardware'

const hardwareStore = useHardwareStore()

const triggerRP2040Bootsel = () => hardwareStore.triggerSequence('rp2040_bootsel')
const triggerRP2040Reset = () => hardwareStore.triggerSequence('rp2040_reset')
const triggerESP32Download = () => hardwareStore.triggerSequence('esp32_download')
const triggerESP32Reset = () => hardwareStore.triggerSequence('esp32_reset')
const triggerPowerCycle = () => hardwareStore.triggerSequence('power_cycle')

</script>

<template>
  <div class="boot-control">
    <div class="brand">
      <span class="glow-text">FlashNode-AI</span>
      <span class="status-indicator"></span>
    </div>
    
    <div class="actions">
      <div class="chip-group">
        <span class="chip-label">RP2040</span>
        <button class="glow-btn" @click="triggerRP2040Bootsel">BOOTSEL</button>
        <button class="glow-btn" @click="triggerRP2040Reset">RESET</button>
      </div>

      <div class="chip-group">
        <span class="chip-label">ESP32</span>
        <button class="glow-btn" @click="triggerESP32Download">DOWNLOAD</button>
        <button class="glow-btn" @click="triggerESP32Reset">RESET EN</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.boot-control {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
}

.glow-text {
  color: var(--text-highlight);
  text-shadow: 0 0 10px rgba(94, 234, 212, 0.5);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--success);
  box-shadow: 0 0 8px var(--success);
  animation: pulseGlow 2s infinite;
}

.actions {
  display: flex;
  gap: 30px;
}

.chip-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chip-label {
  font-family: var(--font-mono);
  color: var(--text-muted);
  font-size: 13px;
  margin-right: 5px;
}
</style>
