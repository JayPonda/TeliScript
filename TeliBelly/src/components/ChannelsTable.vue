<template>
  <div class="channels-table-container">
    <div class="table-header">
      <h2>Channel Management</h2>
      <div class="controls">
        <button @click="fetchChannels" :disabled="loading" class="refresh-btn">
          <span v-if="loading">🔄 Refreshing...</span>
          <span v-else>🔄 Refresh Channels</span>
        </button>
        <button @click="startScraping" :disabled="isScraping" class="scrape-btn">
          <span v-if="isScraping">⏳ Scraping...</span>
          <span v-else>🔍 Refetch All Channels</span>
        </button>
      </div>
    </div>

    <!-- Scraping Status -->
    <div v-if="scrapingStatus.is_running" class="scraping-status">
      <div class="status-info">
        <h3>.telegram Scrape in Progress</h3>
        <p>{{ scrapingStatus.progress }}</p>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: progressPercentage + '%' }"
          ></div>
        </div>
        <p>Processed: {{ scrapingStatus.channels_processed }}/{{ scrapingStatus.total_channels }} channels</p>
      </div>
    </div>

    <!-- Date Range Controls -->
    <div class="date-controls">
      <div class="control-group">
        <label for="days-back">Days Back:</label>
        <input
          type="number"
          id="days-back"
          v-model.number="scrapeOptions.daysBack"
          min="1"
          max="365"
          class="days-input"
        >
      </div>
      <div class="control-group">
        <label for="message-limit">Message Limit:</label>
        <input
          type="number"
          id="message-limit"
          v-model.number="scrapeOptions.limit"
          min="1"
          max="10000"
          class="limit-input"
        >
      </div>
      <button @click="startScrapingWithOptions" :disabled="isScraping" class="apply-options-btn">
        Apply & Refetch
      </button>
    </div>

    <!-- Channels Table -->
    <div class="table-wrapper">
      <table class="channels-table">
        <thead>
          <tr>
            <th>Channel Name</th>
            <th>Messages</th>
            <th>Last Backup</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="channel in channels" :key="channel.channel_name">
            <td>{{ channel.channel_name }}</td>
            <td>{{ channel.total_messages?.toLocaleString() || 0 }}</td>
            <td>{{ formatDate(channel.last_backup_timestamp) }}</td>
            <td>
              <span
                :class="['status-badge', getStatusClass(channel.last_backup_timestamp)]"
              >
                {{ getStatusText(channel.last_backup_timestamp) }}
              </span>
            </td>
            <td>
              <button
                @click="refetchChannel(channel)"
                :disabled="isScraping"
                class="refetch-channel-btn"
              >
                Refetch
              </button>
            </td>
          </tr>
          <tr v-if="channels.length === 0">
            <td colspan="5" class="no-data">No channels found</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

// Props
const props = defineProps({
  channels: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['refreshChannels'])

// State
const loading = ref(false)
const isScraping = ref(false)
const scrapingStatus = ref({
  is_running: false,
  progress: '',
  channels_processed: 0,
  total_channels: 0
})

const scrapeOptions = ref({
  daysBack: 3,
  limit: 1000
})

// Computed
const progressPercentage = computed(() => {
  if (!scrapingStatus.value.total_channels) return 0
  return Math.round(
    (scrapingStatus.value.channels_processed / scrapingStatus.value.total_channels) * 100
  )
})

// Methods
const fetchChannels = async () => {
  loading.value = true
  try {
    await emit('refreshChannels')
  } finally {
    loading.value = false
  }
}

const startScraping = async () => {
  isScraping.value = true
  try {
    const response = await fetch('/api/scraper/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        days_back: scrapeOptions.value.daysBack,
        limit: scrapeOptions.value.limit
      })
    })

    const result = await response.json()
    if (!result.success) {
      alert('Error starting scrape: ' + result.error)
    }
  } catch (error) {
    alert('Error starting scrape: ' + error.message)
  } finally {
    isScraping.value = false
  }
}

const startScrapingWithOptions = () => {
  startScraping()
}

