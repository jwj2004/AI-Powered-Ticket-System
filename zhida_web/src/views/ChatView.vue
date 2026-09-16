<template>
  <div class="chat-page">
    <header class="top">
      <div>
        <h1>知答 · 问答</h1>
        <p class="sub">你好，{{ username }}（{{ role }}）</p>
      </div>
      <div class="top-actions">
        <button v-if="role === 'admin'" class="link" @click="$router.push('/admin/documents')">
          管理后台
        </button>
        <button class="link" @click="onLogout">退出</button>
      </div>
    </header>

    <div class="body">
      <aside class="sidebar">
        <div class="side-title">会话</div>
        <p class="muted">多轮对话已启用；历史列表 D3 再接</p>
        <p v-if="conversationId" class="conv-id">当前会话 #{{ conversationId }}</p>
      </aside>

      <main class="main">
        <div ref="listEl" class="messages">
          <div v-if="!messages.length && !loading" class="placeholder">
            <p>开始提问吧</p>
            <p class="muted">试试「订单导出超时」或「支付回调」；输入「没有答案」可看低置信度样式</p>
          </div>

          <div
            v-for="(m, i) in messages"
            :key="i"
            class="row"
            :class="m.role"
          >
            <div
              class="bubble"
              :class="{
                user: m.role === 'user',
                assistant: m.role === 'assistant',
                low: m.role === 'assistant' && m.confidence === 'low',
              }"
            >
              <div class="role">{{ m.role === 'user' ? '我' : '知答' }}</div>
              <div class="content">{{ m.content }}</div>

              <!-- 引用来源：可点击 -->
              <div v-if="m.citations?.length" class="cites">
                <div class="cites-label">引用来源</div>
                <button
                  v-for="(c, j) in m.citations"
                  :key="j"
                  type="button"
                  class="cite-chip"
                  @click="openCitation(c)"
                >
                  {{ c.title }} · chunk {{ c.chunk_index }}
                </button>
              </div>

              <!-- 低置信度 + gap_id -->
              <div v-if="m.confidence === 'low'" class="gap-tip">
                证据不足，已记入知识缺口
                <span v-if="m.gap_id != null">（gap_id: {{ m.gap_id }}）</span>
              </div>

              <!-- 赞 / 踩 -->
              <div v-if="m.role === 'assistant' && m.message_id" class="fb">
                <button
                  type="button"
                  class="fb-btn"
                  :class="{ active: m.feedback === true }"
                  :disabled="m.feedback !== null"
                  @click="onFeedback(m, true)"
                >
                  赞
                </button>
                <button
                  type="button"
                  class="fb-btn down"
                  :class="{ active: m.feedback === false }"
                  :disabled="m.feedback !== null"
                  @click="onFeedback(m, false)"
                >
                  踩
                </button>
                <span v-if="m.feedback !== null" class="fb-done">已反馈</span>
              </div>
            </div>
          </div>

          <!-- 加载态：正在思考 -->
          <div v-if="loading" class="row assistant">
            <div class="bubble assistant thinking">
              <div class="role">知答</div>
              <div class="content thinking-text">正在思考...</div>
            </div>
          </div>
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <!-- 底部固定输入：Enter 发送，Shift+Enter 换行 -->
        <div class="composer-wrap">
          <div class="composer">
            <textarea
              v-model="input"
              class="input"
              rows="2"
              placeholder="输入问题，Enter 发送，Shift+Enter 换行"
              @keydown="onKeydown"
            ></textarea>
            <button class="btn" :disabled="loading || !input.trim()" @click="onSend">
              发送
            </button>
          </div>
        </div>
      </main>
    </div>

    <!-- 引用详情弹层（mock chunk） -->
    <div v-if="citationDetail" class="modal-mask" @click.self="citationDetail = null">
      <div class="modal">
        <div class="modal-title">
          {{ citationDetail.title }}
          <span class="chunk-tag">chunk {{ citationDetail.chunk_index }}</span>
        </div>
        <p class="modal-meta">document_id: {{ citationDetail.document_id }}</p>
        <div class="modal-body">{{ citationDetail.content }}</div>
        <button type="button" class="btn modal-close" @click="citationDetail = null">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getUsername, getRole, clearAuth } from '../api/authStorage'
import { chat, sendFeedback, getCitationChunk } from '../api/chat'

const router = useRouter()
const username = getUsername() || ''
const role = getRole() || ''

const input = ref('')
const loading = ref(false)
const error = ref('')
const conversationId = ref(null)
const messages = ref([])
const listEl = ref(null)
const citationDetail = ref(null)

async function scrollToBottom() {
  await nextTick()
  const el = listEl.value
  if (el) el.scrollTop = el.scrollHeight
}

function onKeydown(e) {
  // Enter 发送；Shift+Enter 换行
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}

