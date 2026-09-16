<template>
  <div class="panel">
    <div class="toolbar">
      <div>
        <h2>新手指南 FAQ</h2>
        <p class="muted">管理员可发布 FAQ · mock</p>
      </div>
      <button type="button" class="btn" @click="openCreate">新建 FAQ</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="okMsg" class="ok">{{ okMsg }}</p>

    <div v-if="!faq.length" class="empty">暂无 FAQ</div>
    <div v-for="f in faq" :key="f.id" class="card">
      <div class="q">{{ f.question }}</div>
      <div class="a">{{ f.answer }}</div>
      <div v-if="f.gap_id != null" class="meta">关联 gap_id: {{ f.gap_id }}</div>
    </div>

    <div v-if="showModal" class="modal-mask" @click.self="showModal = false">
      <div class="modal">
        <h3>新建 FAQ</h3>
        <label class="label">问题</label>
        <input v-model="form.question" class="input" placeholder="例如：订单导出超时怎么办？" />
        <label class="label">答案</label>
        <textarea v-model="form.answer" class="textarea" rows="5" placeholder="填写标准答复..."></textarea>
        <label class="label">关联 gap_id（可选）</label>
        <input v-model="form.gap_id" class="input" placeholder="如 5" />
        <p v-if="modalError" class="error">{{ modalError }}</p>
        <div class="modal-actions">
          <button type="button" class="link-btn" @click="showModal = false">取消</button>
          <button type="button" class="btn" :disabled="saving" @click="submitCreate">
            {{ saving ? '发布中...' : '发布' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { listFaq, publishFaq } from '../../api/faq'

const faq = ref([])
const error = ref('')
const okMsg = ref('')

const showModal = ref(false)
const saving = ref(false)
const modalError = ref('')
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
  form.question = ''
  form.answer = ''
  form.gap_id = ''
  modalError.value = ''
  showModal.value = true
}

async function submitCreate() {
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
      gap_id: form.gap_id === '' ? null : Number(form.gap_id),
    })
    showModal.value = false
    okMsg.value = '已发布'
    await refresh()
  } catch (e) {
    modalError.value = e.detail || e.message || '发布失败'
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
.empty { color: #999; text-align: center; padding: 24px 0; }
.card {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.q { font-weight: 600; margin-bottom: 6px; }
.a { color: #444; white-space: pre-wrap; }
.meta { margin-top: 8px; font-size: 12px; color: #888; }
.error { color: #d93025; }
.ok { color: #137333; }
.link-btn {
  border: none;
  background: transparent;
  color: #1a73e8;
  cursor: pointer;
  font: inherit;
}

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
.modal h3 { margin: 0 0 12px; }
.label {
  display: block;
  font-weight: 600;
  margin: 12px 0 6px;
}
.input, .textarea {
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
