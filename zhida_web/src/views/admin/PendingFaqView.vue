<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>待确认 FAQ</h2>
        <p class="muted">来自看板高频问题 · 确认后发布为新手指南 FAQ</p>
      </div>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="okMsg" class="ok">{{ okMsg }}</p>
    <p v-if="loading" class="muted">加载中...</p>

    <div v-else-if="!pending.length" class="empty">暂无待确认的高频问题</div>

    <div v-for="item in pending" :key="itemKey(item)" class="row-card">
      <div class="main">
        <div class="q">{{ item.question }}</div>
        <div class="meta">提问次数 · {{ item.count }}</div>
      </div>
      <div class="row-ops">
        <button type="button" class="btn" @click="openPublish(item)">发布为 FAQ</button>
        <button type="button" class="btn-secondary danger" @click="onDelete(item)">删除</button>
      </div>
    </div>

    <div v-if="showModal" class="modal-mask" @click.self="showModal = false">
      <div class="modal">
        <h3>发布为 FAQ</h3>
        <label class="label">问题</label>
        <input v-model="form.question" class="input" />
        <label class="label">答案</label>
        <textarea
          v-model="form.answer"
          class="textarea"
          rows="5"
          placeholder="填写标准答复后发布…"
        ></textarea>
        <p v-if="modalError" class="error">{{ modalError }}</p>
        <div class="modal-actions">
          <button type="button" class="link-btn" @click="showModal = false">取消</button>
          <button type="button" class="btn" :disabled="saving" @click="submitPublish">
            {{ saving ? '发布中...' : '确认发布' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getDashboard, listFaqCandidates } from '../../api/dashboard'
import { listFaq, publishFaq, deleteFaq } from '../../api/faq'

const loading = ref(false)
const error = ref('')
const okMsg = ref('')
const topQuestions = ref([])
const existingFaq = ref([])
/** 本页已发布 / 已删除、从待确认列表移除（key = question） */
const dismissed = ref(new Set())

const showModal = ref(false)
const saving = ref(false)
const modalError = ref('')
const form = reactive({
  question: '',
  answer: '',
  sourceKey: '',
})

const pending = computed(() => {
  const faqQs = new Set(
    existingFaq.value.map((f) => normalizeQ(f.question)),
  )
  return topQuestions.value.filter((t) => {
    const key = normalizeQ(t.question)
    if (!key) return false
    if (dismissed.value.has(key)) return false
    if (faqQs.has(key)) return false
    return true
  })
})

function normalizeQ(q) {
  return String(q || '')
    .trim()
    .replace(/[？?。.!！]+$/g, '')
    .toLowerCase()
}

function itemKey(item) {
  return item.id != null ? `id-${item.id}` : normalizeQ(item.question)
}

function dismiss(key) {
  const next = new Set(dismissed.value)
  next.add(key)
  dismissed.value = next
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    let candidates = []
    try {
      candidates = await listFaqCandidates()
    } catch (_) {
      candidates = []
    }
    if (!candidates.length) {
      const dash = await getDashboard()
      candidates = Array.isArray(dash?.top_questions)
        ? dash.top_questions.map((t) => ({
            question: t.question,
            count: t.count ?? 0,
            id: null,
          }))
        : []
    }
    topQuestions.value = candidates
    existingFaq.value = await listFaq()
  } catch (e) {
    error.value = e.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(refresh)

function openPublish(item) {
  form.question = item.question
  form.answer = ''
  form.sourceKey = normalizeQ(item.question)
  modalError.value = ''
  showModal.value = true
}

async function onDelete(item) {
  if (!window.confirm('确认删除这条待确认 FAQ？')) return
  okMsg.value = ''
  error.value = ''
  const key = normalizeQ(item.question)
  try {
    let faqId = item.id != null ? Number(item.id) : null
    if (faqId == null) {
      const matched = existingFaq.value.find(
        (f) => normalizeQ(f.question) === key,
      )
      if (matched) faqId = Number(matched.id)
    }
    if (faqId != null && !Number.isNaN(faqId)) {
      await deleteFaq(faqId)
      existingFaq.value = existingFaq.value.filter((f) => Number(f.id) !== faqId)
    }
    dismiss(key)
    topQuestions.value = topQuestions.value.filter(
      (t) => normalizeQ(t.question) !== key,
    )
    okMsg.value = '已删除'
  } catch (e) {
    error.value = e.detail || e.message || '删除失败'
  }
}

async function submitPublish() {
  modalError.value = ''
  if (!form.question.trim() || !form.answer.trim()) {
    modalError.value = '问题和答案都不能为空'
    return
  }
  saving.value = true
  try {
    await publishFaq({
      question: form.question.trim(),
      answer: form.answer.trim(),
      gap_id: null,
    })
    dismiss(form.sourceKey || normalizeQ(form.question))
    existingFaq.value = [
      { id: Date.now(), question: form.question.trim(), answer: form.answer.trim() },
      ...existingFaq.value,
    ]
    showModal.value = false
    okMsg.value = '已发布为 FAQ'
  } catch (e) {
    modalError.value = e.detail || e.message || '发布失败'
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
.empty {
  text-align: center;
  color: #94a3b8;
  padding: 36px 0;
}
.row-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  margin-bottom: 10px;
  background: #fff;
}
.row-card:hover { background: #f8fafc; }
.q { font-weight: 600; font-size: 14px; }
.meta { margin-top: 4px; font-size: 12px; color: #94a3b8; }
.row-ops {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.btn {
  border: none;
  background: var(--gradient);
  color: #fff;
  border-radius: var(--radius-sm);
  padding: 8px 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn:hover:not(:disabled) { filter: brightness(1.06); }
.btn:disabled { background: #93c5fd; cursor: not-allowed; }
.btn-secondary {
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-text);
  border-radius: var(--radius-sm);
  padding: 8px 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn-secondary.danger { color: var(--color-danger); border-color: #fecaca; }
.btn-secondary.danger:hover { background: #fef2f2; }
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
.link-btn {
  border: none;
  background: transparent;
  color: var(--color-primary);
  cursor: pointer;
}
</style>
