<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>文档管理</h2>
        <p class="muted">列表 / 上传 / 预览 / 版本历史 / 编辑</p>
      </div>
      <button type="button" class="btn" @click="openUpload">上传文档</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="okMsg" class="ok">{{ okMsg }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>标题</th>
            <th>所属空间</th>
            <th>版本</th>
            <th>更新时间</th>
            <th>引用次数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!docs.length">
            <td colspan="6" class="empty">暂无文档</td>
          </tr>
          <tr v-for="d in docs" :key="d.id" :class="{ stale: isStale(d.updated_at) }">
            <td>{{ d.title }}</td>
            <td>{{ d.space }}</td>
            <td>v{{ d.version }}</td>
            <td>{{ formatTime(d.updated_at) }}</td>
            <td>{{ d.citation_count ?? 0 }}</td>
            <td class="ops">
              <button type="button" class="action-btn" @click="openPreview(d)">
                <svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>
                预览
              </button>
              <button type="button" class="action-btn" @click="openVersions(d)">
                <svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 8v5l3 2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
                历史
              </button>
              <button type="button" class="action-btn" @click="openEdit(d)">
                <svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4l10-10-4-4L4 16v4z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>
                编辑
              </button>
              <button type="button" class="action-btn danger" @click="onDelete(d)">
                <svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 上传弹窗 -->
    <div v-if="showUpload" class="modal-mask" @click.self="showUpload = false">
      <div class="modal">
        <h3>上传文档</h3>
        <label class="label">选择文件</label>
        <input type="file" @change="onFileChange" />
        <label class="label">文档空间</label>
        <select v-model="uploadSpaceId" class="select">
          <option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
        <p v-if="uploadError" class="error">{{ uploadError }}</p>
        <div class="modal-actions">
          <button type="button" class="link-btn" @click="showUpload = false">取消</button>
          <button type="button" class="btn" :disabled="uploading" @click="submitUpload">
            {{ uploading ? '上传中...' : '确认上传' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 预览弹窗 -->
    <div v-if="showPreview" class="modal-mask" @click.self="showPreview = false">
      <div class="modal wide">
        <h3>{{ previewTitle || '文档预览' }}</h3>
        <p v-if="previewLoading" class="muted">加载中...</p>
        <p v-else-if="previewError" class="error">{{ previewError }}</p>
        <div v-else class="doc-body" v-html="previewHtml"></div>
        <div class="modal-actions">
          <button type="button" class="btn" @click="showPreview = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 版本历史弹窗 -->
    <div v-if="showVersions" class="modal-mask" @click.self="closeVersions">
      <div class="modal wide">
        <h3>历史版本 · {{ versionDocTitle }}</h3>
        <p v-if="versionLoading" class="muted">加载中...</p>
        <p v-else-if="versionError" class="error">{{ versionError }}</p>
        <div v-else class="version-layout">
          <ul class="version-list">
            <li v-if="!versions.length" class="muted">暂无版本记录</li>
            <li
              v-for="v in versions"
              :key="v.version"
              :class="{ active: selectedVersion === v.version }"
            >
              <button type="button" class="version-item" @click="selectVersion(v)">
                <span class="ver">v{{ v.version }}</span>
                <span class="when">{{ formatTime(v.created_at) }}</span>
              </button>
            </li>
          </ul>
          <div class="version-detail">
            <p v-if="!selectedVersion" class="muted">点击左侧版本查看时间；若后端提供正文会显示在此。</p>
            <template v-else>
              <div class="version-meta">
                版本 v{{ selectedVersion }}
                <span v-if="selectedCreatedAt">· {{ formatTime(selectedCreatedAt) }}</span>
              </div>
              <p v-if="versionDetailLoading" class="muted">加载正文...</p>
              <p v-else-if="versionContentHint" class="muted">{{ versionContentHint }}</p>
              <div v-else class="doc-body" v-html="versionHtml"></div>
            </template>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn" @click="closeVersions">关闭</button>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="showEdit" class="modal-mask" @click.self="closeEdit">
      <div class="modal wide">
        <h3>编辑文档</h3>
        <label class="label">标题</label>
        <input v-model="editForm.title" class="input" />
        <label class="label">所属空间</label>
        <select v-model="editForm.space_id" class="select">
          <option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
        <label class="label">内容</label>
        <RichTextEditor v-model="editForm.content" placeholder="请输入文档内容..." />
        <p v-if="editError" class="error">{{ editError }}</p>
        <div class="modal-actions">
          <button type="button" class="link-btn" @click="closeEdit">取消</button>
          <button type="button" class="btn" :disabled="saving" @click="submitEdit">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import {
  listDocuments,
  getDocument,
  uploadDocument,
  updateDocument,
  deleteDocument,
  listDocumentVersions,
  getDocumentVersion,
} from '../../api/documents'
import { listDocSpaces } from '../../api/auth'
import { listDocCitations, withCitationCounts } from '../../api/stats'
import RichTextEditor from '../../components/RichTextEditor.vue'
import { renderDocContent } from '../../utils/renderContent'

const docs = ref([])
const spaces = ref([])
const error = ref('')
const okMsg = ref('')

const showUpload = ref(false)
const uploadFile = ref(null)
const uploadSpaceId = ref(1)
const uploading = ref(false)
const uploadError = ref('')

const showPreview = ref(false)
const previewLoading = ref(false)
const previewError = ref('')
const previewTitle = ref('')
const previewHtml = ref('')

const showVersions = ref(false)
const versionDocId = ref(null)
const versionDocTitle = ref('')
const versionLoading = ref(false)
const versionError = ref('')
const versions = ref([])
const selectedVersion = ref(null)
const selectedCreatedAt = ref('')
const versionDetailLoading = ref(false)
const versionHtml = ref('')
const versionContentHint = ref('')

const showEdit = ref(false)
const saving = ref(false)
const editError = ref('')
const editForm = reactive({
  id: null,
  title: '',
  content: '',
  space_id: 1,
})

const STALE_MS = 90 * 24 * 60 * 60 * 1000

function formatTime(iso) {
  if (!iso) return ''
  return String(iso).replace('T', ' ').slice(0, 16)
}

/** updated_at 超过 90 天：整行文字标黄，提醒文档可能过期 */
function isStale(updatedAt) {
  if (!updatedAt) return false
  const t = new Date(updatedAt).getTime()
  if (Number.isNaN(t)) return false
  return Date.now() - t > STALE_MS
}

/** 纯文本转简单 HTML，便于编辑器展示 */
function toEditorHtml(content) {
  if (!content) return '<p></p>'
  if (/<[a-z][\s\S]*>/i.test(content)) return content
  return content
    .split(/\n+/)
    .map((line) => `<p>${line}</p>`)
    .join('')
}

async function refresh() {
  error.value = ''
  try {
    const [list, stats] = await Promise.all([listDocuments(), listDocCitations()])
    docs.value = withCitationCounts(list, stats)
  } catch (e) {
    error.value = e.detail || e.message || '加载文档失败'
  }
}

onMounted(async () => {
  try {
    spaces.value = await listDocSpaces()
    if (spaces.value.length) uploadSpaceId.value = spaces.value[0].id
  } catch (e) {
    error.value = e.detail || e.message || '加载空间失败'
  }
  await refresh()
})

function openUpload() {
  uploadError.value = ''
  uploadFile.value = null
  showUpload.value = true
}

function onFileChange(e) {
  uploadFile.value = e.target.files?.[0] || null
}

async function submitUpload() {
  uploadError.value = ''
  if (!uploadFile.value) {
    uploadError.value = '请选择文件'
    return
  }
  if (!uploadSpaceId.value) {
    uploadError.value = '请选择文档空间'
    return
  }
  uploading.value = true
  try {
    await uploadDocument(uploadFile.value, uploadSpaceId.value)
    showUpload.value = false
    okMsg.value = '上传成功'
    await refresh()
  } catch (e) {
    uploadError.value = e.detail || e.message || '上传失败'
  } finally {
    uploading.value = false
  }
}

async function openPreview(d) {
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

async function openVersions(d) {
  versionDocId.value = d.id
  versionDocTitle.value = d.title || ''
  versions.value = []
  selectedVersion.value = null
  selectedCreatedAt.value = ''
  versionHtml.value = ''
  versionContentHint.value = ''
  versionError.value = ''
  showVersions.value = true
  versionLoading.value = true
  try {
    versions.value = await listDocumentVersions(d.id)
  } catch (e) {
    versionError.value = e.detail || e.message || '加载版本失败'
  } finally {
    versionLoading.value = false
  }
}

function closeVersions() {
  showVersions.value = false
}

async function selectVersion(v) {
  selectedVersion.value = v.version
  selectedCreatedAt.value = v.created_at || ''
  versionHtml.value = ''
  versionContentHint.value = ''

  // 列表里若已带 content（mock / 扩展字段），直接展示
  if (v.content) {
    versionHtml.value = renderDocContent(v.content)
    return
  }

  versionDetailLoading.value = true
  try {
    const detail = await getDocumentVersion(versionDocId.value, v.version)
    if (detail?.content) {
      versionHtml.value = renderDocContent(detail.content)
    } else {
      versionContentHint.value = '后端未提供该版本正文，仅显示版本号与时间。'
    }
  } catch {
    versionContentHint.value = '后端未提供该版本正文，仅显示版本号与时间。'
  } finally {
    versionDetailLoading.value = false
  }
}

async function openEdit(d) {
  editError.value = ''
  try {
    const detail = await getDocument(d.id)
    editForm.id = detail.id
    editForm.title = detail.title
    editForm.content = toEditorHtml(detail.content)
    editForm.space_id = detail.space_id
    showEdit.value = true
  } catch (e) {
    error.value = e.detail || e.message || '加载文档详情失败'
  }
}

function closeEdit() {
  showEdit.value = false
}

async function submitEdit() {
  editError.value = ''
  if (!editForm.title.trim()) {
    editError.value = '标题不能为空'
    return
  }
  saving.value = true
  try {
    await updateDocument(editForm.id, {
      title: editForm.title.trim(),
      content: editForm.content,
      space_id: editForm.space_id,
    })
    showEdit.value = false
    okMsg.value = '保存成功'
    await refresh()
  } catch (e) {
    editError.value = e.detail || e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function onDelete(d) {
  if (!confirm(`确认删除「${d.title}」？`)) return
  try {
    await deleteDocument(d.id)
    okMsg.value = '已删除'
    await refresh()
  } catch (e) {
    error.value = e.detail || e.message || '删除失败'
  }
}
</script>

<style scoped>
.panel {
  background: var(--color-surface);
  border-radius: 12px;
  padding: 20px 22px;
  box-shadow: var(--shadow);
  border: 1px solid var(--color-border);
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}
h2 { margin: 0 0 4px; font-size: 18px; }
.muted { color: var(--color-text-secondary); margin: 0; font-size: 13px; }
.btn {
  border: none;
  background: var(--gradient);
  color: #fff;
  border-radius: var(--radius-sm);
  padding: 9px 16px;
  font-weight: 600;
  cursor: pointer;
}
.btn:hover:not(:disabled) { filter: brightness(1.06); }
.btn:disabled { background: var(--color-primary-muted); cursor: not-allowed; }
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
tbody tr.stale td {
  color: #ca8a04;
}
tbody tr.stale .action-btn {
  color: #ca8a04;
  border-color: #fde68a;
}
tbody tr.stale .action-btn.danger {
  color: #ca8a04;
}
tbody tr.stale:hover { background: #fffbeb; }
.empty { text-align: center; color: #999; }
.ops {
  white-space: nowrap;
  display: flex;
  align-items: center;
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
  line-height: 1.4;
}
.action-btn:hover { background: var(--color-primary-soft); border-color: var(--color-primary-muted); }
.action-btn.danger { color: var(--color-danger); }
.action-btn.danger:hover { background: #fef2f2; border-color: #fecaca; }
.link-btn {
  border: none;
  background: transparent;
  color: var(--color-primary);
  cursor: pointer;
  padding: 0 8px 0 0;
}
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
.label {
  display: block;
  font-weight: 600;
  margin: 12px 0 6px;
  font-size: 13px;
}
.input, .select, .textarea {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
.textarea { resize: vertical; }
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.doc-body {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  background: #f8fafc;
  max-height: 420px;
  overflow: auto;
  line-height: 1.7;
  font-size: 14px;
}
.doc-body :deep(h1),
.doc-body :deep(h2),
.doc-body :deep(h3) {
  margin: 0.6em 0 0.35em;
}
.doc-body :deep(p) { margin: 0.4em 0; }
.doc-body :deep(ul),
.doc-body :deep(ol) { padding-left: 1.4em; margin: 0.4em 0; }
.doc-body :deep(code) {
  background: #e2e8f0;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 12px;
}

.version-layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 14px;
  min-height: 220px;
}
.version-list {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: auto;
  max-height: 360px;
}
.version-list li.active { background: var(--color-primary-soft); }
.version-item {
  display: flex;
  flex-direction: column;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f1f5f9;
}
.version-item:hover { background: #f8fafc; }
.ver { font-weight: 600; color: var(--color-primary); }
.when { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.version-detail {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 12px;
  min-height: 180px;
}
.version-meta {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #374151;
}

@media (max-width: 640px) {
  .version-layout { grid-template-columns: 1fr; }
}
</style>
