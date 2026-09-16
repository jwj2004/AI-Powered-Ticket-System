<template>
  <div class="login-page">
    <div class="card">
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
import { useRouter } from 'vue-router'
import { login } from '../api/auth'

const router = useRouter()
const username = ref('admin')
const password = ref('123456')
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  try {
    const data = await login(username.value.trim(), password.value)
    if (data.role === 'admin') {
      router.replace('/admin/documents')
    } else {
      router.replace('/chat')
    }
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
  background: #f0f2f5;
  font: 14px/1.6 -apple-system, "PingFang SC", sans-serif;
  padding: 24px;
}
.card {
  width: 100%;
  max-width: 360px;
  background: #fff;
  border-radius: 8px;
  padding: 28px 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
h1 {
  margin: 0;
  text-align: center;
  font-size: 24px;
}
.sub {
  text-align: center;
  color: #888;
  margin: 4px 0 20px;
}
.label {
  display: block;
  font-weight: 600;
  margin: 12px 0 6px;
}
.input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  box-sizing: border-box;
  font: inherit;
}
.btn {
  width: 100%;
  margin-top: 18px;
  padding: 10px;
  border: none;
  border-radius: 6px;
  background: #1a73e8;
  color: #fff;
  font: inherit;
  cursor: pointer;
}
.btn:disabled {
  background: #9bb8e8;
  cursor: not-allowed;
}
.error {
  color: #d93025;
  margin: 10px 0 0;
}
.hint {
  margin-top: 14px;
  font-size: 12px;
  color: #999;
}
</style>
