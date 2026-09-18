<template>
  <div class="chat-page">
    <header class="top">
      <div>
        <h1>知答 · 问答</h1>
        <p class="sub">你好，{{ username }}（{{ role }}）</p>
      </div>
      <div class="top-actions">
        <div class="bell-wrap">
          <button type="button" class="bell" title="通知" @click="toggleNotif">
            🔔
            <span v-if="unreadCount > 0" class="badge" :title="`未读 ${unreadCount}`"></span>
          </button>
          <div v-if="showNotif" class="notif-panel">
            <div class="notif-head">通知</div>
            <div v-if="!notifications.length" class="muted pad">暂无通知</div>
            <button
              v-for="n in notifications"
              :key="n.notification_id"
              type="button"
              class="notif-item"
              :class="{ unread: !n.read }"
              @click="onOpenNotif(n)"
            >
              <div class="notif-q">{{ n.question }}</div>
              <div class="notif-a">{{ n.answer }}</div>
              <div class="notif-t">{{ formatTime(n.created_at) }}</div>
            </button>
          </div>
        </div>
        <button v-if="role === 'admin'" class="link" @click="$router.push('/admin/documents')">
          管理后台
        </button>
        <button v-if="role === 'newbie'" class="link" @click="$router.push('/faq')">
          新手指南
        </button>
        <UserMenu />
        <button class="link" @click="onLogout">退出</button>
      </div>
    </header>

    <div class="body">
      <aside class="sidebar">
        <div class="side-head">
          <div class="side-title">历史会话</div>
          <button type="button" class="new-chat" @click="onNewChat">新对话</button>
        </div>
        <input
          v-model="convQuery"
          class="conv-search"
          type="search"
          placeholder="搜索会话标题..."
          aria-label="搜索会话"
        />
        <div v-if="convLoading" class="muted pad">加载中...</div>
        <button
          v-for="c in filteredConversations"
          :key="c.conversation_id"
          type="button"
          class="conv-item"
          :class="{ active: conversationId === c.conversation_id }"
          @click="onSelectConversation(c.conversation_id)"
        >
          <div class="conv-title">{{ c.title }}</div>
          <div class="conv-time">{{ formatTime(c.updated_at) }}</div>
        </button>
        <p v-if="!convLoading && !conversations.length" class="muted pad">暂无历史会话</p>
        <p v-else-if="!convLoading && conversations.length && !filteredConversations.length" class="muted pad">
          无匹配会话
        </p>
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
                // 仅 low 标黄；high / medium 正常气泡
                low: m.role === 'assistant' && isLowConfidence(m.confidence),
              }"
            >
              <div class="role">{{ m.role === 'user' ? '我' : '知答' }}</div>
              <div class="content">
                {{ m.content }}<span v-if="m.typing" class="cursor" aria-hidden="true">|</span>
              </div>

              <!-- 引用来源：打字结束后再展示 -->
              <div v-if="!m.typing && m.citations?.length" class="cites">
                <div class="cites-label">引用来源</div>
                <button
                  v-for="(c, j) in m.citations"
                  :key="j"
                  type="button"
                  class="cite-chip"
                  @click="openCitation(c)"
                >
                  <span class="cite-ico" aria-hidden="true">📄</span>
                  <span>{{ c.title }} · chunk {{ c.chunk_index }}</span>
                </button>
              </div>

              <!-- 仅 low：黄色提示 + gap_id；medium 不显示 -->
              <div v-if="!m.typing && isLowConfidence(m.confidence)" class="gap-tip">
                证据不足，已记入知识缺口
                <span v-if="m.gap_id != null">（gap_id: {{ m.gap_id }}）</span>
              </div>

              <!-- 复制 + 赞 / 踩：打字结束后再展示 -->
              <div v-if="m.role === 'assistant' && !m.typing" class="fb">
                <button type="button" class="fb-btn copy" @click="onCopy(m)">
                  {{ m.copied ? '已复制' : '复制' }}
                </button>
                <template v-if="m.message_id">
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
                </template>
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
          <div v-if="historyLoading" class="placeholder">
            <p class="muted">加载历史消息...</p>
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
            <button class="btn send-btn" :disabled="loading || !input.trim()" @click="onSend" title="发送">
              ↑
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
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getUsername, getRole, clearAuth } from '../api/authStorage'
import { chat, sendFeedback, getCitationChunk, listConversations, listMessages } from '../api/chat'
import { listNotifications, markNotificationRead } from '../api/notifications'
import { typewrite } from '../utils/typewriter'
import UserMenu from '../components/UserMenu.vue'

const router = useRouter()
const username = getUsername() || ''
const role = getRole() || ''

const input = ref('')
const loading = ref(false)
const historyLoading = ref(false)
const error = ref('')
const conversationId = ref(null)
const messages = ref([])
const listEl = ref(null)
const citationDetail = ref(null)

const conversations = ref([])
const convQuery = ref('')
const convLoading = ref(false)
const notifications = ref([])
const notifUnread = ref(0)
const showNotif = ref(false)

