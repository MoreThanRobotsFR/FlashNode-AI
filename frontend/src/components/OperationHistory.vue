<script setup>
import { useSystemStore } from '../stores/system'
import { onMounted, ref } from 'vue'
import api from '../services/api'

const history = ref([])
const loading = ref(false)

async function fetchHistory() {
  loading.value = true
  try {
    const res = await api.get('/system/history', { params: { limit: 50 } })
    history.value = res.data || []
  } catch (err) {
    console.error('Failed to fetch history', err)
  } finally {
    loading.value = false
  }
}

function formatTime(timestamp) {
  if (!timestamp) return '--:--:--'
  try {
    const d = new Date(timestamp)
    return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return timestamp
  }
}

function formatDate(timestamp) {
  if (!timestamp) return ''
  try {
    const d = new Date(timestamp)
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
  } catch {
    return ''
  }
}

function statusClass(status) {
  const s = (status || '').toUpperCase()
  if (s === 'SUCCESS' || s === 'STARTED') return s === 'SUCCESS' ? 'success' : 'info'
  if (s === 'FAILED' || s === 'ERROR') return 'error'
  if (s === 'CANCELLED') return 'warning'
  return 'info'
}

onMounted(() => {
  fetchHistory()
  // Refresh every 10s to pick up new entries
  setInterval(fetchHistory, 10000)
})
</script>

<template>
  <div class="panel-container">
    <div class="header">
      <h3 class="panel-title">⏱️ Operation History</h3>
      <div class="header-actions">
        <button class="glow-btn small-btn" @click="fetchHistory">↻ Refresh</button>
        <span class="badge">SQLite</span>
      </div>
    </div>

    <div class="logs" v-if="!loading && history.length > 0">
      <div v-for="entry in history" :key="entry.id" class="log-row">
        <span class="date">{{ formatDate(entry.timestamp) }}</span>
        <span class="time">{{ formatTime(entry.timestamp) }}</span>
        <span :class="['status', statusClass(entry.status)]">{{ entry.status }}</span>
        <span class="action">{{ entry.action }}</span>
        <span class="details" v-if="entry.details">{{ entry.details }}</span>
        <span class="duration" v-if="entry.duration_s">{{ entry.duration_s }}s</span>
      </div>
    </div>

    <div class="empty" v-else-if="!loading">
      <span>Aucune opération enregistrée</span>
    </div>

    <div class="empty" v-else>
      <span>Chargement...</span>
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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

.small-btn {
  font-size: 9px;
  padding: 2px 8px;
}

.logs {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.log-row {
  display: flex;
  gap: 12px;
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 3px 0;
  border-bottom: 1px solid rgba(255,255,255,0.02);
  align-items: center;
}

.date {
  color: var(--text-muted);
  opacity: 0.6;
  font-size: 10px;
  width: 40px;
}

.time {
  color: var(--text-muted);
  width: 55px;
}

.status {
  width: 65px;
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
}

.status.success { color: var(--success); }
.status.info { color: var(--info); }
.status.error { color: var(--error); }
.status.warning { color: var(--warning); }

.action {
  color: var(--text-main);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.details {
  color: var(--text-muted);
  font-size: 10px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.duration {
  color: var(--text-highlight);
  font-size: 10px;
  width: 40px;
  text-align: right;
}

.empty {
  color: var(--text-muted);
  font-size: 11px;
  font-style: italic;
  padding: 10px 0;
}
</style>
