<script setup>
import { onMounted, ref, onBeforeUnmount } from 'vue';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { wsManager } from '../services/ws';
import 'xterm/css/xterm.css';

const terminalContainer = ref(null);

onMounted(() => {
  const term = new Terminal({
    theme: {
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
    },
    fontFamily: '"JetBrains Mono", monospace',
    fontSize: 12,
    cursorBlink: true
  });
  
  const fitAddon = new FitAddon();
  term.loadAddon(fitAddon);
  
  term.open(terminalContainer.value);
  fitAddon.fit();
  
  
  let wsUnsubscribe = null;
  // Mock data -> replace by real ws stream
  term.writeln('\x1b[1;36mFlashNode-AI\x1b[0m Terminal Multiplexer');
  term.writeln('Connecting to /ws/flash/output...');
  
  wsUnsubscribe = wsManager.subscribe('/flash/output', (payload) => {
    if (payload && payload.data) {
      // Just write incoming data stream to Xterm
      term.write(payload.data)
    }
  })

  // Simulated connected
  setTimeout(() => term.writeln('\x1b[1;32mConnected.\x1b[0m'), 500);
  
  onBeforeUnmount(() => {
    if (wsUnsubscribe) wsUnsubscribe()
    term.dispose()
  })
});
</script>

<template>
  <div class="panel-container">
    <div class="tabs">
      <div class="tab active">📤 Flash Output</div>
      <div class="tab">📡 /dev/ttyUSB0</div>
      <div class="tab">🔬 GDB</div>
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
  gap: 5px;
  margin-bottom: 15px;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 5px;
}

.tab {
  padding: 5px 12px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 4px 4px 0 0;
  transition: all 0.2s;
}

.tab:hover {
  background: rgba(255,255,255,0.05);
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
  padding: 10px;
}
</style>
