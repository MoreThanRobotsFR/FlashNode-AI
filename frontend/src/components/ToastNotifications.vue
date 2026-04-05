<script setup>
import { useNotificationStore } from '../stores/notifications'

const notifStore = useNotificationStore()
</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="notif in notifStore.notifications"
          :key="notif.id"
          :class="['toast', notif.type, { 'toast-exit': !notif.visible }]"
          @click="notifStore.dismiss(notif.id)"
        >
          <span class="toast-icon">
            <template v-if="notif.type === 'success'">✅</template>
            <template v-else-if="notif.type === 'error'">❌</template>
            <template v-else-if="notif.type === 'warning'">⚠️</template>
            <template v-else>ℹ️</template>
          </span>
          <span class="toast-msg">{{ notif.message }}</span>
          <span class="toast-close">×</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 380px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 8px;
  font-family: var(--font-main);
  font-size: 13px;
  color: var(--text-main);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  pointer-events: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  transition: all 0.3s ease;
}

.toast.success {
  background: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.4);
}

.toast.error {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
}

.toast.warning {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.4);
}

.toast.info {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
}

.toast:hover {
  transform: translateX(-4px);
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.5);
}

.toast-icon {
  font-size: 15px;
  flex-shrink: 0;
}

.toast-msg {
  flex: 1;
  line-height: 1.3;
}

.toast-close {
  font-size: 16px;
  opacity: 0.5;
  flex-shrink: 0;
}

.toast-close:hover {
  opacity: 1;
}

/* Transitions */
.toast-enter-active {
  transition: all 0.3s ease;
}

.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
