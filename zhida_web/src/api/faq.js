import { USE_MOCK, request } from './http'
import { MOCK_FAQ } from './mock/data'

/** GET /api/faq */
export async function listFaq() {
  if (USE_MOCK) {
    return [...MOCK_FAQ]
  }
  return request('/api/faq')
}

/** POST /api/faq */
export async function publishFaq({ question, answer, gap_id }) {
  if (USE_MOCK) {
    return { id: 2, ok: true }
  }
  return request('/api/faq', {
    method: 'POST',
    body: JSON.stringify({ question, answer, gap_id }),
  })
}
