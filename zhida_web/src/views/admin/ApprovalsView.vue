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
              <button type="button" class="action-btn" @click="openPreview(d)">预览</button>
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

    <div v-if="showPreview" class="modal-mask" @click.self="showPreview = false">
      <div class="modal wide">
        <h3>{{ previewTitle || '文档预览' }}</h3>
        <p v-if="previewLoading" class="muted">加载中...</p>
        <p v-else-if="previewError" class="error">{{ previewError }}</p>
        <div v-else class="doc-body" v-html="previewHtml"></div>
        <div class="modal-actions">
          <button type="button" class="link-btn" @click="showPreview = false">关闭</button>
          <button
            type="button"
            class="action-btn"
            :disabled="!previewDoc || busyId === previewDoc.id"
            @click="onApprove(previewDoc)"
          >
            通过
          </button>
          <button
            type="button"
            class="action-btn danger"
            :disabled="!previewDoc || busyId === previewDoc.id"
            @click="onReject(previewDoc)"
          >
            拒绝
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listPendingDocs, approveDoc, rejectDoc } from '../../api/approvals'
import { getDocument } from '../../api/documents'
import { renderDocContent } from '../../utils/renderContent'

const docs = ref([])
const loading = ref(false)
const busyId = ref(null)
const error = ref('')
const okMsg = ref('')

const showPreview = ref(false)
const previewDoc = ref(null)
const previewTitle = ref('')
const previewHtml = ref('')
const previewLoading = ref(false)
const previewError = ref('')

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

async function openPreview(d) {
  previewDoc.value = d
  previewTitle.value = d.title || '文档预览'
  previewError.value = ''
  previewHtml.value = ''
  showPreview.value = true
  previewLoading.value = true
  try {
    const detail = await getDocument(d.id)
    previewTitle.value = detail.title || previewTitle.value
    previewHtml.value = renderDocContent(detail.content)
  } catch (e) {
    previewError.value = e.detail || e.message || '加载预览失败'
  } finally {
    previewLoading.value = false
  }
}

function closePreviewIfCurrent(d) {
  if (showPreview.value && previewDoc.value?.id === d.id) {
    showPreview.value = false
    previewDoc.value = null
  }
}

async function onApprove(d) {
  if (!d) return
  busyId.value = d.id
  okMsg.value = ''
  error.value = ''
  try {
    await approveDoc(d.id)
    okMsg.value = `已通过「${d.title}」`
    closePreviewIfCurrent(d)
    await refresh()
  } catch (e) {
    error.value = e.detail || e.message || '操作失败'
  } finally {
    busyId.value = null
  }
}

async function onReject(d) {
  if (!d) return
  if (!confirm(`确认拒绝「${d.title}」？`)) return
  busyId.value = d.id
  okMsg.value = ''
  error.value = ''
  try {
    await rejectDoc(d.id)
    okMsg.value = `已拒绝「${d.title}」`
    closePreviewIfCurrent(d)
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

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 20px;
}
.modal {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  box-shadow: var(--shadow-lg);
  max-height: 90vh;
  overflow: auto;
}
.modal.wide { max-width: 720px; }
.modal h3 { margin: 0 0 12px; }
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
.link-btn {
  border: none;
  background: transparent;
  color: var(--color-primary);
  cursor: pointer;
}
.doc-body {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  background: #f8fafc;
  white-space: pre-wrap;
  line-height: 1.6;
}
.doc-body :deep(p) { margin: 0.4em 0; }
</style>
