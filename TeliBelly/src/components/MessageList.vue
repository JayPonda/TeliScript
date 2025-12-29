<template>
  <div class="messages" id="messages-container">
    <div v-if="loading" class="loading">Loading messages...</div>
    <div v-else-if="messages.length === 0" class="loading">No messages found</div>
    <MessageItem
      v-for="message in messages"
      :key="message.id"
      :message="message"
      @toggle-read="toggleRead"
      @toggle-like="toggleLike"
      @toggle-trash="toggleTrash"
      @edit-tags="editTags"
    />
  </div>
</template>

<script setup>
import MessageItem from './MessageItem.vue'

defineProps({
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
</style>