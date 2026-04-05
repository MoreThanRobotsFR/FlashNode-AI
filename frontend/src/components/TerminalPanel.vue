<script setup>
import { onMounted, ref, onBeforeUnmount, nextTick, watch } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { wsManager } from '../services/ws'
import { useHardwareStore } from '../stores/hardware'
import 'xterm/css/xterm.css'

const hardwareStore = useHardwareStore()

const activeTab = ref('flash_output')
const terminalContainer = ref(null)

const XTERM_THEME = {
  background: 'transparent',
  foreground: '#e2e8f0',
  cursor: '#5eead4',
  selectionBackground: 'rgba(94, 234, 212, 0.3)',
  black: '#000000',
  red: '#ef4444',
  green: '#10b981',
  yellow: '#f59e0b',
  blue: '#3b82f6',
  magenta: '#d946ef',
  cyan: '#06b6d4',
  white: '#ffffff',
}

// Terminal instances and WS unsubscribers per tab
const terminals = {}
const fitAddons = {}
const wsUnsubs = {}

const tabs = ref([
  { id: 'flash_output', label: '📤 Flash Output', wsPath: '/flash/output', dataKey: 'data' },
  { id: 'system_logs', label: '🖥️ System Logs', wsPath: '/system/logs', dataKey: 'msg' },
])

// Dynamically add serial port tabs based on detected ports
watch(() => hardwareStore.serialPorts, (ports) => {
  // Remove old serial tabs
  tabs.value = tabs.value.filter(t => !t.id.startsWith('serial_'))
  // Add tabs for detected serial ports
  for (const port of (ports || [])) {
    const portName = port.port.replace(/[/\\]/g, '_').replace(':', '')
    tabs.value.push({
      id: `serial_${portName}`,
      label: `📡 ${port.type !== 'Unknown' ? port.type : port.port}`,
      wsPath: `/serial/${portName}`,
      dataKey: 'data'
    })
  }
}, { immediate: true })

function createTerminal(tabId) {
  if (terminals[tabId]) return terminals[tabId]

  const term = new Terminal({
    theme: XTERM_THEME,
    fontFamily: '"JetBrains Mono", monospace',
    fontSize: 12,
    cursorBlink: true,
    scrollback: 5000,
    convertEol: true,
  })

  const fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  terminals[tabId] = term
  fitAddons[tabId] = fitAddon

  return term
}

function mountTerminal(tabId) {
  const container = terminalContainer.value
  if (!container) return
  
  // Clear container
  container.innerHTML = ''
  
  const term = createTerminal(tabId)
  
  if (!term.element) {
    // First time opening this terminal
    term.open(container)
    fitAddons[tabId].fit()
    
    // Welcome message
    const tabDef = tabs.value.find(t => t.id === tabId)
    term.writeln(`\x1b[1;36mFlashNode-AI\x1b[0m — ${tabDef?.label || tabId}`)
    
    // Subscribe to WS
    if (tabDef?.wsPath && !wsUnsubs[tabId]) {
      term.writeln(`Connecting to ${tabDef.wsPath}...`)
      wsUnsubs[tabId] = wsManager.subscribe(tabDef.wsPath, (payload) => {
        if (payload) {
          const text = payload[tabDef.dataKey] || payload.data || payload.msg || JSON.stringify(payload)
          term.writeln(text)
        }
      })
      setTimeout(() => term.writeln('\x1b[1;32mConnected.\x1b[0m'), 300)
    }
  } else {
    // Terminal already created, just re-attach
    container.appendChild(term.element)
    fitAddons[tabId].fit()
  }
}

function switchTab(tabId) {
  activeTab.value = tabId
  nextTick(() => mountTerminal(tabId))
}

onMounted(() => {
  nextTick(() => mountTerminal(activeTab.value))
  
  // Re-fit on window resize
  window.addEventListener('resize', handleResize)
})

function handleResize() {
  const currentFit = fitAddons[activeTab.value]
  if (currentFit) {
    try { currentFit.fit() } catch {}
  }
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  // Cleanup
  Object.values(wsUnsubs).forEach(unsub => { if (unsub) unsub() })
  Object.values(terminals).forEach(term => { try { term.dispose() } catch {} })
})
</script>

<template>
  <div class="panel-container">
    <div class="tabs">
      <div
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab', { active: activeTab === tab.id }]"
        @click="switchTab(tab.id)"
      >
        {{ tab.label }}
      </div>
    </div>

    <div class="terminal-wrapper" ref="terminalContainer"></div>
  </div>
</template>

<style scoped>
.panel-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tabs {
  display: flex;
  gap: 3px;
  margin-bottom: 10px;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 5px;
  overflow-x: auto;
  flex-shrink: 0;
}

.tab {
  padding: 5px 10px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 4px 4px 0 0;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.tab:hover {
  background: rgba(255,255,255,0.05);
  color: var(--text-main);
}

.tab.active {
  color: var(--text-highlight);
  background: rgba(94, 234, 212, 0.1);
  border-bottom: 2px solid var(--border-primary);
}

.terminal-wrapper {
  flex: 1;
  overflow: hidden;
  border-radius: 4px;
  background: rgba(0,0,0,0.4);
  padding: 8px;
  min-height: 0;
}
</style>
