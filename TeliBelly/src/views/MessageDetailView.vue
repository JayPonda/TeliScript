<template>
  <div class="message-detail-view" v-if="message">
    <h1>Message from {{ message.channel_name }}</h1>
    <p><strong>Sender:</strong> {{ message.sender_name }}</p>
    <p><strong>Date:</strong> {{ message.datetime_local }}</p>
    <hr>
    <p>{{ message.text_translated }}</p>
  </div>
  <div v-else-if="loading">
    <p>Loading message...</p>
  </div>
  <div v-else>
    <p>Message not found.</p>
  </div>
</template>

<script>
import { useMessagesStore } from '@/stores/messages';
import { mapState, mapActions } from 'pinia';

export default {
  name: 'MessageDetailView',
  computed: {
    ...mapState(useMessagesStore, ['allMessages', 'loading']),
    message() {
      const messageId = parseInt(this.$route.params.id);
      return this.allMessages.find(m => m.id === messageId);
    }
  },
  async created() {
    if (this.allMessages.length === 0) {
      await this.fetchAllMessages();
    }
  },
  methods: {
    ...mapActions(useMessagesStore, ['fetchAllMessages']),
  }
};
</script>

<style scoped>
.message-detail-view {
  padding: 20px;
}
</style>
