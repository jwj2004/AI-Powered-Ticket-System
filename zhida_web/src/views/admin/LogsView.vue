<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>操作日志</h2>
        <p class="muted">上传 / 编辑 / 删除文档、处理缺口等</p>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>时间</th>
            <th>操作人</th>
            <th>动作</th>
            <th>详情</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="4" class="empty">加载中...</td>
          </tr>
          <tr v-else-if="!logs.length">
            <td colspan="4" class="empty">暂无日志</td>
          </tr>
          <tr v-for="row in logs" :key="row.id">
            <td>{{ formatTime(row.created_at) }}</td>
            <td>{{ row.operator }}</td>
            <td><span class="tag">{{ row.action }}</span></td>
            <td>{{ row.detail || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listLogs } from '../../api/logs'

const logs = ref([])
const loading = ref(false)
const error = ref('')

function formatTime(iso) {
  if (!iso) return ''
  return String(iso).replace('T', ' ').slice(0, 16)
}

onMounted(async () => {
  loading.value = true
  try {
    logs.value = await listLogs()
  } catch (e) {
    error.value = e.detail || e.message || '加载日志失败'
  } finally {
    loading.value = false
  }
})
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
.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 12px;
}
.error { color: var(--color-danger); }
</style>
