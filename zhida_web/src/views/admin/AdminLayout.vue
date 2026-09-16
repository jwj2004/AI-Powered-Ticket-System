<template>
  <div class="admin">
    <aside class="nav">
      <div class="brand">知答 · 管理后台</div>
      <p class="user">{{ username }}</p>
      <nav>
        <RouterLink to="/admin/documents">文档管理</RouterLink>
        <RouterLink to="/admin/gaps">知识缺口</RouterLink>
        <RouterLink to="/admin/dashboard">数据看板</RouterLink>
        <RouterLink to="/admin/faq">新手指南</RouterLink>
      </nav>
      <div class="bottom">
        <RouterLink to="/chat">去问答页</RouterLink>
        <button class="logout" @click="onLogout">退出</button>
      </div>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { getUsername, clearAuth } from '../../api/authStorage'

const router = useRouter()
const username = getUsername() || 'admin'

function onLogout() {
  clearAuth()
  router.replace('/login')
}
</script>

<style scoped>
.admin {
  display: flex;
  min-height: 100vh;
  font: 14px/1.6 -apple-system, "PingFang SC", sans-serif;
  background: #f5f6f8;
}
.nav {
  width: 220px;
  background: #1f2937;
  color: #fff;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
.brand { font-weight: 700; font-size: 16px; }
.user { color: #9ca3af; font-size: 12px; margin: 6px 0 20px; }
nav { display: flex; flex-direction: column; gap: 6px; flex: 1; }
nav a {
  color: #e5e7eb;
  text-decoration: none;
  padding: 8px 10px;
  border-radius: 6px;
}
nav a.router-link-active,
nav a:hover {
  background: #374151;
  color: #fff;
}
.bottom { display: flex; flex-direction: column; gap: 8px; }
.bottom a {
  color: #93c5fd;
  text-decoration: none;
  font-size: 13px;
}
.logout {
  border: none;
  background: #4b5563;
  color: #fff;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
}
.content {
  flex: 1;
  padding: 24px;
  box-sizing: border-box;
}
</style>