/** 切换会话时递增，打断进行中的打字机 */
let typeToken = 0

const unreadCount = computed(() => notifUnread.value)

const filteredConversations = computed(() => {
  const q = convQuery.value.trim().toLowerCase()
  if (!q) return conversations.value
  return conversations.value.filter((c) => String(c.title || '').toLowerCase().includes(q))
})

function formatTime(iso) {
  if (!iso) return ''
  return String(iso).replace('T', ' ').slice(0, 16)
}

/** confidence: high | medium | low；仅 low 显示证据不足黄条 */
function isLowConfidence(confidence) {
  return confidence === 'low'
}

async function refreshConversations() {
  convLoading.value = true
  try {
    conversations.value = await listConversations()
  } catch (e) {
    error.value = e.detail || e.message || '加载会话失败'
  } finally {
    convLoading.value = false
  }
}

async function refreshNotifications() {
  try {
    const data = await listNotifications()
    notifications.value = data.items || []
    notifUnread.value = data.unread ?? 0
  } catch (e) {
    /* 通知失败不影响主流程 */
  }
}

onMounted(async () => {
  await Promise.all([refreshConversations(), refreshNotifications()])
})

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

function cancelTypewriter() {
  typeToken += 1
}

function onNewChat() {
  cancelTypewriter()
  conversationId.value = null
  messages.value = []
  error.value = ''
  input.value = ''
}

