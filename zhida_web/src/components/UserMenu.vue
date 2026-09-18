<template>
  <div ref="rootEl" class="user-menu">
    <button type="button" class="trigger" @click="toggle">
      <span class="name">{{ username }}</span>
      <span class="caret" aria-hidden="true">▾</span>
    </button>
    <div v-if="open" class="menu">
      <button type="button" class="item" @click="openPwd">修改密码</button>
    </div>

    <div v-if="showPwd" class="modal-mask" @click.self="closePwd">
      <div class="modal">
        <h3>修改密码</h3>
        <label class="label">旧密码</label>
        <input v-model="form.old_password" type="password" class="input" placeholder="请输入旧密码" />
        <label class="label">新密码</label>
        <input v-model="form.new_password" type="password" class="input" placeholder="至少 6 位" />
        <label class="label">确认新密码</label>
        <input v-model="form.confirm" type="password" class="input" placeholder="再次输入新密码" />
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="okMsg" class="ok">{{ okMsg }}</p>
        <div class="modal-actions">
          <button type="button" class="link-btn" @click="closePwd">取消</button>
          <button type="button" class="btn" :disabled="saving" @click="submit">
            {{ saving ? '提交中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { getUsername } from '../api/authStorage'
import { changePassword } from '../api/auth'

const username = getUsername() || '用户'
const rootEl = ref(null)
const open = ref(false)
const showPwd = ref(false)
const saving = ref(false)
const error = ref('')
const okMsg = ref('')
const form = reactive({
  old_password: '',
  new_password: '',
  confirm: '',
})

function toggle() {
  open.value = !open.value
}

function onDocClick(e) {
  if (!rootEl.value?.contains(e.target)) open.value = false
}

function openPwd() {
  open.value = false
  form.old_password = ''
  form.new_password = ''
  form.confirm = ''
  error.value = ''
  okMsg.value = ''
  showPwd.value = true
}

function closePwd() {
  showPwd.value = false
}

async function submit() {
  error.value = ''
  okMsg.value = ''
  if (!form.old_password || !form.new_password || !form.confirm) {
    error.value = '请填写旧密码、新密码和确认新密码'
    return
  }
  if (form.new_password !== form.confirm) {
    error.value = '两次输入的新密码不一致'
    return
  }
  saving.value = true
  try {
    await changePassword({
      old_password: form.old_password,
      new_password: form.new_password,
    })
    okMsg.value = '密码已修改'
    setTimeout(closePwd, 800)
  } catch (e) {
    error.value = e.detail || e.message || '修改失败'
  } finally {
    saving.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<style scoped>
.user-menu {
  position: relative;
}
.trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--color-border);
  background: #fff;
  color: #374151;
  border-radius: var(--radius-sm);
  padding: 7px 12px;
  cursor: pointer;
}
.trigger:hover {
  border-color: var(--color-primary-muted);
  color: var(--color-primary);
}
.name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
}
.caret { font-size: 10px; color: #94a3b8; }
.menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  min-width: 140px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-lg);
  z-index: 40;
  padding: 4px;
}
.item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  color: #374151;
}
.item:hover { background: var(--color-primary-soft); color: var(--color-primary); }

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 80;
  padding: 20px;
}
.modal {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  box-shadow: var(--shadow-lg);
}
.modal h3 { margin: 0 0 8px; }
.label {
  display: block;
  font-weight: 600;
  margin: 12px 0 6px;
  font-size: 13px;
}
.input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}
.link-btn {
  border: none;
  background: transparent;
  color: var(--color-primary);
  cursor: pointer;
}
.btn {
  border: none;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-sm);
  padding: 9px 16px;
  font-weight: 600;
  cursor: pointer;
}
.btn:disabled { background: var(--color-primary-muted); cursor: not-allowed; }
.error { color: var(--color-danger); margin: 10px 0 0; font-size: 13px; }
.ok { color: var(--color-success); margin: 10px 0 0; font-size: 13px; }
</style>
