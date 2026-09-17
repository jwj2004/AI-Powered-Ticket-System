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
