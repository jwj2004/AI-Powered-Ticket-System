<template>
  <div class="page">
    <header class="header">
      <h1>知答 · 工单副驾</h1>
      <p class="subtitle">粘贴客户原话，生成答复草稿</p>
    </header>

    <div class="field">
      <label class="label" for="customer">客户</label>
      <select id="customer" v-model="customerId" class="select">
        <option v-for="c in customers" :key="c.id" :value="c.id">
          {{ c.id }} {{ c.name }}
        </option>
      </select>
    </div>

    <!-- P0-1：错误码直查 -->
    <div class="lookup-row">
      <input
        v-model="lookupCode"
        type="text"
        class="lookup-input"
        placeholder="输入错误码，如 PAY_CALLBACK_TIMEOUT"
        @keyup.enter="lookup"
      />
      <button
        @click="lookup"
        :disabled="lookupLoading || !lookupCode.trim()"
        class="btn btn-secondary"
      >
        {{ lookupLoading ? '查询中...' : '查询错误码' }}
      </button>
    </div>

    <!-- 错误码区块（lookup 结果，未命中 name 为空则不渲染） -->
    <div v-if="lookupInfo && lookupInfo.name" class="section section-lookup">
      <div class="label">错误码释义</div>
      <div class="error-code">
        <div class="error-code-title">{{ lookupInfo.code }} · {{ lookupInfo.name }}</div>
        <p v-if="lookupInfo.meaning"><strong>含义：</strong>{{ lookupInfo.meaning }}</p>
        <p v-if="lookupInfo.trigger_condition"><strong>触发条件：</strong>{{ lookupInfo.trigger_condition }}</p>
        <div v-if="lookupInfo.causes?.length">
          <strong>可能原因：</strong>
          <ul>
            <li v-for="(c, i) in lookupInfo.causes" :key="i">{{ c }}</li>
          </ul>
        </div>
        <p v-if="lookupInfo.solution"><strong>处理建议：</strong>{{ lookupInfo.solution }}</p>
        <p v-if="lookupInfo.related_versions?.length">
          <strong>相关版本：</strong>{{ lookupInfo.related_versions.join('、') }}
        </p>
      </div>
    </div>
    <p v-if="lookupMiss" class="warn">未查到该错误码，请核对后重试</p>
    <p v-if="lookupError" class="error">{{ lookupError }}</p>

    <textarea
      v-model="rawText"
      placeholder="粘贴客户原话..."
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
      <div class="label">识别错误码</div>
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
      <div class="actions">
        <button @click="copyDraft" class="copy">{{ copied ? '已复制' : '复制草稿' }}</button>
        <button
          @click="thumbsDown"
          :disabled="thumbsDowned"
          class="thumb"
          :class="{ done: thumbsDowned }"
        >
          {{ thumbsDowned ? '已反馈' : '踩一下' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const API_BASE = 'http://127.0.0.1:8000'

const customers = [
  { id: 'C001', name: '晨曦美妆' },
  { id: 'C002', name: '山野户外' },
  { id: 'C003', name: '糖心甜品' },
  { id: 'C004', name: '极客数码' },
  { id: 'C005', name: '桃桃女装' },
  { id: 'C006', name: '牧原生鲜' },
  { id: 'C007', name: '悦读书房' },
  { id: 'C008', name: '潮玩集合' },
  { id: 'C009', name: '沐光家居' },
  { id: 'C010', name: '鲜果速达' },
]

const customerId = ref('C003')
const rawText = ref('')
const loading = ref(false)
const errorMsg = ref('')
const result = ref(null)
const copied = ref(false)
const thumbsDowned = ref(false)

const lookupCode = ref('')
const lookupLoading = ref(false)
const lookupInfo = ref(null)
const lookupMiss = ref(false)
const lookupError = ref('')

async function lookup() {
  const code = lookupCode.value.trim()
  if (!code) return

  lookupLoading.value = true
  lookupError.value = ''
  lookupMiss.value = false
  lookupInfo.value = null

  try {
    const resp = await fetch(`${API_BASE}/api/lookup?code=${encodeURIComponent(code)}`)
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}))
      lookupError.value = err.detail || `查询失败（${resp.status}）`
      return
    }
    const data = await resp.json()
    // 契约：未命中时 name 为空字符串，不渲染错误码区块
    if (!data.name) {
      lookupMiss.value = true
      return
    }
    lookupInfo.value = data
  } catch (err) {
    lookupError.value = '后端连接失败，请确认 FastAPI 已启动在 8000 端口'
  } finally {
    lookupLoading.value = false
  }
}

