import { USE_MOCK, request } from './http'
import { MOCK_CONVERSATIONS } from './mock/data'

let mockConversationId = 1
let mockMessageId = 100

/**
 * POST /api/chat
 * 前端只 mock chat，不再调 /api/draft
 */
export async function chat({ message, conversation_id = null }) {
  if (USE_MOCK) {
    const cid = conversation_id ?? ++mockConversationId
    const mid = ++mockMessageId
    const low = message.includes('没有答案') || message.includes('不知道')

    if (low) {
      return {
        conversation_id: cid,
        reply: '这个问题我没找到可靠依据，已记录，管理员补全后会通知你。',
        citations: [],
        confidence: 'low',
        gap_id: 5,
        message_id: mid,
      }
    }

    return {
      conversation_id: cid,
      reply: '订单导出超时通常是因为一次导出超过 5 万条。建议按周拆分导出，并检查导出任务队列是否堵塞。',
      citations: [
        { document_id: 2, title: '订单导出超时说明', chunk_index: 3 },
      ],
      confidence: 'high',
      message_id: mid,
    }
  }

  return request('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      conversation_id: conversation_id ?? null,
    }),
  })
}

/** POST /api/feedback 新契约：{ message_id, useful } */
export async function sendFeedback({ message_id, useful }) {
  if (USE_MOCK) {
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
    return [...MOCK_CONVERSATIONS]
  }
  return request('/api/conversations')
}

/** GET /api/conversations/{id}/messages */
export async function listMessages(conversationId) {
  if (USE_MOCK) {
    return [
      {
        role: 'user',
        content: '订单导出超时怎么办？',
        created_at: '2026-09-15T14:00:00',
      },
      {
        role: 'assistant',
        content: '订单导出超时通常是因为一次导出超过 5 万条...',
        citations: [
          { document_id: 2, title: '订单导出超时说明', chunk_index: 3 },
        ],
        confidence: 'high',
        message_id: 101,
      },
    ]
  }
  return request(`/api/conversations/${conversationId}/messages`)
}
