import { createRouter, createWebHistory } from 'vue-router'
import { getToken, getRole } from '../api/authStorage'

import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ChatView from '../views/ChatView.vue'
import AdminLayout from '../views/admin/AdminLayout.vue'
import DocumentsView from '../views/admin/DocumentsView.vue'
import GapsView from '../views/admin/GapsView.vue'
import DashboardView from '../views/admin/DashboardView.vue'
import FaqView from '../views/admin/FaqView.vue'
import PendingFaqView from '../views/admin/PendingFaqView.vue'
import UsersView from '../views/admin/UsersView.vue'
import SpacesView from '../views/admin/SpacesView.vue'
import LogsView from '../views/admin/LogsView.vue'
import ApprovalsView from '../views/admin/ApprovalsView.vue'

/** 角色可访问路径：ops 仅问答；newbie 问答+FAQ；admin 全部 */
function canAccess(role, path) {
  if (role === 'admin') return true
  if (role === 'newbie') {
    return path === '/chat' || path === '/faq' || path.startsWith('/faq/')
  }
  if (role === 'ops') {
    return path === '/chat'
  }
  return false
}

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
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { public: true },
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
    },
    {
      path: '/faq',
      name: 'faq',
      component: FaqView,
      meta: { roles: ['admin', 'newbie'] },
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAdmin: true },
      redirect: '/admin/documents',
      children: [
        { path: 'documents', name: 'admin-documents', component: DocumentsView },
        { path: 'approvals', name: 'admin-approvals', component: ApprovalsView },
        { path: 'spaces', name: 'admin-spaces', component: SpacesView },
        { path: 'gaps', name: 'admin-gaps', component: GapsView },
        { path: 'dashboard', name: 'admin-dashboard', component: DashboardView },
        { path: 'pending-faq', name: 'admin-pending-faq', component: PendingFaqView },
        { path: 'faq', name: 'admin-faq', component: FaqView },
        { path: 'users', name: 'admin-users', component: UsersView },
        { path: 'logs', name: 'admin-logs', component: LogsView },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const token = getToken()
  const role = getRole()

  if (to.meta.public) {
    if (token && (to.path === '/login' || to.path === '/register')) {
      return role === 'admin' ? '/admin/documents' : '/chat'
    }
    return true
  }

  if (!token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // admin 专属后台
  if (to.meta.requiresAdmin || to.path.startsWith('/admin')) {
    if (role !== 'admin') {
      return '/chat'
    }
    return true
  }

  if (!canAccess(role, to.path)) {
    return '/chat'
  }

  return true
})

export default router