async function onSend() {
  const text = input.value.trim()
  if (!text || loading.value) return

  error.value = ''
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const data = await chat({
      message: text,
      conversation_id: conversationId.value,
    })
    conversationId.value = data.conversation_id
    messages.value.push({
      role: 'assistant',
      content: data.reply,
      citations: data.citations || [],
      confidence: data.confidence,
      message_id: data.message_id,
      gap_id: data.gap_id ?? null,
      feedback: null,
    })
  } catch (e) {
    error.value = e.detail || e.message || '发送失败'
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function onFeedback(m, useful) {
  if (!m.message_id || m.feedback !== null) return
  try {
    await sendFeedback({ message_id: m.message_id, useful })
    m.feedback = useful
  } catch (e) {
    error.value = e.detail || e.message || '反馈失败'
  }
}

function openCitation(c) {
  citationDetail.value = getCitationChunk(c)
}

function onLogout() {
  clearAuth()
  router.replace('/login')
}
</script>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  font: 14px/1.6 -apple-system, "PingFang SC", sans-serif;
  background: #f7f8fa;
}
.top {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
}
h1 { margin: 0; font-size: 18px; }
.sub { margin: 2px 0 0; color: #888; font-size: 12px; }
.top-actions { display: flex; gap: 8px; }
.link {
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  font: inherit;
}
.body {
  flex: 1;
  display: flex;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
  min-height: 0;
}
.sidebar {
  width: 200px;
  flex-shrink: 0;
  padding: 16px;
  border-right: 1px solid #e8e8e8;
  background: #fff;
}
.side-title { font-weight: 600; margin-bottom: 8px; }
.muted { color: #999; font-size: 12px; }
.conv-id { margin-top: 12px; font-size: 12px; color: #666; }
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}
.messages {
  flex: 1;
  overflow: auto;
  padding: 20px 16px 12px;
}
.placeholder {
  color: #666;
  text-align: center;
  margin-top: 64px;
}
.placeholder .muted { margin-top: 8px; }

.row {
  display: flex;
  margin-bottom: 14px;
}
.row.user { justify-content: flex-end; }
.row.assistant { justify-content: flex-start; }

.bubble {
  max-width: min(720px, 85%);
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #eee;
  background: #fff;
}
.bubble.user {
  background: #1a73e8;
  border-color: #1a73e8;
  color: #fff;
  border-bottom-right-radius: 4px;
}
.bubble.user .role { color: rgba(255, 255, 255, 0.75); }
.bubble.assistant {
  background: #fff;
  border-bottom-left-radius: 4px;
}
.bubble.low {
  background: #fff8e1;
  border-color: #f0d58c;
}
.bubble.thinking {
  border-style: dashed;
  color: #666;
}
.thinking-text {
  color: #888;
  font-style: italic;
}
.role {
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
}
.content {
  white-space: pre-wrap;
  word-break: break-word;
}

.cites { margin-top: 10px; }
.cites-label {
  font-size: 12px;
  color: #888;
  margin-bottom: 6px;
}
.cite-chip {
  display: inline-block;
  margin: 0 6px 6px 0;
  padding: 4px 10px;
  border: 1px solid #c5d8f7;
  border-radius: 999px;
  background: #eef4ff;
  color: #1a73e8;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
.cite-chip:hover { background: #dce8ff; }

.gap-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #b26a00;
}

.fb {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.fb-btn {
  font: inherit;
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid #ddd;
  background: #fff;
  cursor: pointer;
}
.fb-btn.down { color: #b3261e; }
.fb-btn.active {
  background: #e8f0fe;
  border-color: #1a73e8;
  color: #1a73e8;
}
.fb-btn.down.active {
  background: #fce8e6;
  border-color: #b3261e;
  color: #b3261e;
}
.fb-btn:disabled { cursor: not-allowed; opacity: 0.7; }
.fb-done { font-size: 12px; color: #888; }

.composer-wrap {
  flex-shrink: 0;
  padding: 12px 16px 16px;
  background: #f7f8fa;
  border-top: 1px solid #e8e8e8;
}
.composer {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: #fff;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e8e8e8;
}
.input {
  flex: 1;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font: inherit;
  box-sizing: border-box;
}
.btn {
  padding: 10px 18px;
  border: none;
  border-radius: 6px;
  background: #1a73e8;
  color: #fff;
  font: inherit;
  cursor: pointer;
}
.btn:disabled { background: #9bb8e8; cursor: not-allowed; }
.error {
  color: #d93025;
  margin: 0 16px 8px;
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
.modal-title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 6px;
}
.chunk-tag {
  margin-left: 8px;
  font-size: 12px;
  font-weight: 400;
  color: #1a73e8;
  background: #eef4ff;
  padding: 2px 8px;
  border-radius: 999px;
}
.modal-meta { margin: 0 0 12px; font-size: 12px; color: #888; }
.modal-body {
  white-space: pre-wrap;
  line-height: 1.7;
  margin-bottom: 16px;
}
.modal-close { width: 100%; }
</style>
