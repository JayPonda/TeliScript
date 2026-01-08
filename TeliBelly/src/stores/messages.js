import { defineStore } from 'pinia';

export const useMessagesStore = defineStore('messages', {
  state: () => ({
    allMessages: [],
    loading: false,
  }),
  actions: {
    async fetchAllMessages() {
      this.loading = true;
      try {
        this.allMessages = [];
        let offset = 0;
        const limit = 100;
        while (true) {
          const messagesResponse = await fetch(`/api/messages?limit=${limit}&offset=${offset}`);
          const messagesData = await messagesResponse.json();
          const messages = messagesData.data;
          this.allMessages = this.allMessages.concat(messages);
          if (messages.length < limit) {
            break;
          }
          offset += limit;
        }
      } catch (error) {
        console.error('Error fetching all messages:', error);
      } finally {
        this.loading = false;
      }
    },
  },
});
