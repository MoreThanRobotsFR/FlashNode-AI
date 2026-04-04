<script setup>
import { useSystemStore } from '../stores/system'
import { computed } from 'vue'

const systemStore = useSystemStore()
const ramUsagePercent = computed(() => {
  return systemStore.ramMax > 0 ? (systemStore.ram / systemStore.ramMax) * 100 : 0
})
</script>

<template>
  <div class="panel-container">
    <h3 class="panel-title">🖥️ Base Station</h3>
    
    <div class="metrics">
      <div class="metric">
        <span class="label">CPU</span>
        <div class="bar-bg"><div class="bar-fill" :style="{ width: systemStore.cpu + '%' }"></div></div>
        <span class="val">{{ systemStore.cpu }}%</span>
      </div>

      <div class="metric">
        <span class="label">RAM</span>
        <div class="bar-bg"><div class="bar-fill info" :style="{ width: ramUsagePercent + '%' }"></div></div>
        <span class="val">{{ (systemStore.ram / 1000).toFixed(1) }}/{{ (systemStore.ramMax / 1000).toFixed(1) }} GB</span>
      </div>

      <div class="metric">
        <span class="label">TEMP</span>
        <span class="val val-text">{{ systemStore.temp }}°C</span>
      </div>
      
       <div class="metric">
        <span class="label">UPTIME</span>
        <span class="val val-text">{{ systemStore.uptime || '...' }}</span>
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
  font-size: 13px;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 10px;
}

.metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 20px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 10px;
}

.label {
  font-size: 11px;
  color: var(--text-muted);
  width: 30px;
}

.bar-bg {
  flex: 1;
  height: 4px;
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--success);
}

.bar-fill.info {
  background: var(--info);
}

.val {
  font-family: var(--font-mono);
  font-size: 11px;
  width: 60px;
  text-align: right;
}

.val-text {
  flex: 1;
  text-align: left;
  color: var(--text-highlight);
}
</style>
