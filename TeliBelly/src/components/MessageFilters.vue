<template>
  <div class="filters">
    <div class="filter-row">
      <div class="filter-group">
        <label for="channel">Channel</label>
        <select id="channel" v-model="localFilters.channel">
          <option value="">All Channels</option>
          <option v-for="channel in channels" :key="channel.channel_name" :value="channel.channel_name">
            {{ channel.channel_name }} ({{ channel.total_messages }})
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label for="search">Search</label>
        <input
          type="text"
          id="search"
          placeholder="Search in messages or senders..."
          v-model="localFilters.search"
          @keypress.enter="handleApplyFilters"
        >
      </div>

      <div class="filter-group">
        <label for="start-date">Start Date</label>
        <input type="date" id="start-date" v-model="localFilters.startDate">
      </div>

      <div class="filter-group">
        <label for="end-date">End Date</label>
        <input type="date" id="end-date" v-model="localFilters.endDate">
      </div>
    </div>

    <div class="filter-row">
      <div class="filter-group">
        <label>
          <input
            type="checkbox"
            id="filter-read"
            v-model="localFilters.filterRead"
          >
          Show Only Read
        </label>
      </div>

      <div class="filter-group">
        <label>
          <input
            type="checkbox"
            id="filter-like"
            v-model="localFilters.filterLike"
          >
          Show Only Liked
        </label>
      </div>

      <div class="filter-group">
        <label>
          <input
            type="checkbox"
            id="filter-trash"
            v-model="localFilters.filterTrash"
          >
          Show Only Trashed
        </label>
      </div>

      <div class="filter-group">
        <label>&nbsp;</label>
        <button id="apply-filters" @click="handleApplyFilters">Apply Filters</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  channels: {
    type: Array,
    default: () => []
  },
  filters: {
    type: Object,
    default: () => ({
      channel: '',
      search: '',
      startDate: '',
      endDate: '',
      filterRead: false,
      filterLike: false,
      filterTrash: false
    })
  }
})

const emit = defineEmits(['applyFilters', 'update:filters'])

// Local copy of filters for v-model
const localFilters = ref({ ...props.filters })

// Watch for changes and emit update
watch(localFilters, (newFilters) => {
  emit('update:filters', newFilters)
}, { deep: true })

// Handle apply filters
const handleApplyFilters = () => {
  emit('applyFilters')
}
</script>

<style scoped>
.filters {
  background: var(--card);
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.filter-row {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.filter-group {
  flex: 1;
  min-width: 200px;
}

.filter-group > label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.filter-group label:has(input[type="checkbox"]) {
  display: flex;
  align-items: center;
  margin-bottom: 0;
  font-weight: normal;
}

select,
input[type="text"],
input[type="date"] {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 5px;
  font-size: 14px;
}

input[type="checkbox"] {
  margin-right: 8px;
  cursor: pointer;
  width: auto;
}

button {
  background: var(--primary);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

button:hover {
  background: var(--primary-dark);
}

@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
  }
}
</style>