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
            <svg class="ico" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6 8a6 6 0 1 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
              <path d="M10 20a2 2 0 0 0 4 0" fill="none" stroke="currentColor" stroke-width="1.6" />
            </svg>
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
        <button type="button" class="link" @click="openLookup">错误码直查</button>
        <button v-if="role === 'admin'" class="link" @click="$router.push('/admin/documents')">
          管理后台
        </button>
        <UserMenu />
        <button class="link" @click="onLogout">退出</button>
      </div>
    </header>

    <div class="body">
      <aside class="sidebar">
        <nav class="side-nav">
          <button
            v-if="isNewbie"
            type="button"
            class="side-link"
            @click="openGuide"
          >
            新手指南
          </button>
          <button
            type="button"
            class="side-link"
            :class="{ on: sidePanel === 'history' }"
            @click="sidePanel = 'history'"
          >
            历史会话
          </button>
          <button
            type="button"
            class="side-link"
            :class="{ on: sidePanel === 'fav' }"
            @click="sidePanel = 'fav'"
          >
            我的收藏
          </button>
          <button
            type="button"
            class="side-link"
            :class="{ on: sidePanel === 'docs' }"
            @click="sidePanel = 'docs'"
          >
            最近文档
          </button>
          <button
            type="button"
            class="side-link"
            :class="{ on: sidePanel === 'feedback' }"
            @click="sidePanel = 'feedback'"
          >
            我的反馈
          </button>
          <button type="button" class="side-link new-chat" @click="onNewChat">新对话</button>
        </nav>

        <template v-if="sidePanel === 'history'">
          <div class="side-head">
            <div class="side-title">历史会话</div>
          </div>
          <input
            v-model="convQuery"
            class="conv-search"
            type="search"
            placeholder="搜索会话标题..."
            aria-label="搜索会话"
          />
          <div v-if="convLoading" class="muted pad">加载中...</div>
          <div
            v-for="c in filteredConversations"
            :key="c.conversation_id"
            class="conv-item"
            :class="{ active: conversationId === c.conversation_id }"
            role="button"
            tabindex="0"
            @click="onSelectConversation(c.conversation_id)"
            @keydown.enter.prevent="onSelectConversation(c.conversation_id)"
          >
            <div class="conv-main">
              <div class="conv-title">{{ c.title }}</div>
              <div class="conv-time">{{ formatTime(c.updated_at) }}</div>
            </div>
            <button
              type="button"
              class="conv-del"
              title="删除会话"
              aria-label="删除会话"
            @click.stop="onDeleteConversation(c)"
          >
            <svg class="ico" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 7h16M9 7V5h6v2M8 7l1 13h6l1-13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          </div>
          <p v-if="!convLoading && !conversations.length" class="muted pad">暂无历史会话</p>
          <p v-else-if="!convLoading && conversations.length && !filteredConversations.length" class="muted pad">
            无匹配会话
          </p>
        </template>

        <template v-else-if="sidePanel === 'fav'">
          <div class="side-title block">我的收藏</div>
          <p v-if="!favorites.length" class="muted pad">还没有收藏</p>
          <button
            v-for="f in favorites"
            :key="f.message_id"
            type="button"
            class="side-card"
            @click="onOpenSaved(f)"
          >
            <div class="conv-title">{{ f.question || '未命名问题' }}</div>
            <div class="conv-time">{{ f.reply }}</div>
          </button>
        </template>

        <template v-else-if="sidePanel === 'docs'">
          <div class="side-title block">最近文档</div>
          <p v-if="!recentDocs.length" class="muted pad">回答里引用过的文档会出现在这里</p>
          <button
            v-for="d in recentDocs"
            :key="d.document_id"
            type="button"
            class="side-card"
            @click="onPreviewDoc(d)"
          >
            <div class="conv-title">{{ d.title }}</div>
            <div class="conv-time">点击预览</div>
          </button>
        </template>

        <template v-else>
          <div class="side-title block">我的反馈</div>
          <p v-if="!myFeedback.length" class="muted pad">赞或踩之后会出现在这里</p>
          <button
            v-for="f in myFeedback"
            :key="f.message_id"
            type="button"
            class="side-card"
            @click="onOpenSaved(f)"
          >
            <div class="fb-line">
              <span class="fb-tag" :class="f.useful ? 'up' : 'down'">{{ f.useful ? '赞' : '踩' }}</span>
              <span v-if="feedbackUpdated(f)" class="updated-tag">已更新</span>
            </div>
            <div class="conv-title">{{ f.question || '未命名问题' }}</div>
          </button>
        </template>
      </aside>

      <main class="main">
        <div ref="listEl" class="messages">
          <div v-if="!messages.length && !loading" class="placeholder">
            <svg class="empty-art" viewBox="0 0 120 80" aria-hidden="true">
              <rect x="18" y="16" width="84" height="52" rx="12" fill="none" stroke="#667eea" stroke-width="2" />
              <path d="M36 40h48M36 50h28" stroke="#764ba2" stroke-width="2" stroke-linecap="round" />
              <circle cx="92" cy="22" r="8" fill="#eef2ff" stroke="#667eea" stroke-width="2" />
            </svg>
            <p>{{ emptyHint }}</p>
            <div v-if="hotQuestions.length" class="hot">
              <div class="hot-title">大家都在问</div>
              <button
                v-for="q in hotQuestions"
                :key="q"
                type="button"
                class="hot-chip"
                @click="askQuestion(q)"
              >
                {{ q }}
              </button>
            </div>
            <p v-else-if="emptyHint !== '开始新对话'" class="muted">试试「订单导出超时」或「支付回调」；输入「没有答案」可看低置信度样式</p>
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
                  <svg class="ico cite-ico" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" fill="none" stroke="currentColor" stroke-width="1.6" />
                    <path d="M14 3v5h5" fill="none" stroke="currentColor" stroke-width="1.6" />
                  </svg>
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
                  <button
                    type="button"
                    class="fb-btn"
                    :class="{ active: isFavorited(m) }"
                    @click="onToggleFavorite(m)"
                  >
                    {{ isFavorited(m) ? '已收藏' : '收藏' }}
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
              <svg class="ico" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 19V5M6 11l6-6 6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>
          <div class="templates">
            <button
              v-for="t in questionTemplates"
              :key="t"
              type="button"
              class="tpl"
              @click="applyTemplate(t)"
            >
              {{ t }}
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

    <div v-if="showGuide" class="modal-mask" @click.self="closeGuide">
      <div class="modal guide-modal">
        <div class="modal-title">欢迎使用知答，先看看这几个常见问题</div>
        <div v-if="isNewbie" class="progress">
          <div class="progress-label">已读 {{ readCount }} / 共 {{ faqItems.length }} 条</div>
          <div class="progress-track">
            <div class="progress-bar" :style="{ width: progressPct + '%' }"></div>
          </div>
        </div>
        <p v-if="!faqItems.length" class="muted">暂无常见问题</p>
        <div v-else class="guide-list">
          <div v-for="f in faqItems" :key="f.id" class="guide-row">
            <button type="button" class="guide-q" @click="onGuideAsk(f)">{{ f.question }}</button>
            <span v-if="isNewbie" class="read-tag" :class="{ read: isFaqRead(f.id) }">
              {{ isFaqRead(f.id) ? '已读' : '未读' }}
            </span>
            <button type="button" class="link-mini" @click="onGuideDetail(f)">详情</button>
          </div>
        </div>
        <div v-if="guideDetail" class="guide-detail">
          <div class="conv-title">{{ guideDetail.question }}</div>
          <div class="modal-body">{{ guideDetail.answer }}</div>
          <button type="button" class="link-mini" @click="onGuideAsk(guideDetail)">用这个问题提问</button>
        </div>
        <label class="suppress">
          <input type="checkbox" :checked="!guideAuto" @change="onSuppressChange" />
          不再自动弹出
        </label>
        <button type="button" class="btn modal-close" @click="closeGuide">开始使用</button>
      </div>
    </div>

    <div v-if="lookupOpen" class="modal-mask" @click.self="lookupOpen = false">
      <div class="modal">
        <div class="modal-title">错误码直查</div>
        <div class="lookup-row">
          <input
            v-model="lookupCode"
            class="lookup-input"
            placeholder="例如 PAY_CALLBACK_TIMEOUT"
            @keyup.enter="onLookup"
          />
          <button type="button" class="btn" :disabled="lookupLoading || !lookupCode.trim()" @click="onLookup">
            {{ lookupLoading ? '查询中...' : '查询' }}
          </button>
        </div>
        <p v-if="lookupError" class="error">{{ lookupError }}</p>
        <div v-if="lookupResult" class="lookup-result">
          <template v-if="lookupResult.name">
            <div class="lookup-name">{{ lookupResult.code }} · {{ lookupResult.name }}</div>
            <div class="modal-body">{{ lookupResult.solution || '暂无解决方案' }}</div>
          </template>
          <p v-else class="muted">没有找到这个错误码</p>
        </div>
        <button type="button" class="btn modal-close" @click="lookupOpen = false">关闭</button>
      </div>
    </div>

    <div v-if="docPreview" class="modal-mask" @click.self="docPreview = null">
      <div class="modal">
        <div class="modal-title">{{ docPreview.title }}</div>
        <p v-if="docPreview.error" class="error">{{ docPreview.error }}</p>
        <div v-else class="modal-body doc-html" v-html="docPreview.html"></div>
        <button type="button" class="btn modal-close" @click="docPreview = null">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getUsername, getRole, clearAuth } from '../api/authStorage'
