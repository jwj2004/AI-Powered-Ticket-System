<template>
  <div class="login-page">
    <div class="card">
      <div class="logo">知</div>
      <h1>知答</h1>
      <p class="sub">企业内部知识库问答</p>

      <label class="label">用户名</label>
      <input v-model="username" class="input" placeholder="请输入用户名" @keyup.enter="onSubmit" />

      <label class="label">密码</label>
      <input
        v-model="password"
        type="password"
        class="input"
        placeholder="请输入密码"
        @keyup.enter="onSubmit"
      />

      <p v-if="tip" class="tip">{{ tip }}</p>
      <p v-if="error" class="error">{{ error }}</p>

      <button class="btn" :disabled="loading" @click="onSubmit">
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <p class="reg">
        没有账号？
        <RouterLink to="/register">申请注册</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../api/auth'
import { loadPendingUserCount } from '../api/pendingBadge'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const tip = ref('')

onMounted(() => {
  const q = route.query.tip
  if (typeof q === 'string' && q) tip.value = q
})

function resolveLanding(role) {
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect.startsWith('/')) {
    return redirect
  }
  return role === 'admin' ? '/admin/documents' : '/chat'
}

async function onSubmit() {
  error.value = ''
  tip.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  try {
    const data = await login(username.value.trim(), password.value)
    if (data.role === 'admin') {
      try {
        await loadPendingUserCount()
      } catch {
        /* 红点失败不挡住登录 */
      }
    }
    router.replace(resolveLanding(data.role))
  } catch (e) {
    const detail = e.detail || e.message || '登录失败'
    // 待审核 / 拒绝：用 tip 样式区分；其它错误走 error
    if (detail.includes('待审核') || detail.includes('已被拒绝') || detail.includes('拒绝')) {
      tip.value = detail
      error.value = ''
    } else {
      error.value = detail
    }
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
  padding: 24px;
  background:
    radial-gradient(ellipse 80% 60% at 20% 10%, rgba(37, 99, 235, 0.28), transparent 55%),
    radial-gradient(ellipse 70% 50% at 90% 80%, rgba(59, 130, 246, 0.2), transparent 50%),
    linear-gradient(160deg, #eff6ff 0%, #f8fafc 45%, #e2e8f0 100%);
}
.card {
  width: 100%;
  max-width: 400px;
  background: var(--color-surface);
  border-radius: 20px;
  padding: 40px 36px 30px;
  box-shadow: var(--shadow-lg);
  border: 1px solid rgba(255, 255, 255, 0.8);
}
.logo {
  width: 56px;
  height: 56px;
  margin: 0 auto 14px;
  border-radius: 16px;
  background: linear-gradient(145deg, #2563eb, #3b82f6);
  color: #fff;
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.02em;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
}
h1 {
  margin: 0;
  text-align: center;
  font-size: 28px;
  color: var(--color-text);
  font-weight: 700;
}
.sub {
  text-align: center;
  color: var(--color-text-secondary);
  margin: 6px 0 26px;
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
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18);
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
  transition: background 0.15s, box-shadow 0.15s;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}
.btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}
.btn:disabled {
  background: var(--color-primary-muted);
  cursor: not-allowed;
  box-shadow: none;
}
.error {
  color: var(--color-danger);
  margin: 10px 0 0;
  font-size: 13px;
}
.tip {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--color-warn);
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius-sm);
  padding: 8px 10px;
}
.reg {
  margin-top: 14px;
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}
.reg a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}
.reg a:hover {
  text-decoration: underline;
}
</style>
