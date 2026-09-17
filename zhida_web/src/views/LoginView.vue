<template>
  <div class="login-page">
    <div class="card">
      <div class="logo">知</div>
      <h1>知答</h1>
      <p class="sub">企业内部知识库问答</p>

      <label class="label">用户名</label>
      <input v-model="username" class="input" placeholder="admin / zhangsan / lisi" @keyup.enter="onSubmit" />

      <label class="label">密码</label>
      <input
        v-model="password"
        type="password"
        class="input"
        placeholder="123456"
        @keyup.enter="onSubmit"
      />

      <p v-if="error" class="error">{{ error }}</p>

      <button class="btn" :disabled="loading" @click="onSubmit">
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <p class="hint">mock：admin / zhangsan(ops) / lisi(newbie)，密码均为 123456</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../api/auth'

const router = useRouter()
const route = useRoute()
const username = ref('admin')
const password = ref('123456')
const loading = ref(false)
const error = ref('')

function resolveLanding(role) {
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect.startsWith('/')) {
    return redirect
  }
  return role === 'admin' ? '/admin/documents' : '/chat'
}

async function onSubmit() {
  error.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  try {
    const data = await login(username.value.trim(), password.value)
    router.replace(resolveLanding(data.role))
  } catch (e) {
    error.value = e.detail || e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  padding: 24px;
}
.card {
  width: 100%;
  max-width: 380px;
  background: var(--color-surface);
  border-radius: 16px;
  padding: 36px 32px 28px;
  box-shadow: var(--shadow-lg);
}
.logo {
  width: 52px;
  height: 52px;
  margin: 0 auto 12px;
  border-radius: 14px;
  background: linear-gradient(145deg, #1e40af, #3b82f6);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.02em;
}
h1 {
  margin: 0;
  text-align: center;
  font-size: 26px;
  color: var(--color-text);
  font-weight: 700;
}
.sub {
  text-align: center;
  color: var(--color-text-secondary);
  margin: 6px 0 24px;
  font-size: 13px;
}
.label {
  display: block;
  font-weight: 600;
  font-size: 13px;
  margin: 14px 0 6px;
  color: #374151;
}
.input {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.15);
}
.btn {
  width: 100%;
  margin-top: 22px;
  padding: 12px;
  border: none;
  border-radius: var(--radius);
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}
.btn:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}
.error {
  color: var(--color-danger);
  margin: 10px 0 0;
  font-size: 13px;
}
.hint {
  margin-top: 16px;
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
  line-height: 1.5;
}
</style>
