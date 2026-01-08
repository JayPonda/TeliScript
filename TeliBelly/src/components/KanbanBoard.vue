<template>
  <div class="kanban-board">
    <h2>Kanban Board</h2>
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else class="board">
      <div v-for="column in columns" :key="column.name" class="column">
        <h3>{{ column.name }}</h3>
        <div class="cards">
          <template v-for="item in column.items" :key="item.type === 'card' ? item.id : item.date">
            <div v-if="item.type === 'date_separator'" class="date-separator">
              <span>{{ item.date }}</span>
            </div>
            <div v-else class="card" :class="{ liked: item.like, trashed: item.trashed_at }">
              <p>{{ item.text_translated ? item.text_translated.substring(0, 50) + '...' : '' }}</p>
              <router-link :to="`/message/${item.id}`">Read more</router-link>
              <div class="card-actions">
                <button @click="toggleLike(item)">{{ item.like ? 'Unlike' : 'Like' }}</button>
                <button @click="toggleRead(item)">{{ item.read ? 'Unread' : 'Read' }}</button>
                <button @click="toggleTrash(item)">{{ item.trashed_at ? 'Restore' : 'Trash' }}</button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useMessagesStore } from '@/stores/messages';
import { mapState, mapActions } from 'pinia';

export default {
  name: 'KanbanBoard',
  computed: {
    ...mapState(useMessagesStore, ['allMessages', 'loading']),
    columns() {
      const groupMessagesByDate = (messages) => {
        const grouped = [];
        let lastDate = null;

        // Sort messages by date to ensure correct grouping
        messages.sort((a, b) => new Date(b.datetime_local) - new Date(a.datetime_local));

        for (const message of messages) {
          const messageDate = message.datetime_local.split(' ')[0]; // Get YYYY-MM-DD
          if (messageDate !== lastDate) {
            grouped.push({ type: 'date_separator', date: messageDate });
            lastDate = messageDate;
          }
          grouped.push({ type: 'card', ...message });
        }
        return grouped;
      };

      const channels = [...new Set(this.allMessages.map(m => m.channel_name))];
      const columns = channels.map(channel => ({
        name: channel,
        items: groupMessagesByDate(this.allMessages.filter(message => message.channel_name === channel && !message.read)),
      }));

      // Add 'Read' column
      columns.push({
        name: 'Read',
        items: groupMessagesByDate(this.allMessages.filter(message => message.read)),
      });

      return columns;
    }
  },
  async created() {
    await this.fetchAllMessages();
  },
  methods: {
    ...mapActions(useMessagesStore, ['fetchAllMessages']),
    async toggleRead(card) {
      try {
        const response = await fetch(`/api/messages/${card.id}/read`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        const result = await response.json();
        if (result.success) {
          card.read = !card.read;
        } else {
          alert('Error: ' + result.error);
        }
      } catch (error) {
        alert('Error marking as read: ' + error.message);
      }
    },
    async toggleLike(card) {
      try {
        const response = await fetch(`/api/messages/${card.id}/like`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        const result = await response.json();
        if (result.success) {
          card.like = result.data.liked;
        } else {
          alert('Error: ' + result.error);
        }
      } catch (error) {
        alert('Error toggling like: ' + error.message);
      }
    },
    async toggleTrash(card) {
      try {
        const response = await fetch(`/api/messages/${card.id}/trash`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        const result = await response.json();
        if (result.success) {
          if (result.data.action === 'trashed') {
            card.trashed_at = new Date().toISOString();
          } else {
            card.trashed_at = null;
          }
        } else {
          alert('Error: ' + result.error);
        }
      } catch (error) {
        alert('Error toggling trash: ' + error.message);
      }
    }
  },
};
</script>

<style scoped>
.kanban-board {
  padding: 20px;
}

.board {
  display: flex;
  gap: 20px;
  overflow-x: auto;
}

.column {
  background-color: #f4f4f4;
  border-radius: 5px;
  padding: 10px;
  width: 300px;
  flex-shrink: 0;
}

.cards {
  margin-top: 10px;
}

.card {
  background-color: #fff;
  border-radius: 5px;
  padding: 10px;
  margin-bottom: 10px;
}

.card.liked {
  background-color: #fff1f2;
}

.card.trashed {
  opacity: 0.5;
}

.card-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
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
