import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import KanbanView from '@/views/KanbanView.vue'
import MessageDetailView from '@/views/MessageDetailView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/kanban',
      name: 'kanban',
      component: KanbanView
    },
    {
      path: '/message/:id',
      name: 'message-detail',
      component: MessageDetailView
    }
  ],
})

export default router