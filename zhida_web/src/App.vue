<template>
  <div class="page">
    <h1>知答 · 工单副驾</h1>
    <p class="subtitle">粘贴客户原话，生成答复草稿</p>

    <textarea
      v-model="rawText"
      placeholder="粘贴客户原话或输入错误码..."
      class="input"
    ></textarea>

    <button @click="generate" :disabled="loading || !rawText.trim()" class="btn">
      {{ loading ? '生成中...' : '生成答复草稿' }}
    </button>

    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
    <p v-if="result?.confidence === 'low'" class="warn">
      {{ result.message || '未找到可靠依据，建议转二线处理' }}
    </p>

    <div v-if="result?.error_code" class="section">
      <div class="label">错误码</div>
      <div class="error-code">{{ result.error_code }}</div>
    </div>

    <div v-if="result?.evidence?.length" class="section">
      <div class="label">历史相似工单</div>
      <div v-for="e in result.evidence" :key="e.ticket_id" class="evidence">
        · [{{ e.ticket_id }}] {{ e.summary }}
      </div>
    </div>

    <div v-if="result?.draft" class="section">
      <div class="label">答复草稿</div>
      <div class="draft">{{ result.draft }}</div>
      <button @click="copyDraft" class="copy">{{ copied ? '已复制 ✓' : '复制草稿' }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const API_BASE = 'http://127.0.0.1:8000'

const rawText = ref('')
const loading = ref(false)
const errorMsg = ref('')
const result = ref(null)
const copied = ref(false)

async function generate() {
  loading.value = true
  errorMsg.value = ''
  result.value = null
  copied.value = false

  try {
    const resp = await fetch(`${API_BASE}/api/draft`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text: rawText.value, customer_id: 'C003' })
    })
    result.value = await resp.json()
  } catch (err) {
    errorMsg.value = '后端连接失败，请确认 FastAPI 已启动在 8000 端口'
  } finally {
    loading.value = false
  }
}

async function copyDraft() {
  if (!result.value?.draft) return
  await navigator.clipboard.writeText(result.value.draft)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)

  // 上报埋点
  try {
    await fetch(`${API_BASE}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query_id: result.value.query_id,
        copied: true,
        thumbs_down: false
      })
    })
  } catch (e) { /* 埋点失败不影响主流程 */ }
}
</script>

<style scoped>
.page {
  max-width: 600px;
  margin: 40px auto;
  font: 14px/1.6 -apple-system, "PingFang SC", sans-serif;
  padding: 0 20px;
}
h1 { font-size: 22px; margin-bottom: 4px; }
.subtitle { color: #888; margin-top: 0; }
.input {
  width: 100%;
  height: 80px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  resize: vertical;
  box-sizing: border-box;
  font: inherit;
}
.btn {
  margin-top: 10px;
  padding: 10px 20px;
  background: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
}
.btn:disabled { background: #9bb8e8; cursor: not-allowed; }
.error { color: #d93025; }
.warn { color: #b26a00; background: #fff8e1; padding: 10px; border-radius: 6px; }
.section { margin-top: 16px; }
.label { font-weight: 600; margin-bottom: 6px; }
.error-code { background: #fff3e0; padding: 10px; border-radius: 6px; }
.evidence { background: #f5f5f5; padding: 8px 10px; border-radius: 6px; margin-bottom: 4px; font-size: 13px; }
.draft { background: #e8f0fe; padding: 12px; border-radius: 6px; white-space: pre-wrap; }
.copy {
  margin-top: 8px;
  padding: 6px 16px;
  background: #34a853;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
}
</style>
