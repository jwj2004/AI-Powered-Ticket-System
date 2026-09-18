<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>知识缺口</h2>
        <p class="muted">待处理缺口榜单 · 标记已解决后通知提问者</p>
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
            <td class="ops">
              <button
                v-if="g.status === 'pending'"
                type="button"
                class="action-btn"
                title="处理"
                @click="openResolve(g)"
              >
                ✓ 处理
              </button>
              <button type="button" class="action-btn" @click="openMerge(g)">合并</button>
              <span v-if="g.status !== 'pending'" class="muted">已处理</span>
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

    <div v-if="showMerge" class="modal-mask" @click.self="showMerge = false">
      <div class="modal">
        <h3>合并知识缺口 #{{ mergeSource?.gap_id }}</h3>
        <p class="q">{{ mergeSource?.question }}</p>
        <label class="label">合并到</label>
        <select v-model="mergeTargetId" class="select">
          <option :value="null">请选择另一个缺口</option>
          <option
            v-for="g in mergeOptions"
            :key="g.gap_id"
            :value="g.gap_id"
          >
            #{{ g.gap_id }} {{ g.question }}
          </option>
        </select>
        <p v-if="mergeError" class="error">{{ mergeError }}</p>
        <div class="modal-actions">
          <button type="button" class="link-btn" @click="showMerge = false">取消</button>
          <button type="button" class="btn" :disabled="merging" @click="submitMerge">
            {{ merging ? '合并中...' : '确认合并' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { listGaps, resolveGap, mergeGaps } from '../../api/gaps'
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

const showMerge = ref(false)
const merging = ref(false)
const mergeError = ref('')
const mergeSource = ref(null)
const mergeTargetId = ref(null)

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

function openMerge(g) {
  mergeSource.value = g
  mergeTargetId.value = null
  mergeError.value = ''
  showMerge.value = true
}

const mergeOptions = computed(() =>
  gaps.value.filter((g) => g.gap_id !== mergeSource.value?.gap_id),
)

async function submitMerge() {
  mergeError.value = ''
  if (mergeTargetId.value == null) {
    mergeError.value = '请选择另一个缺口'
    return
  }
  merging.value = true
  try {
    await mergeGaps(mergeSource.value.gap_id, mergeTargetId.value)
    showMerge.value = false
    okMsg.value = `已将缺口 #${mergeSource.value.gap_id} 合并到 #${mergeTargetId.value}`
    await refresh()
  } catch (e) {
    mergeError.value = e.detail || e.message || '合并失败'
  } finally {
    merging.value = false
  }
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
.status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 12px;
}
.status.pending { background: #fff7ed; color: var(--color-warn); }
.status.resolved { background: #ecfdf5; color: var(--color-success); }
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
}
.action-btn:hover { background: var(--color-primary-soft); border-color: var(--color-primary-muted); }
.ops { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.link-btn {
  border: none;
  background: transparent;
  color: var(--color-primary);
  cursor: pointer;
  padding: 0;
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
.btn:disabled { background: #93c5fd; cursor: not-allowed; }
.error { color: var(--color-danger); }
.ok { color: var(--color-success); }

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
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
  border-radius: 14px;
  padding: 20px;
  box-shadow: var(--shadow-lg);
}
.modal h3 { margin: 0 0 8px; }
.q { color: #555; margin: 0 0 12px; }
.label {
  display: block;
  font-weight: 600;
  margin: 12px 0 6px;
  font-size: 13px;
}
.textarea, .select {
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
</style>
