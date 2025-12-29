<template>
  <div class="message">
    <div class="message-header">
      <div class="channel">{{ message.channel_name }}</div>
      <div class="timestamp">{{ formatDate(message.datetime_local) }}</div>
    </div>
    <div class="sender">{{ message.sender_name || 'Unknown Sender' }}</div>
    <div class="message-content" v-html="formatMessageContent(message.text_translated)"></div>
    <div class="message-meta">
      <span>Views: {{ message.views || 0 }}</span>
      <span>Forwards: {{ message.forwards || 0 }}</span>
      <span>Type: {{ message.media_type || 'text' }}</span>
    </div>
    <div class="message-tags">
      <strong>Tags:</strong>
      <MessageTags
        :tags="message.tags"
        :message-id="message.id"
        @edit-tags="editTags"
        @remove-tag="removeTag"
      />
      <button class="action-btn" @click="handleEditTags">✏️ Edit Tags</button>
    </div>
    <div class="message-actions">
      <button
        class="action-btn"
        :class="{ active: message.read }"
        @click="toggleRead(message.id)"
      >
        {{ message.read ? '✓ Read' : 'Mark as Read' }}
      </button>
      <button
        class="action-btn"
        :class="{ active: message.like }"
        @click="toggleLike(message.id)"
      >
        {{ message.like ? '❤️ Liked' : '🤍 Like' }}
      </button>
      <button
        class="action-btn"
        :class="{ active: message.trashed_at }"
        @click="toggleTrash(message.id)"
      >
        {{ message.trashed_at ? '🗑️ Trashed' : 'Move to Trash' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MessageTags from './MessageTags.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['toggleRead', 'toggleLike', 'toggleTrash', 'editTags'])

// Methods
const formatDate = (dateString) => {
  if (!dateString) return 'Unknown date'

  const date = new Date(dateString)
  return date.toLocaleString()
}

const formatMessageContent = (content) => {
  if (!content) return ''

  // Convert markdown links to HTML links
  return content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
}

const toggleRead = (messageId) => {
  emit('toggleRead', messageId)
}

const toggleLike = (messageId) => {
  emit('toggleLike', messageId)
}

const toggleTrash = (messageId) => {
  emit('toggleTrash', messageId)
}

const handleEditTags = () => {
  const tagString = props.message.tags || ''
  const input = prompt('Enter tags to add (comma-separated).\nCurrent tags: ' + (tagString || 'None'), '')

  if (input !== null) {
    // If user entered something, add it to existing tags
    if (input.trim() !== '') {
      // Parse new tags
      const newTagsArray = input.split(',').map(tag => tag.trim()).filter(tag => tag)

      // If message already has tags, parse them
      let currentTagsArray = []
      if (props.message.tags) {
        currentTagsArray = props.message.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
      }

      // Combine with existing tags, avoiding duplicates
      const combinedTags = [...new Set([...currentTagsArray, ...newTagsArray])]
      const combinedTagString = combinedTags.join(', ')

      editTags(props.message.id, combinedTagString)
    }
  }
}

const editTags = (messageId, tags) => {
  emit('editTags', messageId, tags)
}

const removeTag = (messageId, tagToRemove) => {
  let currentTags = []
  if (props.message.tags) {
    // Split current tags
    currentTags = props.message.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
  }

  // Remove the specified tag
  const updatedTags = currentTags.filter(tag => tag !== tagToRemove)

  // Join remaining tags (empty string if no tags left)
  const newTagsString = updatedTags.length > 0 ? updatedTags.join(', ') : ''

  // Update tags
  editTags(props.message.id, newTagsString)
}
</script>

<style scoped>
.message {
  padding: 20px;
  border-bottom: 1px solid var(--border);
}

.message:last-child {
  border-bottom: none;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 10px;
}

.channel {
  font-weight: bold;
  color: var(--primary);
}

.timestamp {
  color: var(--secondary);
  font-size: 14px;
}

.sender {
  color: var(--success);
  font-weight: 500;
}

.message-content {
  margin: 10px 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-meta {
  display: flex;
  gap: 15px;
  font-size: 14px;
  color: var(--secondary);
  margin-bottom: 15px;
}

.message-tags {
  margin: 10px 0;
  padding: 8px;
  background-color: #f1f5f9;
  border-radius: 4px;
}

.message-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--border);
}

.action-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--background);
  border-color: var(--primary);
  color: var(--primary);
}

.action-btn.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

@media (max-width: 768px) {
  .message-header {
    flex-direction: column;
  }
}
</style>