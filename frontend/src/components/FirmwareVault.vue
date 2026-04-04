<template>
  <div class="panel-container">
    <div class="header-row">
      <h3 class="panel-title">📦 Firmware Vault</h3>
      <button class="glow-btn" style="font-size: 10px; padding: 4px 8px;">+ UPLOAD</button>
    </div>
    
    <div class="vault-grid">
      <div class="vault-section">
        <h4 class="section-title">RP2040/</h4>
        <div class="file-item">
          <span class="file-name">main_logic_v1.2.elf</span>
          <span class="file-meta">MD5: a3f4... ✅</span>
          <div class="file-actions">
            <button>🎯 Flash</button>
          </div>
        </div>
      </div>
      
      <div class="vault-section">
        <h4 class="section-title">ESP32/</h4>
        <div class="file-item">
          <span class="file-name">wifi_modem_v2.0.bin</span>
          <span class="file-meta">MD5: d4e9... ✅</span>
          <div class="file-actions">
             <button>🎯 Flash</button>
          </div>
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
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 8px;
}

.panel-title {
  font-size: 14px;
  text-transform: uppercase;
  color: var(--text-main);
  font-weight: 600;
}

.vault-grid {
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow-y: auto;
}

.section-title {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.file-item {
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 4px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all 0.2s;
}

.file-item:hover {
  background: rgba(255,255,255,0.05);
  border-color: var(--border-light);
}

.file-name {
  font-size: 12px;
  font-weight: 500;
}

.file-meta {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--success);
}

.file-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}

.file-actions button {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.4);
  color: #60a5fa;
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 10px;
  cursor: pointer;
}

.file-actions button:hover {
  background: rgba(59, 130, 246, 0.2);
}
</style>
