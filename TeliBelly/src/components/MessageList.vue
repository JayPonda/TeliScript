<template>
  <div class="messages" id="messages-container">
    <div v-if="loading" class="loading">Loading messages...</div>
    <div v-else-if="groupedMessages.length === 0" class="loading">No messages found</div>
    <template v-else>
      <template v-for="(item, index) in groupedMessages" :key="item.type === 'message' ? item.id : 'date-' + item.date + '-' + index">
        <div v-if="item.type === 'date_separator'" class="date-separator">
          <span>{{ item.date }}</span>
        </div>
        <MessageItem
          v-else
          :message="item"
          @toggle-read="toggleRead"
          @toggle-like="toggleLike"
          @toggle-trash="toggleTrash"
          @edit-tags="editTags"
        />
      </template>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MessageItem from './MessageItem.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggleRead', 'toggleLike', 'toggleTrash', 'editTags'])

const groupedMessages = computed(() => {
  const grouped = []
  let lastDate = null

  // Sort messages by date to ensure correct grouping
  const sortedMessages = [...props.messages].sort((a, b) => new Date(b.datetime_local) - new Date(a.datetime_local))

  for (const message of sortedMessages) {
    const messageDate = message.datetime_local ? message.datetime_local.split(' ')[0] : 'Unknown Date'; // Get YYYY-MM-DD
    if (messageDate !== lastDate) {
      grouped.push({ type: 'date_separator', date: messageDate });
      lastDate = messageDate;
    }
    grouped.push({ type: 'message', ...message });
  }
  return grouped
})

const toggleRead = (messageId) => {
  emit('toggleRead', messageId)
}

const toggleLike = (messageId) => {
  emit('toggleLike', messageId)
}

const toggleTrash = (messageId) => {
  emit('toggleTrash', messageId)
}

const editTags = (messageId, tags) => {
  emit('editTags', messageId, tags)
}
</script>

<style scoped>
.messages {
  background: var(--card);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--secondary);
}

.error {
  background: #fee2e2;
  color: #991b1b;
  padding: 15px;
  border-radius: 5px;
  margin: 20px 0;
}

.date-separator {
  background-color: #e2e8f0;
  padding: 5px 10px;
  margin: 10px 0;
  border-radius: 3px;
  text-align: center;
  font-weight: bold;
}
</style>