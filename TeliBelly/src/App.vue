<template>
  <div id="app-container">
    <router-view v-slot="{ Component }">
      <component :is="Component" :isConnected="!showConnectionMessage" :reconnectTime="reconnectTime"
        :nextCheckTime="nextCheckTime" />
    </router-view>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const showConnectionMessage = ref(true)
const reconnectTime = ref(0)
const nextCheckTime = ref(0) // New ref for healthy check countdown
let healthCheckTimeout = null
let countdownInterval = null
let healthyCountdownInterval = null // New interval for healthy countdown

const checkBackendConnection = async () => {
  try {
    const response = await fetch('/api/health')
    const data = await response.json()

    if (data.status === 'healthy') {
      showConnectionMessage.value = false
      clearInterval(countdownInterval)
      clearInterval(healthyCountdownInterval) // Clear previous healthy countdown
      reconnectTime.value = 0
      nextCheckTime.value = data.next_check_in_seconds // Set initial next check time

      healthyCountdownInterval = setInterval(() => {
        nextCheckTime.value -= 1
        if (nextCheckTime.value <= 0) {
          clearInterval(healthyCountdownInterval)
          checkBackendConnection() // Trigger next check
        }
      }, 1000)

      // scheduleHealthCheck(data.next_check_in_seconds * 1000) // This is now handled by healthyCountdownInterval
    } else {
      throw new Error('Backend unhealthy')
    }
  } catch (error) {
    console.error('Health check failed:', error)
    showConnectionMessage.value = true
    clearInterval(healthyCountdownInterval) // Clear healthy countdown if it becomes unhealthy
    nextCheckTime.value = 0 // Reset next check time
    reconnectTime.value = 1
    clearInterval(countdownInterval)
    countdownInterval = setInterval(() => {
      reconnectTime.value -= 1
      if (reconnectTime.value <= 0) {
        checkBackendConnection()
      }
    }, 1000)
  }
}

onMounted(() => {
  checkBackendConnection()
})

onUnmounted(() => {
  clearTimeout(healthCheckTimeout)
  clearInterval(countdownInterval)
  clearInterval(healthyCountdownInterval) // Clear new interval
})
</script>

<style>
:root {
  --primary: #2563eb;
  --primary-dark: #1d4ed8;
  --secondary: #64748b;
  --success: #10b981;
  --background: #f8fafc;
  --card: #ffffff;
  --text: #1e293b;
  --border: #e2e8f0;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: var(--background);
  color: var(--text);
  line-height: 1.6;
}

.connection-message {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.message-content {
  background-color: var(--card);
  padding: 30px;
  border-radius: 10px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  max-width: 400px;
  width: 90%;
}

.message-content h3 {
  color: var(--text);
  margin-bottom: 15px;
}

.message-content p {
  color: var(--secondary);
  margin-bottom: 20px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background-color: var(--primary);
  transition: width 0.1s linear;
}
</style>
