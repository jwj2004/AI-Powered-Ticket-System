<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>待审批文档</h2>
        <p class="muted">未审批文档 · 通过或拒绝</p>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="okMsg" class="ok">{{ okMsg }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>标题</th>
            <th>提交人</th>
            <th>提交时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="4" class="empty">加载中...</td>
          </tr>
          <tr v-else-if="!docs.length">
            <td colspan="4" class="empty">暂无待审批文档</td>
          </tr>
          <tr v-for="d in docs" :key="d.id">
            <td>{{ d.title }}</td>
            <td>{{ d.submitter }}</td>
            <td>{{ formatTime(d.submitted_at) }}</td>
            <td class="ops">
              <button type="button" class="action-btn" :disabled="busyId === d.id" @click="onApprove(d)">
                通过
              </button>
              <button type="button" class="action-btn danger" :disabled="busyId === d.id" @click="onReject(d)">
                拒绝
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listPendingDocs, approveDoc, rejectDoc } from '../../api/approvals'

const docs = ref([])
const loading = ref(false)
const busyId = ref(null)
const error = ref('')
const okMsg = ref('')

function formatTime(iso) {
  if (!iso) return ''
  return String(iso).replace('T', ' ').slice(0, 16)
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    docs.value = await listPendingDocs()
  } catch (e) {
    error.value = e.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function onApprove(d) {
  busyId.value = d.id
  okMsg.value = ''
  error.value = ''
  try {
    await approveDoc(d.id)
    okMsg.value = `已通过「${d.title}」`
    await refresh()
  } catch (e) {
    error.value = e.detail || e.message || '操作失败'
  } finally {
    busyId.value = null
  }
}

async function onReject(d) {
  if (!confirm(`确认拒绝「${d.title}」？`)) return
  busyId.value = d.id
  okMsg.value = ''
  error.value = ''
  try {
    await rejectDoc(d.id)
    okMsg.value = `已拒绝「${d.title}」`
    await refresh()
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
.table-wrap { overflow: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td {
  border-bottom: 1px solid var(--color-border);
  padding: 12px 10px;
  text-align: left;
}
th { color: #64748b; font-weight: 600; background: #f8fafc; }
tbody tr:hover { background: #eff6ff; }
.empty { text-align: center; color: #999; }
.ops { display: flex; gap: 6px; }
.action-btn {
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-primary);
  border-radius: var(--radius-sm);
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}
.action-btn.danger { color: var(--color-danger); }
.action-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.error { color: var(--color-danger); }
.ok { color: var(--color-success); }
</style>
