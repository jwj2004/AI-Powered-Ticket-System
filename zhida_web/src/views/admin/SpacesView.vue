<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>空间管理</h2>
        <p class="muted">查看、新增、删除文档空间（mock）</p>
      </div>
    </div>

    <form class="create" @submit.prevent="onCreate">
      <input v-model="form.name" class="input" placeholder="空间名称" />
      <input v-model="form.description" class="input grow" placeholder="空间描述" />
      <button type="submit" class="btn" :disabled="saving">{{ saving ? '提交中...' : '新增空间' }}</button>
    </form>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="okMsg" class="ok">{{ okMsg }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>名称</th>
            <th>描述</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="3" class="empty">加载中...</td>
          </tr>
          <tr v-else-if="!spaces.length">
            <td colspan="3" class="empty">暂无空间</td>
          </tr>
          <tr v-for="s in spaces" :key="s.id">
            <td>{{ s.name }}</td>
            <td>{{ s.description || '—' }}</td>
            <td>
              <button type="button" class="action-btn danger" :disabled="busyId === s.id" @click="onDelete(s)">
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { listManagedSpaces, createSpace, deleteSpace } from '../../api/spaces'

const spaces = ref([])
const loading = ref(false)
const saving = ref(false)
const busyId = ref(null)
const error = ref('')
const okMsg = ref('')
const form = reactive({ name: '', description: '' })

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    spaces.value = await listManagedSpaces()
  } catch (e) {
    error.value = e.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  error.value = ''
  okMsg.value = ''
  saving.value = true
  try {
    await createSpace({ name: form.name, description: form.description })
    form.name = ''
    form.description = ''
    okMsg.value = '已新增空间'
    await refresh()
  } catch (e) {
    error.value = e.detail || e.message || '新增失败'
  } finally {
    saving.value = false
  }
}

async function onDelete(s) {
  if (!confirm(`确认删除空间「${s.name}」？`)) return
  busyId.value = s.id
  error.value = ''
  okMsg.value = ''
  try {
    await deleteSpace(s.id)
    okMsg.value = `已删除 ${s.name}`
    await refresh()
  } catch (e) {
    error.value = e.detail || e.message || '删除失败'
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
.create {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.input {
  padding: 9px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  min-width: 160px;
}
.input.grow { flex: 1; min-width: 220px; }
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
.action-btn {
  border: 1px solid var(--color-border);
  background: #fff;
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
