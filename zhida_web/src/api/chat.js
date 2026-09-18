import { USE_MOCK, request } from './http'
import {
  MOCK_CONVERSATIONS,
  MOCK_CONVERSATION_MESSAGES,
  MOCK_CITATION_CHUNKS,
} from './mock/data'

let mockConversationId = 10
let mockMessageId = 200

function delay(ms = 600) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function formatNow() {
  return new Date().toISOString().slice(0, 19)
}

/**
 * POST /api/chat
 * 前端只 mock chat，不再调 /api/draft
 */
export async function chat({ message, conversation_id = null }) {
  if (USE_MOCK) {
    await delay(700)
    const isNew = conversation_id == null
    const cid = conversation_id ?? ++mockConversationId
    const mid = ++mockMessageId
    const text = message.trim()
    const low =
      text.includes('没有答案') ||
      text.includes('不知道') ||
      text.includes('随便问问')

    let replyPayload
    if (low) {
      replyPayload = {
        conversation_id: cid,
        reply: '这个问题我没找到可靠依据，已记录，管理员补全后会通知你。',
        citations: [],
        confidence: 'low',
        gap_id: 5,
        message_id: mid,
      }
    } else if (text.includes('支付') || text.includes('回调')) {
      replyPayload = {
        conversation_id: cid,
        reply:
          '支付回调超时一般是商户平台未及时通知商城。建议：1）在支付后台确认是否已扣款；2）核对回调地址是否与当前版本一致；3）升级后注意 v4.2 的新回调路径。',
        citations: [
          { document_id: 1, title: '支付回调超时排查手册', chunk_index: 1 },
          { document_id: 1, title: '支付回调超时排查手册', chunk_index: 2 },
        ],
        // 与真后端文档召回对齐：有引用但未到错误码级 high
        confidence: 'medium',
        message_id: mid,
      }
    } else {
      replyPayload = {
        conversation_id: cid,
        reply:
          '订单导出超时通常是因为一次导出超过 5 万条。建议按周拆分导出，并检查导出任务队列是否堵塞。如需追问，可继续说明你们的导出条数和版本。',
        citations: [
          { document_id: 2, title: '订单导出超时说明', chunk_index: 3 },
        ],
        confidence: 'high',
        message_id: mid,
      }
    }

    // 同步写入 mock 会话列表，便于侧边栏刷新
    const now = formatNow()
    if (isNew) {
      MOCK_CONVERSATIONS.unshift({
        conversation_id: cid,
        title: text.slice(0, 20) || '新对话',
        updated_at: now,
      })
      MOCK_CONVERSATION_MESSAGES[cid] = []
    } else {
      const item = MOCK_CONVERSATIONS.find((c) => c.conversation_id === cid)
      if (item) item.updated_at = now
    }
    if (!MOCK_CONVERSATION_MESSAGES[cid]) MOCK_CONVERSATION_MESSAGES[cid] = []
    MOCK_CONVERSATION_MESSAGES[cid].push(
      { role: 'user', content: text, created_at: now },
      {
        role: 'assistant',
        content: replyPayload.reply,
        citations: replyPayload.citations,
        confidence: replyPayload.confidence,
        message_id: replyPayload.message_id,
        gap_id: replyPayload.gap_id ?? null,
        created_at: now,
      },
    )

    return replyPayload
  }

  return request('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      conversation_id: conversation_id ?? null,
    }),
  })
}

/** 点击引用时取 chunk 详情（mock） */
export function getCitationChunk(citation) {
  if (!citation) return null
  const key = `${citation.document_id}:${citation.chunk_index}`
  return (
    MOCK_CITATION_CHUNKS[key] || {
      document_id: citation.document_id,
      title: citation.title,
      chunk_index: citation.chunk_index,
      content: '（mock）暂无该片段正文，接真后端后从文档块接口读取。',
    }
  )
}

/** POST /api/feedback 新契约：{ message_id, useful } */
export async function sendFeedback({ message_id, useful }) {
  if (USE_MOCK) {
    await delay(200)
    return { ok: true }
  }
  return request('/api/feedback', {
    method: 'POST',
    body: JSON.stringify({ message_id, useful }),
  })
}

/** GET /api/conversations */
export async function listConversations() {
  if (USE_MOCK) {
    await delay(150)
    return [...MOCK_CONVERSATIONS].sort((a, b) =>
      (b.updated_at || '').localeCompare(a.updated_at || ''),
    )
  }
  // A/B JWT 未统一前：会话接口 401 不踢登，避免问答页进不去、通知铃铛测不了
  return request('/api/conversations', { skipAuthRedirect: true })
}

/** GET /api/conversations/{id}/messages */
export async function listMessages(conversationId) {
  if (USE_MOCK) {
    await delay(200)
    const id = Number(conversationId)
    const list = MOCK_CONVERSATION_MESSAGES[id] || []
    return list.map((m) => ({
      ...m,
      feedback: null,
      // 兼容 ChatView 气泡字段
      content: m.content,
    }))
  }
  return request(`/api/conversations/${conversationId}/messages`)
}
