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
        <div class="side-title">会话（骨架）</div>
        <p class="muted">D2 接历史会话列表</p>
      </aside>

      <main class="main">
        <div class="messages">
          <div v-if="!messages.length" class="placeholder">
            在下方输入问题开始对话。D1 为骨架 + mock chat。
          </div>
          <div v-for="(m, i) in messages" :key="i" class="bubble" :class="m.role">
            <div class="role">{{ m.role === 'user' ? '我' : '知答' }}</div>
            <div class="content">{{ m.content }}</div>
            <div v-if="m.citations?.length" class="cites">
              引用：
              <span v-for="(c, j) in m.citations" :key="j">
                [{{ c.title }}#{{ c.chunk_index }}]
              </span>
            </div>
            <div v-if="m.confidence === 'low'" class="low">证据不足，已记入知识缺口</div>
            <div v-if="m.message_id" class="fb">
              <button @click="onFeedback(m, true)" :disabled="m.feedbackSent">有用</button>
              <button @click="onFeedback(m, false)" :disabled="m.feedbackSent">没用</button>
            </div>
          </div>
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <div class="composer">
          <textarea
            v-model="input"
            class="input"
            rows="3"
            placeholder="输入问题，例如：订单导出超时怎么办？"
            @keydown.enter.exact.prevent="onSend"
          ></textarea>
          <button class="btn" :disabled="loading || !input.trim()" @click="onSend">
            {{ loading ? '回答中...' : '发送' }}
          </button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getUsername, getRole, clearAuth } from '../api/authStorage'
import { chat, sendFeedback } from '../api/chat'

const router = useRouter()
const username = getUsername() || ''
const role = getRole() || ''

const input = ref('')
const loading = ref(false)
const error = ref('')
const conversationId = ref(null)
const messages = ref([])

async function onSend() {
  const text = input.value.trim()
  if (!text || loading.value) return

  error.value = ''
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true

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
      feedbackSent: false,
    })
  } catch (e) {
    error.value = e.detail || e.message || '发送失败'
  } finally {
    loading.value = false
  }
}

async function onFeedback(m, useful) {
  if (!m.message_id || m.feedbackSent) return
  try {
    await sendFeedback({ message_id: m.message_id, useful })
    m.feedbackSent = true
  } catch (e) {
    error.value = e.detail || e.message || '反馈失败'
  }
}

function onLogout() {
  clearAuth()
  router.replace('/login')
}
</script>

<style scoped>
.chat-page {
  min-height: 100vh;
  font: 14px/1.6 -apple-system, "PingFang SC", sans-serif;
  background: #f7f8fa;
}
.top {
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
  display: flex;
  max-width: 1100px;
  margin: 0 auto;
  min-height: calc(100vh - 64px);
}
.sidebar {
  width: 200px;
  padding: 16px;
  border-right: 1px solid #e8e8e8;
  background: #fff;
}
.side-title { font-weight: 600; margin-bottom: 8px; }
.muted { color: #999; font-size: 12px; }
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
}
.messages {
  flex: 1;
  overflow: auto;
  padding-bottom: 12px;
}
.placeholder {
  color: #999;
  text-align: center;
  margin-top: 80px;
}
.bubble {
  max-width: 720px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #eee;
}
.bubble.user { margin-left: auto; background: #e8f0fe; }
.role { font-size: 12px; color: #888; margin-bottom: 4px; }
.cites { margin-top: 6px; font-size: 12px; color: #1a73e8; }
.low { margin-top: 6px; color: #b26a00; font-size: 12px; }
.fb { margin-top: 8px; display: flex; gap: 8px; }
.fb button {
  font: inherit;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid #ddd;
  background: #fff;
  cursor: pointer;
}
.fb button:disabled { opacity: 0.5; cursor: not-allowed; }
.composer {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: #fff;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}
.input {
  flex: 1;
  resize: vertical;
  padding: 8px;
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
.error { color: #d93025; }
</style>
