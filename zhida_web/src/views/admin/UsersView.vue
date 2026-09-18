<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>用户管理</h2>
        <p class="muted">注册审核 · 同意 / 拒绝 / 升级管理员</p>
      </div>
    </div>

    <div class="tabs">
      <button
        type="button"
        class="tab"
        :class="{ active: tab === 'pending' }"
        @click="switchTab('pending')"
      >
        待审核
        <span v-if="pending.length" class="count">{{ pending.length }}</span>
      </button>
      <button
        type="button"
        class="tab"
        :class="{ active: tab === 'active' }"
        @click="switchTab('active')"
      >
        已通过
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="okMsg" class="ok">{{ okMsg }}</p>

    <!-- 待审核 -->
    <div v-if="tab === 'pending'" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>用户名</th>
            <th>申请角色</th>
            <th>申请时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="4" class="empty">加载中...</td>
          </tr>
          <tr v-else-if="!pending.length">
            <td colspan="4" class="empty">暂无待审核用户</td>
          </tr>
          <tr v-for="u in pending" :key="u.id">
            <td>{{ u.username }}</td>
            <td>{{ u.role }}</td>
            <td>{{ formatTime(u.created_at) }}</td>
            <td class="ops">
              <button
                type="button"
                class="action-btn"
                :disabled="busyId === u.id"
                @click="onApprove(u)"
              >
                ✓ 同意
              </button>
              <button
                type="button"
                class="action-btn danger"
                :disabled="busyId === u.id"
                @click="onReject(u)"
              >
                ✕ 拒绝
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 已通过 -->
    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>用户名</th>
            <th>角色</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="4" class="empty">加载中...</td>
          </tr>
          <tr v-else-if="!active.length">
            <td colspan="4" class="empty">暂无用户</td>
          </tr>
          <tr v-for="u in active" :key="u.id">
            <td>{{ u.username }}</td>
            <td>{{ u.role }}</td>
            <td>
              <span class="status" :class="u.status === 'disabled' ? 'disabled' : 'active'">
                {{ u.status === 'disabled' ? '已禁用' : (u.status || 'active') }}
              </span>
            </td>
            <td class="ops">
              <button
                v-if="u.role !== 'admin' && u.username !== me"
                type="button"
                class="action-btn"
                :disabled="busyId === u.id"
                @click="onMakeAdmin(u)"
              >
                ↑ 升级为管理员
              </button>
              <button
                v-if="u.username !== me && u.status !== 'disabled'"
                type="button"
                class="action-btn danger"
                :disabled="busyId === u.id"
                @click="onDisable(u)"
              >
                禁用
              </button>
              <span v-if="u.status === 'disabled'" class="muted-inline">已禁用</span>
              <span v-else-if="u.username === me" class="muted-inline">当前账号</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getUsername } from '../../api/authStorage'
import {
  listPendingUsers,
  listActiveUsers,
  approveUser,
  rejectUser,
  makeAdmin,
  disableUser,
} from '../../api/users'

const me = getUsername() || ''
const tab = ref('pending')
const pending = ref([])
const active = ref([])
const loading = ref(false)
const error = ref('')
const okMsg = ref('')
const busyId = ref(null)

function formatTime(iso) {
  if (!iso) return ''
  return String(iso).replace('T', ' ').slice(0, 16)
}

async function loadPending() {
  pending.value = await listPendingUsers()
}

async function loadActive() {
  active.value = await listActiveUsers()
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    if (tab.value === 'pending') await loadPending()
    else await loadActive()
  } catch (e) {
    error.value = e.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function switchTab(name) {
  tab.value = name
  okMsg.value = ''
  error.value = ''
  refresh()
}

async function onApprove(u) {
  busyId.value = u.id
  error.value = ''
  okMsg.value = ''
  try {
    await approveUser(u.id)
    okMsg.value = `已同意 ${u.username}`
    await loadPending()
  } catch (e) {
    error.value = e.detail || e.message || '操作失败'
  } finally {
    busyId.value = null
  }
}

async function onReject(u) {
  if (!confirm(`确认拒绝「${u.username}」的注册申请？`)) return
  busyId.value = u.id
  error.value = ''
  okMsg.value = ''
  try {
    await rejectUser(u.id)
    okMsg.value = `已拒绝 ${u.username}`
    await loadPending()
  } catch (e) {
    error.value = e.detail || e.message || '操作失败'
  } finally {
    busyId.value = null
  }
}

async function onMakeAdmin(u) {
  if (!confirm(`确认将「${u.username}」升级为管理员？`)) return
  busyId.value = u.id
  error.value = ''
  okMsg.value = ''
  try {
    await makeAdmin(u.id)
    okMsg.value = `${u.username} 已升级为管理员`
    await loadActive()
  } catch (e) {
    error.value = e.detail || e.message || '操作失败'
  } finally {
    busyId.value = null
  }
}

async function onDisable(u) {
  if (u.username === me) {
    error.value = '不能禁用当前登录账号'
    return
  }
  if (!confirm(`确认禁用「${u.username}」？`)) return
  busyId.value = u.id
  error.value = ''
  okMsg.value = ''
  try {
    await disableUser(u.id)
    okMsg.value = `已禁用 ${u.username}`
    await loadActive()
  } catch (e) {
    error.value = e.detail || e.message || '操作失败'
  } finally {
    busyId.value = null
  }
}

onMounted(refresh)
</script>

<style scoped>
.panel {
  background: var(--color-surface);
  border-radius: 12px;
  padding: 20px 22px;
  box-shadow: var(--shadow);
  border: 1px solid var(--color-border);
}
.toolbar { margin-bottom: 16px; }
h2 { margin: 0 0 4px; font-size: 18px; }
.muted { color: var(--color-text-secondary); margin: 0; font-size: 13px; }
.muted-inline { color: #9ca3af; font-size: 13px; }

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0;
}
.tab {
  border: none;
  background: transparent;
  padding: 10px 14px;
  cursor: pointer;
  color: #64748b;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}
.count {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 11px;
  line-height: 18px;
  text-align: center;
}

.table-wrap { overflow: auto; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th, td {
  border-bottom: 1px solid var(--color-border);
  padding: 12px 10px;
  text-align: left;
}
th { color: #64748b; font-weight: 600; background: #f8fafc; }
tbody tr:hover { background: #eff6ff; }
.empty { text-align: center; color: #999; }
.ops {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-primary);
  border-radius: var(--radius-sm);
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}
.action-btn:hover:not(:disabled) {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-muted);
}
.action-btn.danger { color: var(--color-danger); }
.action-btn.danger:hover:not(:disabled) {
  background: #fef2f2;
  border-color: #fecaca;
}
.action-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 12px;
}
.status.active { background: #ecfdf5; color: var(--color-success); }
.status.disabled { background: #fef2f2; color: var(--color-danger); }

.error { color: var(--color-danger); }
.ok { color: var(--color-success); }
</style>