import { chat, chatStream, sendFeedback, getCitationChunk, listConversations, listMessages, deleteConversation } from '../api/chat'
import { USE_MOCK } from '../api/http'
import { listNotifications, markNotificationRead } from '../api/notifications'
import { listFaq } from '../api/faq'
import { lookupErrorCode } from '../api/lookup'
import { getDocument } from '../api/documents'
import { renderDocContent } from '../utils/renderContent'
import { typewrite } from '../utils/typewriter'
import UserMenu from '../components/UserMenu.vue'
import {
  consumeGuidePending,
  guideAutoEnabled,
  setGuideAuto,
  loadReadFaq,
  markFaqRead,
  loadFavorites,
  saveFavorites,
  loadRecentDocs,
  saveRecentDocs,
  loadMyFeedback,
  saveMyFeedback,
} from '../utils/userLocal'

const router = useRouter()
const username = getUsername() || ''
const role = getRole() || ''
const isNewbie = role === 'newbie'

const questionTemplates = [
  '客户说付了钱订单没更新',
  '客户反映系统卡顿',
  '客户要退款',
]

const input = ref('')
const loading = ref(false)
const historyLoading = ref(false)
const error = ref('')
const conversationId = ref(null)
const messages = ref([])
const emptyHint = ref('开始提问吧')
const listEl = ref(null)
const citationDetail = ref(null)

