<template>
  <div :class="{ 'faq-standalone': standalone }">
    <header v-if="standalone" class="faq-top">
      <h1>知答 · 新手指南</h1>
      <button type="button" class="link" @click="$router.push('/chat')">返回问答</button>
    </header>

    <div class="panel">
      <div class="toolbar">
        <div>
          <h2>新手指南 FAQ</h2>
          <p class="muted">{{ isAdmin ? '管理员可发布 FAQ' : '新人入职常见问题' }}</p>
        </div>
        <button v-if="isAdmin" type="button" class="btn" @click="openCreate">新建 FAQ</button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="okMsg" class="ok">{{ okMsg }}</p>

      <div v-if="!faq.length" class="empty">暂无 FAQ</div>
      <div v-for="f in faq" :key="f.id" class="card">
        <div class="card-head">
          <div class="q">{{ f.question }}</div>
          <div v-if="isAdmin" class="card-ops">
            <button type="button" class="link-btn" @click="openEdit(f)">编辑</button>
            <button type="button" class="link-btn danger" @click="onDelete(f)">删除</button>
          </div>
        </div>
        <div class="a">{{ f.answer }}</div>
        <div v-if="f.gap_id != null" class="meta">关联 gap_id: {{ f.gap_id }}</div>
      </div>

      <div v-if="showModal" class="modal-mask" @click.self="showModal = false">
        <div class="modal">
          <h3>{{ editingId == null ? '新建 FAQ' : '编辑 FAQ' }}</h3>
          <label class="label">问题</label>
          <input v-model="form.question" class="input" placeholder="例如：订单导出超时怎么办？" />
          <label class="label">答案</label>
          <textarea v-model="form.answer" class="textarea" rows="5" placeholder="填写标准答复..."></textarea>
          <template v-if="editingId == null">
            <label class="label">关联 gap_id（可选）</label>
            <input v-model="form.gap_id" class="input" placeholder="如 5" />
          </template>
          <p v-if="modalError" class="error">{{ modalError }}</p>
          <div class="modal-actions">
            <button type="button" class="link-btn" @click="showModal = false">取消</button>
            <button type="button" class="btn" :disabled="saving" @click="submitSave">
              {{ saving ? '保存中...' : (editingId == null ? '发布' : '保存') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getRole } from '../../api/authStorage'
import { listFaq, publishFaq, updateFaq, deleteFaq } from '../../api/faq'

const route = useRoute()
const role = getRole() || ''
const isAdmin = computed(() => role === 'admin')
const standalone = computed(() => route.path === '/faq')

const faq = ref([])
const error = ref('')
const okMsg = ref('')

const showModal = ref(false)
const saving = ref(false)
const modalError = ref('')
const editingId = ref(null)
const form = reactive({
  question: '',
  answer: '',
  gap_id: '',
})

async function refresh() {
  try {
    faq.value = await listFaq()
  } catch (e) {
    error.value = e.detail || e.message || '加载 FAQ 失败'
  }
}

onMounted(refresh)

function openCreate() {
  editingId.value = null
  form.question = ''
  form.answer = ''
  form.gap_id = ''
  modalError.value = ''
  showModal.value = true
}

function openEdit(item) {
  editingId.value = item.id
  form.question = item.question || ''
  form.answer = item.answer || ''
  form.gap_id = ''
  modalError.value = ''
  showModal.value = true
}

async function submitSave() {
  modalError.value = ''
  if (!form.question.trim() || !form.answer.trim()) {
    modalError.value = '问题和答案都不能为空'
    return
  }
  saving.value = true
  try {
    if (editingId.value == null) {
      await publishFaq({
        question: form.question.trim(),
        answer: form.answer.trim(),
        gap_id: form.gap_id === '' ? null : Number(form.gap_id),
      })
      okMsg.value = '已发布'
    } else {
      await updateFaq(editingId.value, {
        question: form.question.trim(),
        answer: form.answer.trim(),
      })
      okMsg.value = '已更新'
    }
    showModal.value = false
    await refresh()
  } catch (e) {
    modalError.value = e.detail || e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function onDelete(item) {
  if (!confirm(`确认删除「${item.question}」？`)) return
  error.value = ''
  okMsg.value = ''
  try {
    await deleteFaq(item.id)
    faq.value = faq.value.filter((f) => f.id !== item.id)
    okMsg.value = '已删除'
  } catch (e) {
    error.value = e.detail || e.message || '删除失败'
  }
}
</script>

<style scoped>
.faq-standalone {
  max-width: 860px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}
.faq-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.faq-top h1 {
  margin: 0;
  font-size: 20px;
}
.faq-top .link {
  border: none;
  background: transparent;
  color: var(--color-primary);
  cursor: pointer;
  font-weight: 600;
}
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
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-sm);
  padding: 9px 16px;
  font-weight: 600;
  cursor: pointer;
}
.btn:hover:not(:disabled) { background: var(--color-primary-hover); }
.btn:disabled { background: #93c5fd; cursor: not-allowed; }
.empty { color: #999; text-align: center; padding: 24px 0; }
.card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 14px 16px;
  margin-bottom: 10px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}
.q { font-weight: 600; margin-bottom: 6px; }
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.card-ops {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.link-btn.danger { color: var(--color-danger); }
.a { color: #444; white-space: pre-wrap; }
.meta { margin-top: 8px; font-size: 12px; color: #888; }
.error { color: var(--color-danger); }
.ok { color: var(--color-success); }
.link-btn {
  border: none;
  background: transparent;
  color: var(--color-primary);
  cursor: pointer;
}

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
.modal h3 { margin: 0 0 12px; }
.label {
  display: block;
  font-weight: 600;
  margin: 12px 0 6px;
  font-size: 13px;
}
.input, .textarea {
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
