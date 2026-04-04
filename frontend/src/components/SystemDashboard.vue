<template>
  <div class="panel-container">
    <h3 class="panel-title">🖥️ Base Station</h3>
    
    <div class="metrics">
      <div class="metric">
        <span class="label">CPU</span>
        <div class="bar-bg"><div class="bar-fill" style="width: 25%"></div></div>
        <span class="val">25%</span>
      </div>

      <div class="metric">
        <span class="label">RAM</span>
        <div class="bar-bg"><div class="bar-fill info" style="width: 15%"></div></div>
        <span class="val">2.1/16 GB</span>
      </div>

      <div class="metric">
        <span class="label">TEMP</span>
        <span class="val val-text">45°C</span>
      </div>
      
       <div class="metric">
        <span class="label">IP</span>
        <span class="val val-text">192.168.1.42</span>
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
