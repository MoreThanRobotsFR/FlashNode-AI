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
        <div class="bar-bg"><div class="bar-fill" :class="{ warn: systemStore.cpu > 80 }" :style="{ width: systemStore.cpu + '%' }"></div></div>
        <span class="val">{{ systemStore.cpu }}%</span>
      </div>

      <div class="metric">
        <span class="label">RAM</span>
        <div class="bar-bg"><div class="bar-fill info" :style="{ width: ramUsagePercent + '%' }"></div></div>
        <span class="val">{{ (systemStore.ram / 1000).toFixed(1) }}/{{ (systemStore.ramMax / 1000).toFixed(1) }} GB</span>
      </div>

      <div class="metric">
        <span class="label">TEMP</span>
        <span class="val val-text" :class="{ hot: systemStore.temp > 70 }">{{ systemStore.temp || '—' }}°C</span>
      </div>
      
      <div class="metric">
        <span class="label">UP</span>
        <span class="val val-text">{{ systemStore.uptimeFormatted }}</span>
      </div>

      <div class="metric" v-if="systemStore.ip">
        <span class="label">IP</span>
        <span class="val val-text ip">{{ systemStore.ip }}</span>
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
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.label {
  font-size: 10px;
  color: var(--text-muted);
  width: 30px;
  flex-shrink: 0;
  font-family: var(--font-mono);
}

.bar-bg {
  flex: 1;
  height: 4px;
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
  overflow: hidden;
  min-width: 60px;
}

.bar-fill {
  height: 100%;
  background: var(--success);
  transition: width 0.5s ease;
}

.bar-fill.info {
  background: var(--info);
}

.bar-fill.warn {
  background: var(--error);
}

.val {
  font-family: var(--font-mono);
  font-size: 11px;
  width: 80px;
  text-align: right;
  flex-shrink: 0;
}

.val-text {
  flex: 1;
  text-align: left;
  color: var(--text-highlight);
}

.val-text.hot {
  color: var(--error);
}

.ip {
  font-size: 10px;
}
</style>
