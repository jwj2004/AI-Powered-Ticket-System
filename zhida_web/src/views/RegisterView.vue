<template>
  <div class="reg-page">
    <div class="card">
      <div class="logo">知</div>
      <h1>申请注册</h1>
      <p class="sub">提交后由管理员审核开通</p>

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

      <label class="label">确认密码</label>
      <input
        v-model="confirm"
        type="password"
        class="input"
        placeholder="再次输入密码"
        @keyup.enter="onSubmit"
      />

      <label class="label">申请角色</label>
      <select v-model="role" class="input select">
        <option value="ops">ops（客服/运维）</option>
        <option value="newbie">newbie（新人）</option>
      </select>

      <p v-if="error" class="error">{{ error }}</p>

      <button class="btn" :disabled="loading" @click="onSubmit">
        {{ loading ? '提交中...' : '提交申请' }}
      </button>

      <p class="foot">
        已有账号？
        <RouterLink to="/login">返回登录</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../api/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const confirm = ref('')
const role = ref('newbie')
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  const name = username.value.trim()
  if (!name || !password.value) {
    error.value = '请填写用户名和密码'
    return
  }
  if (password.value !== confirm.value) {
    error.value = '两次密码不一致'
    return
  }
  if (role.value !== 'ops' && role.value !== 'newbie') {
    error.value = '请选择角色'
    return
  }
  loading.value = true
  try {
    await register({
      username: name,
      password: password.value,
      role: role.value,
    })
    router.replace({
      path: '/login',
      query: { tip: '申请已提交，等待管理员审核' },
    })
  } catch (e) {
    error.value = e.detail || e.message || '提交失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.reg-page {
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
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
}
h1 {
  margin: 0;
  text-align: center;
  font-size: 26px;
  font-weight: 700;
}
.sub {
  text-align: center;
  color: var(--color-text-secondary);
  margin: 6px 0 22px;
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
.select {
  cursor: pointer;
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
.foot {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}
.foot a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}
.foot a:hover {
  text-decoration: underline;
}
</style>
