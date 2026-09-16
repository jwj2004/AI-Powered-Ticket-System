<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>文档管理</h2>
        <p class="muted">列表 / 上传 / 富文本编辑 / 删除 · mock</p>
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
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!docs.length">
            <td colspan="5" class="empty">暂无文档</td>
          </tr>
          <tr v-for="d in docs" :key="d.id">
            <td>{{ d.title }}</td>
            <td>{{ d.space }}</td>
            <td>v{{ d.version }}</td>
            <td>{{ formatTime(d.updated_at) }}</td>
            <td class="ops">
              <button type="button" class="link-btn" @click="openEdit(d)">编辑</button>
              <button type="button" class="link-btn danger" @click="onDelete(d)">删除</button>
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

    <!-- 编辑弹窗：WangEditor 富文本，保存提交 HTML -->
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
} from '../../api/documents'
import { listDocSpaces } from '../../api/auth'
import RichTextEditor from '../../components/RichTextEditor.vue'

const docs = ref([])
const spaces = ref([])
const error = ref('')
const okMsg = ref('')

const showUpload = ref(false)
const uploadFile = ref(null)
const uploadSpaceId = ref(1)
const uploading = ref(false)
const uploadError = ref('')

const showEdit = ref(false)
const saving = ref(false)
const editError = ref('')
const editForm = reactive({
  id: null,
  title: '',
  content: '',
  space_id: 1,
})

function formatTime(iso) {
  if (!iso) return ''
  return String(iso).replace('T', ' ').slice(0, 16)
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
    docs.value = await listDocuments()
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
      content: editForm.content, // HTML
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
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e8e8e8;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}
h2 { margin: 0 0 4px; }
.muted { color: #888; margin: 0; font-size: 13px; }
.btn {
  border: none;
  background: #1a73e8;
  color: #fff;
  border-radius: 6px;
  padding: 8px 14px;
  font: inherit;
  cursor: pointer;
}
.btn:disabled { background: #9bb8e8; cursor: not-allowed; }
.table-wrap { overflow: auto; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th, td {
  border-bottom: 1px solid #eee;
  padding: 10px 8px;
  text-align: left;
}
th { color: #666; font-weight: 600; background: #fafafa; }
.empty { text-align: center; color: #999; }
.ops { white-space: nowrap; }
.link-btn {
  border: none;
  background: transparent;
  color: #1a73e8;
  cursor: pointer;
  font: inherit;
  padding: 0 8px 0 0;
}
.link-btn.danger { color: #d93025; }
.error { color: #d93025; }
.ok { color: #137333; }

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
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
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}
.modal.wide { max-width: 640px; }
.modal h3 { margin: 0 0 12px; }
.label {
  display: block;
  font-weight: 600;
  margin: 12px 0 6px;
}
.input, .select, .textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font: inherit;
  box-sizing: border-box;
}
.textarea { resize: vertical; }
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}
</style>
