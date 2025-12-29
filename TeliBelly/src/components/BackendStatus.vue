<template>
  <div v-if="!isConnected" class="backend-status-disconnected">
    <div class="status-indicator">
      <div class="status-dot disconnected"></div>
      <span>Backend Disconnected</span>
    </div>
    <div v-if="reconnectTime > 0" class="reconnect-info">
      Reconnecting in {{ reconnectTime }} seconds...
    </div>
  </div>
  <div v-else class="backend-status-connected">
    <div class="status-indicator">
      <div class="status-dot connected"></div>
      <span>Backend Connected</span>
    </div>
    <div v-if="nextCheckTime > 0" class="reconnect-info">
      Rechecking in {{ nextCheckTime }} seconds...
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  isConnected: {
    type: Boolean,
    required: true,
  },
  reconnectTime: {
    type: Number,
    required: true,
  },
  nextCheckTime: {
    type: Number,
    required: true,
  },
})
</script>

<style scoped>
.backend-status-disconnected,
.backend-status-connected {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 1000;
  padding: 10px 15px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.backend-status-disconnected {
  background-color: #fee2e2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.backend-status-connected {
  background-color: #dcfce7;
  border: 1px solid #bbf7d0;
  color: #14532d;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot.connected {
  background-color: #22c55e;
}

.status-dot.disconnected {
  background-color: #ef4444;
}

.reconnect-info {
  margin-top: 5px;
  font-size: 12px;
  opacity: 0.8;
}
</style>
