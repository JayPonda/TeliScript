<template>
  <div class="container">
    <BackendStatus :isConnected="isConnected" :reconnectTime="reconnectTime" :nextCheckTime="nextCheckTime" />
    <header>
      <h1>Telegram Messages Dashboard</h1>
      <p>Browse and filter your collected Telegram messages</p>
    </header>

    <MessageFilters
      :channels="channels"
      @apply-filters="applyFilters"
      @update-filters="updateFilters"
      v-model:filters="currentFilters"
    />

    <DashboardStats
      :total-messages="stats.totalMessages"
      :total-channels="stats.totalChannels"
      :date-range="stats.dateRange"
    />

    <ChannelsTable
      :channels="channels"
      @refresh-channels="refreshChannels"
    />

    <MessageList
      :messages="messages"
      :loading="loading"
      @toggle-read="toggleRead"
      @toggle-like="toggleLike"
      @toggle-trash="toggleTrash"
      @edit-tags="editTags"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps } from 'vue'
import MessageFilters from '@/components/MessageFilters.vue'
import DashboardStats from '@/components/DashboardStats.vue'
import MessageList from '@/components/MessageList.vue'
import ChannelsTable from '@/components/ChannelsTable.vue'
import BackendStatus from '@/components/BackendStatus.vue'

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

// State
const messages = ref([])
const channels = ref([])
const loading = ref(false)
const stats = ref({
  totalMessages: 0,
  totalChannels: 0,
  dateRange: ''
})

const currentFilters = ref({
  channel: '',
  search: '',
  startDate: '',
  endDate: '',
  filterRead: false,
  filterLike: false,
  filterTrash: false
})

// Methods
const loadStats = async () => {
  try {
    const response = await fetch('/api/stats')
    const result = await response.json()

    if (result.success) {
      const data = result.data
      stats.value.totalMessages = data.total_messages
      stats.value.totalChannels = data.total_channels

      if (data.date_range.earliest && data.date_range.latest) {
        const earliest = new Date(data.date_range.earliest).toLocaleDateString()
        const latest = new Date(data.date_range.latest).toLocaleDateString()
        stats.value.dateRange = `${earliest} - ${latest}`
      } else {
        stats.value.dateRange = 'N/A'
      }
    }
  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

const loadChannels = async () => {
  try {
    const response = await fetch('/api/channels')
    const result = await response.json()

    if (result.success) {
      channels.value = result.data
    }
  } catch (error) {
    console.error('Error loading channels:', error)
  }
}

const loadMessages = async () => {
  try {
    loading.value = true

    // Build query parameters
    const params = new URLSearchParams()
    params.append('limit', 50)
    params.append('offset', 0)

    if (currentFilters.value.channel) {
      params.append('channel', currentFilters.value.channel)
    }

    if (currentFilters.value.search) {
      params.append('search', currentFilters.value.search)
    }

    if (currentFilters.value.startDate) {
      params.append('start_date', currentFilters.value.startDate)
    }

    if (currentFilters.value.endDate) {
      params.append('end_date', currentFilters.value.endDate)
    }

    if (currentFilters.value.filterRead) {
      params.append('filter_read', '1')
    }

    if (currentFilters.value.filterLike) {
      params.append('filter_like', '1')
    }

    if (currentFilters.value.filterTrash) {
      params.append('filter_trash', '1')
    }

    const response = await fetch(`/api/messages?${params.toString()}`)
    const result = await response.json()

    if (result.success) {
      messages.value = result.data
    } else {
      console.error('Error loading messages:', result.error)
    }
  } catch (error) {
    console.error('Error loading messages:', error)
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  loadMessages()
}

const updateFilters = (filters) => {
  currentFilters.value = filters
}

const toggleRead = async (messageId) => {
  try {
    const response = await fetch(`/api/messages/${messageId}/read`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const result = await response.json()
    if (result.success) {
      await loadMessages()
    } else {
      alert('Error: ' + result.error)
    }
  } catch (error) {
    alert('Error marking as read: ' + error.message)
  }
}

const toggleLike = async (messageId) => {
  try {
    const response = await fetch(`/api/messages/${messageId}/like`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const result = await response.json()
    if (result.success) {
      await loadMessages()
    } else {
      alert('Error: ' + result.error)
    }
  } catch (error) {
    alert('Error toggling like: ' + error.message)
  }
}

const toggleTrash = async (messageId) => {
  try {
    const response = await fetch(`/api/messages/${messageId}/trash`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const result = await response.json()
    if (result.success) {
      await loadMessages()
    } else {
      alert('Error: ' + result.error)
    }
  } catch (error) {
    alert('Error toggling trash: ' + error.message)
  }
}

const editTags = async (messageId, tags) => {
  try {
    const response = await fetch(`/api/messages/${messageId}/tags`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tags: tags })
    })

    const result = await response.json()
    if (result.success) {
      await loadMessages() // Reload messages to show updated tags
    } else {
      alert('Error updating tags: ' + result.error)
    }
  } catch (error) {
    alert('Error updating tags: ' + error.message)
  }
}

const refreshChannels = async () => {
  await loadChannels()
  await loadStats()
  await loadMessages()
}

// Lifecycle
onMounted(async () => {
  await loadStats()
  await loadChannels()
  await loadMessages()
})
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
</style>