const refetchChannel = async (channel) => {
  isScraping.value = true
  try {
    // For now, we'll refetch all channels since the API doesn't support
    // single channel refetching. In a more advanced implementation,
    // you might pass channel-specific parameters.
    const response = await fetch('/api/scraper/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        days_back: scrapeOptions.value.daysBack,
        limit: scrapeOptions.value.limit
      })
    })

    const result = await response.json()
    if (!result.success) {
      alert('Error refetching channel: ' + result.error)
    }
  } catch (error) {
    alert('Error refetching channel: ' + error.message)
  } finally {
    isScraping.value = false
  }
}

const formatDate = (timestamp) => {
  if (!timestamp) return 'Never'
  try {
    return new Date(timestamp).toLocaleString()
  } catch (e) {
    return timestamp
  }
}

const getStatusClass = (timestamp) => {
  if (!timestamp) return 'status-stale'

  const lastBackup = new Date(timestamp)
  const now = new Date()
  const diffHours = Math.abs(now - lastBackup) / 36e5

  if (diffHours < 24) return 'status-active'
  if (diffHours < 168) return 'status-recent' // 1 week
  return 'status-stale'
}

const getStatusText = (timestamp) => {
  if (!timestamp) return 'Stale'

  const lastBackup = new Date(timestamp)
  const now = new Date()
  const diffHours = Math.abs(now - lastBackup) / 36e5

  if (diffHours < 1) return 'Active'
  if (diffHours < 24) return 'Today'
  if (diffHours < 168) return 'Recent'
  return 'Stale'
}

// Poll for scraping status
const pollScrapingStatus = async () => {
  try {
    const response = await fetch('/api/scraper/status')
    const result = await response.json()

    if (result.success) {
      scrapingStatus.value = result.status

      // Continue polling if scraping is still running
      if (result.status.is_running) {
        setTimeout(pollScrapingStatus, 2000) // Poll every 2 seconds
      } else {
        // Refresh channels when scraping completes
        if (scrapingStatus.value.channels_processed > 0) {
          setTimeout(fetchChannels, 1000) // Refresh after 1 second
        }
      }
    }
  } catch (error) {
    console.error('Error fetching scraping status:', error)
    // Continue polling even if there's an error
    setTimeout(pollScrapingStatus, 5000) // Poll every 5 seconds on error
  }
}

// Lifecycle
onMounted(() => {
  // Start polling for scraping status
  pollScrapingStatus()
})
</script>

<style scoped>
.channels-table-container {
  background: var(--card);
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.table-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.scraping-status {
  background: #e3f2fd;
  border: 1px solid #2196f3;
  border-radius: 5px;
  padding: 15px;
  margin-bottom: 20px;
}

.status-info h3 {
  margin: 0 0 10px 0;
  color: #1976d2;
}

.status-info p {
  margin: 5px 0;
}

.progress-bar {
  width: 100%;
  height: 10px;
  background: #bbdefb;
  border-radius: 5px;
  overflow: hidden;
  margin: 10px 0;
}

.progress-fill {
  height: 100%;
  background: #2196f3;
  transition: width 0.3s ease;
}

.date-controls {
  display: flex;
  gap: 15px;
  align-items: end;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  min-width: 120px;
}

.control-group label {
  margin-bottom: 5px;
  font-weight: 500;
  color: var(--text-secondary);
}

.days-input,
.limit-input {
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 14px;
}

.table-wrapper {
  overflow-x: auto;
}

.channels-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.channels-table th,
.channels-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.channels-table th {
  background: var(--background-light);
  font-weight: 600;
  color: var(--text-secondary);
}

.no-data {
  text-align: center;
  padding: 30px;
  color: var(--text-secondary);
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-active {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-recent {
  background: #fff8e1;
  color: #f57f17;
}

.status-stale {
  background: #ffebee;
  color: #c62828;
}

button {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.refresh-btn,
.apply-options-btn {
  background: var(--primary);
  color: white;
}

.refresh-btn:hover:not(:disabled),
.apply-options-btn:hover:not(:disabled) {
  background: var(--primary-dark);
}

.scrape-btn {
  background: #4caf50;
  color: white;
}

.scrape-btn:hover:not(:disabled) {
  background: #388e3c;
}

.refetch-channel-btn {
  background: #2196f3;
  color: white;
}

.refetch-channel-btn:hover:not(:disabled) {
  background: #1976d2;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    align-items: stretch;
  }

  .controls {
    justify-content: center;
  }

  .date-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .control-group {
    width: 100%;
  }
}
</style>