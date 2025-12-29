<template>
  <span v-if="!tagArray || tagArray.length === 0" class="no-tags">None</span>
  <span v-else>
    <span
      v-for="tag in tagArray"
      :key="tag"
      class="tag"
    >
      {{ tag }}
      <button
        class="remove-tag-btn"
        @click="removeTag(tag)"
      >
        ×
      </button>
    </span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tags: {
    type: String,
    default: ''
  },
  messageId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['editTags', 'removeTag'])

// Computed property to parse tags into an array
const tagArray = computed(() => {
  if (!props.tags || props.tags.trim() === '') {
    return []
  }
  return props.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
})

// Methods
const removeTag = (tagToRemove) => {
  emit('removeTag', props.messageId, tagToRemove)
}
</script>

<style scoped>
.tag {
  display: inline-block;
  background-color: #2563eb;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  margin-right: 4px;
  margin-bottom: 4px;
  position: relative;
}

.remove-tag-btn {
  background: none;
  border: none;
  color: white;
  font-weight: bold;
  cursor: pointer;
  padding: 0 2px;
  margin-left: 4px;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.remove-tag-btn:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.no-tags {
  color: #94a3b8;
  font-style: italic;
}
</style>