const conversations = ref([])
const convQuery = ref('')
const convLoading = ref(false)
const notifications = ref([])
const notifUnread = ref(0)
const showNotif = ref(false)

const sidePanel = ref('history')
const faqItems = ref([])
const readIds = ref(loadReadFaq(username))
const favorites = ref(loadFavorites(username))
const recentDocs = ref(loadRecentDocs(username))
const myFeedback = ref(loadMyFeedback(username))
const showGuide = ref(false)
const guideAuto = ref(guideAutoEnabled(username))
const guideDetail = ref(null)

const lookupOpen = ref(false)
const lookupCode = ref('')
const lookupLoading = ref(false)
const lookupResult = ref(null)
const lookupError = ref('')
const docPreview = ref(null)

/** 切换会话时递增，打断进行中的打字机 */
let typeToken = 0

const unreadCount = computed(() => notifUnread.value)

const filteredConversations = computed(() => {
  const q = convQuery.value.trim().toLowerCase()
  if (!q) return conversations.value
  return conversations.value.filter((c) => String(c.title || '').toLowerCase().includes(q))
})

const hotQuestions = computed(() => {
  const seen = new Set()
  const out = []
  for (const f of faqItems.value) {
    const q = String(f.question || '').trim()
    if (!q || seen.has(q)) continue
    seen.add(q)
    out.push(q)
    if (out.length >= 10) break
  }
  return out
})

const readCount = computed(
  () => faqItems.value.filter((f) => readIds.value.includes(Number(f.id))).length,
)

