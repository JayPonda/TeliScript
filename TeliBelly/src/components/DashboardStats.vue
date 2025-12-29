<template>
  <div class="stats">
    <div class="stat-card">
      <div class="stat-label">Total Messages</div>
      <div class="stat-value">{{ totalMessages.toLocaleString() }}</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Channels</div>
      <div class="stat-value">{{ totalChannels }}</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Date Range</div>
      <div class="stat-value">{{ dateRange }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  totalMessages: {
    type: Number,
    default: 0
  },
  totalChannels: {
    type: Number,
    default: 0
  },
  dateRange: {
    type: String,
    default: 'N/A'
  }
})
</script>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--card);
  padding: 20px;
  border-radius: 10px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--primary);
  margin: 10px 0;
}

.stat-label {
  color: var(--secondary);
  font-size: 14px;
}
</style>