import { createRouter, createWebHistory } from 'vue-router'
import { getToken, getRole } from '../api/authStorage'

import LoginView from '../views/LoginView.vue'
import ChatView from '../views/ChatView.vue'
import AdminLayout from '../views/admin/AdminLayout.vue'
import DocumentsView from '../views/admin/DocumentsView.vue'
import GapsView from '../views/admin/GapsView.vue'
import DashboardView from '../views/admin/DashboardView.vue'
import FaqView from '../views/admin/FaqView.vue'
import PendingFaqView from '../views/admin/PendingFaqView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/chat' },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAdmin: true },
      redirect: '/admin/documents',
      children: [
        { path: 'documents', name: 'admin-documents', component: DocumentsView },
        { path: 'gaps', name: 'admin-gaps', component: GapsView },
        { path: 'dashboard', name: 'admin-dashboard', component: DashboardView },
        { path: 'pending-faq', name: 'admin-pending-faq', component: PendingFaqView },
        { path: 'faq', name: 'admin-faq', component: FaqView },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const token = getToken()
  const role = getRole()

  if (to.meta.public) {
    if (token && to.path === '/login') {
      return role === 'admin' ? '/admin/documents' : '/chat'
    }
    return true
  }

  if (!token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin || to.path.startsWith('/admin')) {
    if (role !== 'admin') {
      return '/chat'
    }
  }

  return true
})

export default router
