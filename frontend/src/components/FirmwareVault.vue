<script setup>
import { useFlasherStore } from '../stores/flasher'
import { ref } from 'vue'

const flasherStore = useFlasherStore()
const fileInputRP2040 = ref(null)
const fileInputESP32 = ref(null)

const triggerUpload = (target) => {
  if (target === 'RP2040') fileInputRP2040.value.click()
  if (target === 'ESP32') fileInputESP32.value.click()
}

const onFileChange = async (e, target) => {
  const file = e.target.files[0]
  if (file) {
    try {
      await flasherStore.uploadFirmware(file, target)
    } finally {
      e.target.value = '' // Reset input
    }
  }
}
</script>

<template>
  <div class="panel-container">
    <!-- Hidden inputs for file upload -->
    <input type="file" ref="fileInputRP2040" style="display:none;" @change="e => onFileChange(e, 'RP2040')" />
    <input type="file" ref="fileInputESP32" style="display:none;" @change="e => onFileChange(e, 'ESP32')" />
    
    <div class="header-row">
      <h3 class="panel-title">📦 Firmware Vault</h3>
      <button class="glow-btn" style="font-size: 10px; padding: 4px 8px;">+ UPLOAD</button>
    </div>
    
    <div class="vault-grid">
      <div class="vault-section">
        <div class="section-header">
          <h4 class="section-title">RP2040/</h4>
          <button class="glow-btn small-btn" @click="triggerUpload('RP2040')">+ UPLOAD</button>
        </div>
        <div v-for="fw in flasherStore.vaultFirmwares['RP2040']" :key="fw.name" class="file-item">
          <span class="file-name">{{ fw.name }}</span>
          <span class="file-meta">MD5: {{ fw.md5 ? fw.md5.substring(0,6)+'...' : 'N/A' }} ✅</span>
          <div class="file-actions">
            <button @click="flasherStore.deleteFirmware(fw.name)">🗑</button>
            <button>🎯 Flash</button>
          </div>
        </div>
        <div v-if="!flasherStore.vaultFirmwares['RP2040']?.length" class="empty-text">No firmwares</div>
      </div>
      
      <div class="vault-section">
        <div class="section-header">
          <h4 class="section-title">ESP32/</h4>
          <button class="glow-btn small-btn" @click="triggerUpload('ESP32')">+ UPLOAD</button>
        </div>
        <div v-for="fw in flasherStore.vaultFirmwares['ESP32']" :key="fw.name" class="file-item">
          <span class="file-name">{{ fw.name }}</span>
          <span class="file-meta">MD5: {{ fw.md5 ? fw.md5.substring(0,6)+'...' : 'N/A' }} ✅</span>
          <div class="file-actions">
             <button @click="flasherStore.deleteFirmware(fw.name)">🗑</button>
             <button>🎯 Flash</button>
          </div>
        </div>
        <div v-if="!flasherStore.vaultFirmwares['ESP32']?.length" class="empty-text">No firmwares</div>
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

.small-btn {
  font-size: 10px;
  padding: 4px 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.empty-text {
  font-size: 10px;
  color: var(--text-muted);
  font-style: italic;
  padding-left: 5px;
}
</style>
