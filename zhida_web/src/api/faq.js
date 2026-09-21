import { USE_MOCK, request } from './http'
import { MOCK_FAQ } from './mock/data'

/** GET /api/faq */
export async function listFaq() {
  if (USE_MOCK) {
    return MOCK_FAQ.map((f) => ({ ...f }))
  }
  return request('/api/faq')
}

/** POST /api/faq */
export async function publishFaq({ question, answer, gap_id }) {
  if (USE_MOCK) {
    const id = Math.max(0, ...MOCK_FAQ.map((f) => f.id)) + 1
    MOCK_FAQ.unshift({
      id,
      question,
      answer,
      gap_id: gap_id == null || gap_id === '' ? null : Number(gap_id),
    })
    return { id, ok: true }
  }
  return request('/api/faq', {
    method: 'POST',
    body: JSON.stringify({ question, answer, gap_id }),
  })
}

/** PUT /api/faq/{id}  body: { question, answer } */
export async function updateFaq(id, { question, answer }) {
  if (USE_MOCK) {
    const item = MOCK_FAQ.find((f) => f.id === Number(id))
    if (!item) {
      const err = new Error('FAQ 不存在')
      err.detail = 'FAQ 不存在'
      throw err
    }
    item.question = question
    item.answer = answer
    return { ok: true }
  }
  return request(`/api/faq/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ question, answer }),
  })
}

/** DELETE /api/faq/{id} */
export async function deleteFaq(id) {
  if (USE_MOCK) {
    const idx = MOCK_FAQ.findIndex((f) => f.id === Number(id))
    if (idx < 0) {
      const err = new Error('FAQ 不存在')
      err.detail = 'FAQ 不存在'
      throw err
    }
    MOCK_FAQ.splice(idx, 1)
    return { ok: true }
  }
  return request(`/api/faq/${id}`, { method: 'DELETE' })
}
