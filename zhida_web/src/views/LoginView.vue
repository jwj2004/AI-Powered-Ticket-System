<template>
  <div class="login-page">
    <section class="brand">
      <svg class="deco deco-a" viewBox="0 0 120 120" aria-hidden="true">
        <circle cx="60" cy="60" r="48" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="2" />
        <circle cx="60" cy="60" r="28" fill="rgba(255,255,255,0.12)" />
      </svg>
      <svg class="deco deco-b" viewBox="0 0 80 80" aria-hidden="true">
        <rect x="8" y="8" width="64" height="64" rx="16" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="2" />
      </svg>
      <div class="logo">知</div>
      <h1>知答</h1>
      <p class="slogan">知答・企业知识库智能问答</p>
    </section>
    <section class="form-side">
      <div class="card">
        <h2>登录</h2>
        <p class="sub">使用企业账号进入知识库</p>

        <label class="label">用户名</label>
        <div class="field">
          <svg class="field-ico" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="8" r="3.2" fill="none" stroke="currentColor" stroke-width="1.6" />
            <path d="M5 19c1.5-3 3.8-4.5 7-4.5S17.5 16 19 19" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
          </svg>
          <input v-model="username" class="input" placeholder="请输入用户名" @keyup.enter="onSubmit" />
        </div>

        <label class="label">密码</label>
        <div class="field">
          <svg class="field-ico" viewBox="0 0 24 24" aria-hidden="true">
            <rect x="6" y="11" width="12" height="9" rx="2" fill="none" stroke="currentColor" stroke-width="1.6" />
            <path d="M8 11V8a4 4 0 0 1 8 0v3" fill="none" stroke="currentColor" stroke-width="1.6" />
          </svg>
          <input
            v-model="password"
            type="password"
            class="input"
            placeholder="请输入密码"
            @keyup.enter="onSubmit"
          />
        </div>

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
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../api/auth'
import { loadPendingUserCount } from '../api/pendingBadge'
import { markGuidePending } from '../utils/userLocal'

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
    if (data.role === 'newbie') markGuidePending(data.username)
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
  background: #fff;
}
.brand {
  position: relative;
  flex: 1.1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding: 48px 36px;
  color: #fff;
  background: var(--gradient);
  overflow: hidden;
}
.deco { position: absolute; }
.deco-a { width: 220px; height: 220px; right: -20px; top: -30px; }
.deco-b { width: 120px; height: 120px; left: 40px; bottom: 48px; }
.logo {
  width: 72px;
  height: 72px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 20px;
}
.brand h1 { margin: 0; font-size: 40px; font-weight: 600; }
.slogan { margin: 10px 0 0; font-size: 18px; font-weight: 400; opacity: 0.92; }
.form-side {
  flex: 0.9;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
  background: var(--bg-gradient);
}
.card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 12px;
  padding: 36px 32px 28px;
  box-shadow: var(--shadow);
}
.card h2 { margin: 0; font-size: 24px; font-weight: 600; }
.sub { color: var(--color-text-secondary); margin: 6px 0 18px; font-size: 13px; font-weight: 400; }
.label { display: block; font-weight: 600; font-size: 13px; margin: 14px 0 6px; }
.field { position: relative; }
.field-ico {
  position: absolute;
  left: 12px;
  top: 50%;
  width: 18px;
  height: 18px;
  margin-top: -9px;
  color: #94a3b8;
}
.input {
  width: 100%;
  padding: 11px 14px 11px 40px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.18);
}
.btn {
  width: 100%;
  margin-top: 22px;
  padding: 12px;
  border: none;
  border-radius: 12px;
  background: var(--gradient);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.2s, box-shadow 0.2s, transform 0.15s;
  box-shadow: 0 8px 18px rgba(102, 126, 234, 0.35);
}
.btn:hover:not(:disabled) { filter: brightness(1.06); }
.btn:disabled { opacity: 0.65; cursor: not-allowed; box-shadow: none; }
.error { color: var(--color-danger); margin: 10px 0 0; font-size: 13px; }
.tip {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--color-warn);
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 12px;
  padding: 8px 10px;
}
.reg { margin-top: 16px; text-align: center; font-size: 13px; color: #64748b; }
.reg a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  margin-left: 4px;
}
.reg a:hover { color: #764ba2; }
@media (max-width: 720px) {
  .login-page { flex-direction: column; }
  .brand { padding: 40px 28px; min-height: 240px; }
  .brand h1 { font-size: 32px; }
}
</style>
