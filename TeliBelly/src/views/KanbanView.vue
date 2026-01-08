<template>
  <div class="kanban-view">
    <KanbanBoard />
  </div>
</template>

<script>
import KanbanBoard from '@/components/KanbanBoard.vue';

export default {
  name: 'KanbanView',
  components: {
    KanbanBoard,
  },
};
</script>

<style scoped>
.kanban-view {
  padding: 20px;
}
</style>