async function generate() {
  loading.value = true
  errorMsg.value = ''
  result.value = null
  copied.value = false
  thumbsDowned.value = false

  try {
    const resp = await fetch(`${API_BASE}/api/draft`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        raw_text: rawText.value,
        customer_id: customerId.value || null,
      }),
    })
    const data = await resp.json().catch(() => ({}))
    if (!resp.ok) {
      errorMsg.value = data.detail || `生成失败（${resp.status}）`
      return
    }
    result.value = data
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
        thumbs_down: false,
      }),
    })
  } catch (e) { /* 埋点失败不影响主流程 */ }
}

async function thumbsDown() {
  if (!result.value?.query_id || thumbsDowned.value) return
  thumbsDowned.value = true
  try {
    await fetch(`${API_BASE}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query_id: result.value.query_id,
        copied: false,
        thumbs_down: true,
      }),
    })
  } catch (e) { /* 埋点失败不影响主流程 */ }
}
</script>

<style scoped>
.page {
  max-width: 640px;
  margin: 40px auto;
  font: 14px/1.6 -apple-system, "PingFang SC", sans-serif;
  padding: 0 24px 48px;
  box-sizing: border-box;
}
.header {
  text-align: center;
  margin-bottom: 24px;
}
h1 {
  font-size: 22px;
  margin: 0 0 6px;
}
.subtitle {
  color: #888;
  margin: 0;
}
.field {
  margin-bottom: 16px;
}
.select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font: inherit;
  box-sizing: border-box;
  background: #fff;
}
.lookup-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.lookup-input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font: inherit;
  box-sizing: border-box;
}
.input {
  width: 100%;
  height: 80px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  resize: vertical;
  box-sizing: border-box;
  font: inherit;
  margin-top: 4px;
}
.btn {
  margin-top: 12px;
  padding: 10px 20px;
  background: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
}
.btn-secondary {
  margin-top: 0;
  flex-shrink: 0;
  background: #5f6368;
}
.btn:disabled,
.btn-secondary:disabled {
  background: #9bb8e8;
  cursor: not-allowed;
}
.btn-secondary:disabled {
  background: #b0b3b8;
}
.error { color: #d93025; margin: 12px 0 0; }
.warn {
  color: #b26a00;
  background: #fff8e1;
  padding: 10px;
  border-radius: 6px;
  margin: 12px 0 0;
}
.section {
  margin-top: 20px;
}
.section-lookup {
  margin-top: 0;
  margin-bottom: 16px;
}
.label {
  display: block;
  font-weight: 600;
  margin-bottom: 6px;
}
.error-code {
  background: #fff3e0;
  padding: 12px;
  border-radius: 6px;
}
.error-code-title {
  font-weight: 600;
  margin-bottom: 8px;
}
.error-code p { margin: 6px 0; }
.error-code ul {
  margin: 4px 0 0;
  padding-left: 18px;
}
.evidence {
  background: #f5f5f5;
  padding: 8px 10px;
  border-radius: 6px;
  margin-bottom: 6px;
  font-size: 13px;
}
.draft {
  background: #e8f0fe;
  padding: 12px;
  border-radius: 6px;
  white-space: pre-wrap;
}
.actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.copy,
.thumb {
  padding: 6px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
  color: #fff;
}
.copy { background: #34a853; }
.thumb { background: #ea4335; }
.thumb.done,
.thumb:disabled {
  background: #b0b3b8;
  cursor: not-allowed;
}
</style>
