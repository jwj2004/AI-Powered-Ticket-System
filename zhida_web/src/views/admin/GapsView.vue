<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>知识缺口</h2>
        <p class="muted">待处理缺口榜单 · mock resolve</p>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="okMsg" class="ok">{{ okMsg }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>问题</th>
            <th>提问人</th>
            <th>时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!gaps.length">
            <td colspan="5" class="empty">暂无缺口</td>
          </tr>
          <tr v-for="g in gaps" :key="g.gap_id">
            <td>{{ g.question }}</td>
            <td>{{ g.username }}</td>
            <td>{{ formatTime(g.created_at) }}</td>
            <td>
              <span class="status" :class="g.status">{{ g.status }}</span>
            </td>
            <td>
              <button
                v-if="g.status === 'pending'"
                type="button"
                class="link-btn"
                @click="openResolve(g)"
              >
                处理
              </button>
              <span v-else class="muted">已处理</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showModal" class="modal-mask" @click.self="showModal = false">
      <div class="modal">
        <h3>处理知识缺口 #{{ current?.gap_id }}</h3>
        <p class="q">{{ current?.question }}</p>

        <label class="label">写答案</label>
        <textarea v-model="form.answer" class="textarea" rows="5" placeholder="直接填写答案..."></textarea>

        <label class="label">或关联文档（可选）</label>
        <select v-model="form.document_id" class="select">
          <option :value="null">不关联文档</option>
          <option v-for="d in docs" :key="d.id" :value="d.id">{{ d.title }}</option>
        </select>

        <p v-if="modalError" class="error">{{ modalError }}</p>
        <div class="modal-actions">
          <button type="button" class="link-btn" @click="showModal = false">取消</button>
          <button type="button" class="btn" :disabled="saving" @click="submitResolve">
            {{ saving ? '提交中...' : '标记已解决' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { listGaps, resolveGap } from '../../api/gaps'
import { listDocuments } from '../../api/documents'

const gaps = ref([])
const docs = ref([])
const error = ref('')
const okMsg = ref('')

const showModal = ref(false)
const saving = ref(false)
const modalError = ref('')
const current = ref(null)
const form = reactive({
  answer: '',
  document_id: null,
})

function formatTime(iso) {
  if (!iso) return ''
  return String(iso).replace('T', ' ').slice(0, 16)
}

async function refresh() {
  try {
    gaps.value = await listGaps()
  } catch (e) {
    error.value = e.detail || e.message || '加载缺口失败'
  }
}

onMounted(async () => {
  await refresh()
  try {
    docs.value = await listDocuments()
  } catch (e) {
    /* 文档列表失败不影响缺口页 */
  }
})

function openResolve(g) {
  current.value = g
  form.answer = ''
  form.document_id = null
  modalError.value = ''
  showModal.value = true
}

async function submitResolve() {
  modalError.value = ''
  if (!form.answer.trim() && form.document_id == null) {
    modalError.value = '请填写答案或选择关联文档'
    return
  }
  saving.value = true
  try {
    await resolveGap(current.value.gap_id, {
      answer: form.answer.trim() || null,
      document_id: form.document_id,
    })
    showModal.value = false
    okMsg.value = '已标记为 resolved'
    await refresh()
  } catch (e) {
    modalError.value = e.detail || e.message || '处理失败'
  } finally {
    saving.value = false
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
.toolbar { margin-bottom: 16px; }
h2 { margin: 0 0 4px; }
.muted { color: #888; margin: 0; font-size: 13px; }
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
.status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
}
.status.pending { background: #fff8e1; color: #b26a00; }
.status.resolved { background: #e6f4ea; color: #137333; }
.link-btn {
  border: none;
  background: transparent;
  color: #1a73e8;
  cursor: pointer;
  font: inherit;
  padding: 0;
}
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
  max-width: 480px;
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}
.modal h3 { margin: 0 0 8px; }
.q { color: #555; margin: 0 0 12px; }
.label {
  display: block;
  font-weight: 600;
  margin: 12px 0 6px;
}
.textarea, .select {
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
