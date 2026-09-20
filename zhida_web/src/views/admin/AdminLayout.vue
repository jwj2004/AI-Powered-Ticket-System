<template>
  <div class="admin">
    <aside class="nav">
      <div class="brand">知答 · 管理后台</div>
      <p class="user">{{ username }}</p>
      <nav>
        <RouterLink to="/admin/documents">文档管理</RouterLink>
        <RouterLink to="/admin/approvals">待审批文档</RouterLink>
        <RouterLink to="/admin/spaces">空间管理</RouterLink>
        <RouterLink to="/admin/gaps">知识缺口</RouterLink>
        <RouterLink to="/admin/dashboard">数据看板</RouterLink>
        <RouterLink to="/admin/users" class="nav-users">
          用户管理
          <span v-if="isAdmin && pendingUserCount > 0" class="pending-badge">{{ pendingUserCount }}</span>
        </RouterLink>
        <RouterLink to="/admin/logs">操作日志</RouterLink>
        <RouterLink to="/admin/pending-faq">待确认 FAQ</RouterLink>
        <RouterLink to="/admin/faq">新手指南</RouterLink>
      </nav>
      <div class="bottom">
        <RouterLink class="to-chat" to="/chat">去问答页</RouterLink>
        <button class="logout" @click="onLogout">退出</button>
      </div>
    </aside>
    <main class="content">
      <div class="topbar">
        <UserMenu />
      </div>
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { getUsername, getRole, clearAuth } from '../../api/authStorage'
import { pendingUserCount } from '../../api/pendingBadge'
import UserMenu from '../../components/UserMenu.vue'

const router = useRouter()
const username = getUsername() || 'admin'
const isAdmin = getRole() === 'admin'

function onLogout() {
  clearAuth()
  router.replace('/login')
}
</script>

<style scoped>
.admin {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}
.nav {
  width: 228px;
  background: var(--color-sidebar, #1e293b);
  color: #fff;
  padding: 24px 14px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.brand {
  font-weight: 700;
  font-size: 15px;
  padding: 0 10px;
  letter-spacing: 0.02em;
}
.user {
  color: #94a3b8;
  font-size: 12px;
  margin: 8px 10px 22px;
}
nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}
nav a {
  color: #cbd5e1;
  text-decoration: none;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  transition: background 0.15s, color 0.15s;
}
nav a:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}
nav a.router-link-active {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}
.nav-users {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.pending-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-danger, #dc2626);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
  box-shadow: none;
}
.bottom {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
}
.to-chat {
  color: var(--color-primary-muted);
  text-decoration: none;
  font-size: 13px;
  padding: 0 10px;
}
.to-chat:hover {
  color: #fff;
}
.logout {
  border: none;
  background: #0f172a;
  color: #e2e8f0;
  padding: 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
}
.logout:hover {
  background: #334155;
}
.content {
  flex: 1;
  padding: 16px 24px 24px;
  min-width: 0;
}
.topbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
</style>