async function onSelectConversation(id) {
  if (loading.value || historyLoading.value) return
  cancelTypewriter()
  error.value = ''
  conversationId.value = id
  historyLoading.value = true
  messages.value = []
  try {
    const list = await listMessages(id)
    messages.value = list.map((m) => ({
      role: m.role,
      content: m.content,
      citations: m.citations || [],
      confidence: m.confidence || null,
      message_id: m.message_id || null,
      gap_id: m.gap_id ?? null,
      feedback: null,
      typing: false,
      copied: false,
    }))
  } catch (e) {
    error.value = e.detail || e.message || '加载消息失败'
  } finally {
    historyLoading.value = false
    await scrollToBottom()
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

  const myToken = ++typeToken

  try {
    const data = await chat({
      message: text,
      conversation_id: conversationId.value,
    })
    if (myToken !== typeToken) return

    conversationId.value = data.conversation_id
    const reply = data.reply || ''
    messages.value.push({
      role: 'assistant',
      content: '',
      citations: data.citations || [],
      confidence: data.confidence,
      message_id: data.message_id,
      gap_id: data.gap_id ?? null,
      feedback: null,
      typing: true,
      copied: false,
    })
    // 取数组内响应式对象再写 content，避免打字机不刷新
    const msg = messages.value[messages.value.length - 1]
    loading.value = false
    await scrollToBottom()

    // 本地打字机；后端 SSE 就绪后可改为流式写入 content
    await typewrite(
      reply,
      (partial) => {
        msg.content = partial
        if (partial.length % 8 === 0) scrollToBottom()
      },
      {
        interval: 18,
        shouldContinue: () => myToken === typeToken,
      },
    )

    if (myToken !== typeToken) return
    msg.content = reply
    msg.typing = false
    await refreshConversations()
  } catch (e) {
    error.value = e.detail || e.message || '发送失败'
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function onCopy(m) {
  const text = m.content || ''
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    m.copied = true
    setTimeout(() => {
      m.copied = false
    }, 1500)
  } catch (e) {
    error.value = '复制失败，请检查浏览器权限'
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

function toggleNotif() {
  showNotif.value = !showNotif.value
}

async function onOpenNotif(n) {
  if (!n.read) {
    await markNotificationRead(n.notification_id)
    n.read = true
    if (notifUnread.value > 0) notifUnread.value -= 1
  }
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
  background: var(--color-bg);
}
.top {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}
h1 { margin: 0; font-size: 18px; color: var(--color-text); }
.sub { margin: 2px 0 0; color: var(--color-text-secondary); font-size: 12px; }
.top-actions { display: flex; gap: 8px; align-items: center; }
.link {
  border: 1px solid var(--color-border);
  background: #fff;
  border-radius: var(--radius-sm);
  padding: 7px 12px;
  cursor: pointer;
  color: #374151;
}
.link:hover { border-color: var(--color-primary-muted); color: var(--color-primary); }
.bell-wrap { position: relative; }
.bell {
  position: relative;
  border: 1px solid var(--color-border);
  background: #fff;
  border-radius: var(--radius-sm);
  padding: 7px 10px;
  cursor: pointer;
  line-height: 1;
}
.badge {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 8px;
  height: 8px;
  min-width: 8px;
  padding: 0;
  border-radius: 50%;
  background: #ef4444;
  border: 1.5px solid #fff;
  box-sizing: content-box;
}
.notif-panel {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  width: 320px;
  max-height: 360px;
  overflow: auto;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  z-index: 40;
}
.notif-head {
  padding: 10px 12px;
  font-weight: 600;
  border-bottom: 1px solid var(--color-border);
}
.notif-item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  border-bottom: 1px solid #f3f4f6;
  background: #fff;
  padding: 10px 12px;
  cursor: pointer;
}
.notif-item.unread { background: #eff6ff; }
.notif-q { font-weight: 600; font-size: 13px; }
.notif-a { color: #555; font-size: 12px; margin-top: 4px; }
.notif-t { color: #999; font-size: 11px; margin-top: 4px; }
.pad { padding: 8px 0; }
.body {
  flex: 1;
  display: flex;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
  min-height: 0;
  background: var(--color-surface);
  box-shadow: var(--shadow);
  border-left: 1px solid var(--color-border);
  border-right: 1px solid var(--color-border);
}
.sidebar {
  width: 240px;
  flex-shrink: 0;
  padding: 14px 12px;
  border-right: 1px solid var(--color-border);
  background: #fafbfc;
  overflow: auto;
}
.side-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}
.side-title { font-weight: 600; font-size: 13px; color: #374151; }
.new-chat {
  border: none;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-sm);
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
}
.new-chat:hover { background: var(--color-primary-hover); }
.conv-search {
  width: 100%;
  margin-bottom: 10px;
  padding: 7px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: #fff;
  font-size: 12px;
}
.conv-search:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}
.conv-item {
  display: block;
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  background: transparent;
  border-radius: var(--radius-sm);
  padding: 9px 10px;
  margin-bottom: 4px;
  cursor: pointer;
}
.conv-item:hover { background: #f3f4f6; }
.conv-item.active {
  background: var(--color-primary-soft);
  border-color: #bfdbfe;
}
.conv-title {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-time { font-size: 11px; color: #9ca3af; margin-top: 2px; }
.muted { color: var(--color-text-secondary); font-size: 12px; }
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
  background: #f8fafc;
}
.placeholder {
  color: #64748b;
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
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  border: 1px solid transparent;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.bubble.user {
  background: var(--color-primary);
  color: #fff;
  border-bottom-right-radius: 6px;
}
.bubble.user .role { color: rgba(255, 255, 255, 0.72); }
.bubble.assistant {
  background: #f1f5f9;
  color: var(--color-text);
  border-bottom-left-radius: 6px;
}
.bubble.low {
  background: #fff7ed;
  border-color: #fed7aa;
}
.bubble.thinking {
  border: 1px dashed #cbd5e1;
  background: #fff;
  color: #64748b;
}
.thinking-text {
  color: #94a3b8;
  font-style: italic;
}
.role {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}
.content {
  white-space: pre-wrap;
  word-break: break-word;
}
.cursor {
  display: inline-block;
  margin-left: 1px;
  color: var(--color-primary);
  animation: blink 0.9s step-end infinite;
  font-weight: 400;
}
@keyframes blink {
  50% { opacity: 0; }
}

.cites { margin-top: 10px; }
.cites-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}
.cite-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 0 6px 6px 0;
  padding: 4px 10px;
  border: none;
  border-radius: var(--radius-pill);
  background: #fff;
  color: var(--color-primary);
  font-size: 12px;
  cursor: pointer;
  box-shadow: 0 0 0 1px #bfdbfe inset;
  max-width: 100%;
}
.cite-ico {
  font-size: 12px;
  line-height: 1;
  flex-shrink: 0;
}
.cite-chip span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cite-chip:hover { background: var(--color-primary-soft); }

.gap-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-warn);
  background: #fffbeb;
  border-radius: 6px;
  padding: 6px 8px;
}

.fb {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.fb-btn {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: #fff;
  cursor: pointer;
}
.fb-btn.copy { color: #374151; }
.fb-btn.copy:hover { border-color: var(--color-primary-muted); color: var(--color-primary); }
.fb-btn.down { color: #b3261e; }
.fb-btn.active {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
  color: var(--color-primary);
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
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
}
.composer {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  background: #fff;
  padding: 10px 12px;
  border-radius: 20px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow);
}
.input {
  flex: 1;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  padding: 10px 14px;
  border: 1px solid transparent;
  border-radius: 14px;
  background: #f8fafc;
}
.input:focus {
  outline: none;
  border-color: var(--color-primary);
  background: #fff;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}
.btn {
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.btn:hover:not(:disabled) { background: var(--color-primary-hover); }
.btn:disabled { background: var(--color-primary-muted); cursor: not-allowed; }
.send-btn {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 50%;
  font-size: 18px;
  font-weight: 700;
  line-height: 44px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}
.error {
  color: var(--color-danger);
  margin: 0 16px 8px;
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
.modal-title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 6px;
}
.chunk-tag {
  margin-left: 8px;
  font-size: 12px;
  font-weight: 400;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}
.modal-meta { margin: 0 0 12px; font-size: 12px; color: #888; }
.modal-body {
  white-space: pre-wrap;
  line-height: 1.7;
  margin-bottom: 16px;
}
.modal-close { width: 100%; }
</style>
