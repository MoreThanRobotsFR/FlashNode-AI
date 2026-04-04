<template>
  <div class="panel-container">
    <div class="header-row">
      <h3 class="panel-title">📋 Pipeline Studio</h3>
      <div class="pipeline-selector">
        <select class="custom-select">
          <option>Prod_Board_V1_Full_Deploy</option>
        </select>
        <button class="glow-btn">▶ LAUNCH</button>
      </div>
    </div>
    
    <div class="pipeline-steps">
      <div class="step success">
        <div class="step-header">
          <span class="step-num">[1]</span>
          <span class="step-name">Flash RP2040</span>
          <span class="step-status">✅ OK</span>
        </div>
        <div class="step-details">
          <div>Outil: <span class="val">Picotool</span></div>
          <div>Firmware: <span class="val">main_logic_v1.2.uf2</span></div>
        </div>
      </div>

      <div class="step active">
        <div class="step-header">
          <span class="step-num">[2]</span>
          <span class="step-name">Flash ESP32</span>
          <span class="step-status spinner">⚡</span>
        </div>
        <div class="step-details">
          <div>Outil: <span class="val">esptool.py</span></div>
          <div>Port: <span class="val">/dev/ttyUSB0</span></div>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar" style="width: 60%"></div>
        </div>
      </div>

      <div class="step pending">
        <div class="step-header">
          <span class="step-num">[3]</span>
          <span class="step-name">Validation UART</span>
          <span class="step-status">Pending</span>
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

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.panel-title {
  font-size: 15px;
  text-transform: uppercase;
  color: var(--text-main);
  font-weight: 700;
  letter-spacing: 1px;
}

.pipeline-selector {
  display: flex;
  gap: 10px;
}

.custom-select {
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--border-light);
  color: var(--text-main);
  padding: 5px 10px;
  border-radius: 4px;
  outline: none;
  font-family: var(--font-mono);
  font-size: 12px;
}

.pipeline-steps {
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow-y: auto;
  padding-right: 5px;
}

.step {
  border: 1px solid var(--border-light);
  background: rgba(0,0,0,0.2);
  border-radius: 6px;
  padding: 12px;
  transition: all 0.3s;
}

.step.active {
  border-color: var(--info);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.15);
  background: rgba(59, 130, 246, 0.05);
}

.step.success {
  border-left: 3px solid var(--success);
}

.step.pending {
  opacity: 0.5;
}

.step-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.step-num {
  font-family: var(--font-mono);
  color: var(--text-muted);
  margin-right: 10px;
}

.step-name {
  font-weight: 600;
  flex: 1;
}

.step-status {
  font-size: 12px;
}

.spinner {
  animation: pulseGlow 1s infinite alternate;
}

.step-details {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
}

.val {
  color: var(--text-highlight);
}

.progress-bar-container {
  height: 4px;
  background: rgba(0,0,0,0.5);
  border-radius: 2px;
  margin-top: 10px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--info);
  box-shadow: 0 0 10px var(--info);
}
</style>