const progressPct = computed(() => {
  if (!faqItems.value.length) return 0
  return Math.round((readCount.value / faqItems.value.length) * 100)
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

async function loadFaqList() {
  try {
    const data = await listFaq()
    faqItems.value = Array.isArray(data) ? data : []
  } catch {
    faqItems.value = []
  }
}

onMounted(async () => {
  await Promise.all([refreshConversations(), refreshNotifications(), loadFaqList()])
  if (isNewbie && consumeGuidePending(username)) showGuide.value = true
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
  sidePanel.value = 'history'
  conversationId.value = null
  messages.value = []
  emptyHint.value = '开始提问吧'
  error.value = ''
  input.value = ''
}

async function onDeleteConversation(item) {
  if (!confirm('确认删除这个会话？')) return
  error.value = ''
  try {
    await deleteConversation(item.conversation_id)
    conversations.value = conversations.value.filter(
      (c) => c.conversation_id !== item.conversation_id,
    )
    if (conversationId.value === item.conversation_id) {
      cancelTypewriter()
      conversationId.value = null
      messages.value = []
      input.value = ''
      emptyHint.value = '开始新对话'
    }
  } catch (e) {
    error.value = e.detail || e.message || '删除会话失败'
  }
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
    rememberCitations(messages.value.flatMap((m) => m.citations || []))
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
    if (USE_MOCK) {
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
      const msg = messages.value[messages.value.length - 1]
      loading.value = false
      await scrollToBottom()

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
      rememberCitations(msg.citations || [])
    } else {
      messages.value.push({
        role: 'assistant',
        content: '',
        citations: [],
        confidence: null,
        message_id: null,
        gap_id: null,
        feedback: null,
        typing: true,
        copied: false,
      })
      const msg = messages.value[messages.value.length - 1]
      loading.value = false
      await scrollToBottom()

      await chatStream(
        { message: text, conversation_id: conversationId.value },
        {
          onMeta(meta) {
            if (myToken !== typeToken) return
            conversationId.value = meta.conversation_id
            msg.citations = meta.citations || []
            msg.confidence = meta.confidence
            msg.gap_id = meta.gap_id ?? null
          },
          onToken(delta) {
            if (myToken !== typeToken) return
            msg.content += delta || ''
            if (msg.content.length % 8 === 0) scrollToBottom()
          },
          onDone(done) {
            if (myToken !== typeToken) return
            conversationId.value = done.conversation_id
            msg.content = done.reply || msg.content
            msg.citations = done.citations || msg.citations || []
            msg.confidence = done.confidence
            msg.message_id = done.message_id
            msg.gap_id = done.gap_id ?? null
            msg.typing = false
            rememberCitations(msg.citations || [])
          },
        },
      )
      if (myToken !== typeToken) return
      msg.typing = false
    }
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
    const question = questionBefore(m)
    const list = loadMyFeedback(username).filter((x) => x.message_id !== m.message_id)
    list.unshift({
      message_id: m.message_id,
      conversation_id: conversationId.value,
      question,
      useful,
      created_at: new Date().toISOString(),
    })
    saveMyFeedback(username, list)
    myFeedback.value = list
  } catch (e) {
    error.value = e.detail || e.message || '反馈失败'
  }
}

function questionBefore(m) {
  const i = messages.value.indexOf(m)
  for (let j = i - 1; j >= 0; j -= 1) {
    if (messages.value[j].role === 'user') return messages.value[j].content || ''
  }
  return ''
}

function rememberCitations(citations) {
  if (!citations?.length) return
  let list = loadRecentDocs(username)
  for (const c of citations) {
    if (c?.document_id == null) continue
    list = list.filter((d) => d.document_id !== c.document_id)
    list.unshift({
      document_id: c.document_id,
      title: c.title || `文档 #${c.document_id}`,
      chunk_index: c.chunk_index ?? null,
    })
  }
  saveRecentDocs(username, list)
  recentDocs.value = loadRecentDocs(username)
}

function isFavorited(m) {
  return favorites.value.some((f) => f.message_id === m.message_id)
}

function onToggleFavorite(m) {
  if (!m.message_id) return
  const list = loadFavorites(username)
  const idx = list.findIndex((f) => f.message_id === m.message_id)
  if (idx >= 0) {
    list.splice(idx, 1)
  } else {
    list.unshift({
      message_id: m.message_id,
      conversation_id: conversationId.value,
      question: questionBefore(m),
      reply: String(m.content || '').slice(0, 160),
      created_at: new Date().toISOString(),
    })
  }
  saveFavorites(username, list)
  favorites.value = list
}

function onOpenSaved(item) {
  sidePanel.value = 'history'
  if (item?.conversation_id != null) onSelectConversation(item.conversation_id)
}

function normText(s) {
  return String(s || '').replace(/\s+/g, '').trim()
}

function feedbackUpdated(item) {
  if (!item || item.useful !== false) return false
  const q = normText(item.question)
  if (!q) return false
  return notifications.value.some(
    (n) => normText(n.question) === q && String(n.answer || '').trim(),
  )
}

function applyTemplate(text) {
  input.value = text
}

function askQuestion(text) {
  const q = String(text || '').trim()
  if (!q || loading.value) return
  input.value = q
  onSend()
}

function isFaqRead(id) {
  return readIds.value.includes(Number(id))
}

function touchFaqRead(id) {
  readIds.value = markFaqRead(username, id)
}

function openGuide() {
  guideDetail.value = null
  guideAuto.value = guideAutoEnabled(username)
  showGuide.value = true
}

function closeGuide() {
  showGuide.value = false
  guideDetail.value = null
}

function onSuppressChange(e) {
  const suppress = Boolean(e.target.checked)
  guideAuto.value = !suppress
  setGuideAuto(username, !suppress)
}

function onGuideDetail(item) {
  touchFaqRead(item.id)
  guideDetail.value = item
}

function onGuideAsk(item) {
  touchFaqRead(item.id)
  closeGuide()
  askQuestion(item.question)
}

function openLookup() {
  lookupOpen.value = true
  lookupError.value = ''
  lookupResult.value = null
}

async function onLookup() {
  const code = lookupCode.value.trim()
  if (!code || lookupLoading.value) return
  lookupLoading.value = true
  lookupError.value = ''
  lookupResult.value = null
  try {
    lookupResult.value = await lookupErrorCode(code)
  } catch (e) {
    lookupError.value = e.detail || e.message || '查询失败'
  } finally {
    lookupLoading.value = false
  }
}

async function onPreviewDoc(d) {
  docPreview.value = { title: d.title, html: '<p>加载中...</p>', error: '' }
  try {
    const detail = await getDocument(d.document_id)
    docPreview.value = {
      title: detail.title || d.title,
      html: renderDocContent(detail.content || ''),
      error: '',
    }
  } catch (e) {
    docPreview.value = {
      title: d.title,
      html: '',
      error: e.detail || e.message || '预览失败',
    }
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
  background: var(--bg-gradient);
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
  width: 248px;
  flex-shrink: 0;
  padding: 14px 12px;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  background: #1e293b;
  color: #fff;
  overflow: auto;
}
.side-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}
.side-title { font-weight: 600; font-size: 13px; color: #e2e8f0; }
.new-chat {
  border: none;
  background: var(--gradient);
  color: #fff;
  border-radius: var(--radius-sm);
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: filter 0.2s ease, transform 0.15s ease;
}
.new-chat:hover { filter: brightness(1.08); }
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
  display: flex;
  align-items: flex-start;
  gap: 6px;
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  background: transparent;
  border-radius: var(--radius-sm);
  padding: 9px 8px 9px 10px;
  margin-bottom: 4px;
  cursor: pointer;
}
.conv-item:hover { background: rgba(255, 255, 255, 0.06); }
.conv-item.active {
  background: var(--gradient);
  border-color: transparent;
  color: #fff;
}
.conv-main { min-width: 0; flex: 1; }
.conv-del {
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  opacity: 0;
  padding: 0 2px;
  font-size: 14px;
  line-height: 1;
}
.conv-item:hover .conv-del,
.conv-item:focus-within .conv-del {
  opacity: 1;
}
.conv-del:hover { color: var(--color-danger); }
.conv-title {
  font-size: 13px;
  font-weight: 600;
  color: #f8fafc;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-time { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.sidebar .muted { color: #94a3b8; font-size: 12px; }
.muted { color: var(--color-text-secondary); font-size: 12px; font-weight: 400; }
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
  margin-top: 48px;
}
.empty-art { width: 140px; height: 92px; margin-bottom: 8px; }
.placeholder .muted { margin-top: 8px; }

.row {
  display: flex;
  margin-bottom: 14px;
  animation: bubble-in 0.35s ease;
}
@keyframes bubble-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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
  background: var(--gradient);
  color: #fff;
  border-radius: 16px;
  border-bottom-right-radius: 6px;
}
.bubble.user .role { color: rgba(255, 255, 255, 0.8); }
.bubble.assistant {
  background: #fff;
  color: var(--color-text);
  border-radius: 16px;
  border-bottom-left-radius: 6px;
  border-left: 4px solid #667eea;
  box-shadow: var(--shadow);
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
  gap: 6px;
  margin: 0 8px 8px 0;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #fff;
  color: #334155;
  font-size: 12px;
  cursor: pointer;
  box-shadow: var(--shadow);
  max-width: 100%;
}
.cite-ico { width: 16px; height: 16px; color: #667eea; }
.cite-chip span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cite-chip:hover {
  border-color: #667eea;
  color: #667eea;
  background: #eef2ff;
}

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
  padding: 8px 8px 8px 16px;
  border-radius: 24px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow);
}
.input {
  flex: 1;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  padding: 10px 4px;
  border: none;
  border-radius: 24px;
  background: transparent;
}
.input:focus { outline: none; }
.btn {
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--gradient);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.btn:hover:not(:disabled) { filter: brightness(1.06); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.send-btn {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.35);
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}
.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 20px rgba(102, 126, 234, 0.4);
}
.error {
  color: var(--color-danger);
  margin: 0 16px 8px;
}

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
.side-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}
.side-link {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: transparent;
  color: #e2e8f0;
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}
.side-link.on,
.side-link:hover {
  border-color: transparent;
  color: #fff;
  background: var(--gradient);
}
.side-title.block { margin-bottom: 8px; }
.side-card {
  display: block;
  width: 100%;
  text-align: left;
  border: 1px solid var(--color-border);
  background: #fff;
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  margin-bottom: 6px;
  cursor: pointer;
}
.side-card:hover { border-color: var(--color-primary-muted); }
.fb-line { display: flex; gap: 6px; align-items: center; margin-bottom: 4px; }
.fb-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #047857;
}
.fb-tag.down { background: #fef2f2; color: #b91c1c; }
.updated-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 999px;
  background: #eff6ff;
  color: var(--color-primary);
}
.hot {
  margin-top: 18px;
  text-align: left;
}
.hot-title { font-weight: 600; font-size: 14px; margin-bottom: 10px; color: #334155; }
.hot-chip {
  display: inline-flex;
  width: calc(50% - 6px);
  text-align: left;
  margin: 0 6px 8px 0;
  border: 1px solid var(--color-border);
  background: #fff;
  border-radius: 12px;
  padding: 12px 14px;
  cursor: pointer;
  color: #1e293b;
  box-shadow: var(--shadow);
  vertical-align: top;
}
.hot-chip:hover { border-color: var(--color-primary-muted); color: var(--color-primary); }
.templates {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.tpl {
  border: 1px solid var(--color-border);
  background: #fff;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
}
.tpl:hover { border-color: var(--color-primary-muted); color: var(--color-primary); }
.guide-modal { max-width: 560px; max-height: 80vh; overflow: auto; }
.progress { margin: 10px 0 12px; }
.progress-label { font-size: 12px; color: #4b5563; margin-bottom: 6px; }
.progress-track {
  height: 8px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: var(--color-primary);
}
.guide-list { margin-bottom: 12px; }
.guide-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}
.guide-q {
  flex: 1;
  text-align: left;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #111827;
  padding: 0;
}
.guide-q:hover { color: var(--color-primary); }
.read-tag {
  flex-shrink: 0;
  font-size: 11px;
  color: #9ca3af;
}
.read-tag.read { color: #047857; }
.link-mini {
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 12px;
  padding: 0;
}
.guide-detail {
  background: #f8fafc;
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  margin-bottom: 12px;
}
.suppress {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #4b5563;
  margin-bottom: 12px;
}
.lookup-row { display: flex; gap: 8px; margin: 12px 0; }
.lookup-input {
  flex: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
}
.lookup-name { font-weight: 600; margin-bottom: 6px; }
.doc-html { white-space: normal; }
.doc-html :deep(p) { margin: 0 0 8px; }
.modal-close { width: 100%; }
</style>
