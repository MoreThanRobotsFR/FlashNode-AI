<template>
  <div class="panel-container">
    <div class="header">
      <h3 class="panel-title">⏱️ Operation History</h3>
      <span class="badge">SQLite</span>
    </div>
    
    <div class="logs">
      <div class="log-row">
        <span class="time">14:32:11</span>
        <span class="status success">SUCCESS</span>
        <span class="action">Pipeline Prod_Board_V1_Full_Deploy completed</span>
      </div>
      <div class="log-row">
        <span class="time">14:32:04</span>
        <span class="status info">STARTED</span>
        <span class="action">Flash ESP32 via esptool</span>
      </div>
      <div class="log-row">
        <span class="time">14:31:55</span>
        <span class="status error">FAILED</span>
        <span class="action">Timeout waiting for USB RP2040</span>
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

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.panel-title {
  font-size: 13px;
  color: var(--text-muted);
  text-transform: uppercase;
}

.badge {
  font-size: 10px;
  background: rgba(255,255,255,0.1);
  padding: 2px 6px;
  border-radius: 10px;
}

.logs {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-row {
  display: flex;
  gap: 15px;
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 4px 0;
  border-bottom: 1px solid rgba(255,255,255,0.02);
}

.time {
  color: var(--text-muted);
}

.status {
  width: 60px;
  font-weight: 600;
}

.status.success { color: var(--success); }
.status.info { color: var(--info); }
.status.error { color: var(--error); }

.action {
  color: var(--text-main);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
