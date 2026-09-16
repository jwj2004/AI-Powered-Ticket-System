import { USE_MOCK, request } from './http'
import { MOCK_GAPS } from './mock/data'

/** GET /api/gaps */
export async function listGaps() {
  if (USE_MOCK) {
    return [...MOCK_GAPS]
  }
  return request('/api/gaps')
}

/** POST /api/gaps/{gap_id}/resolve */
export async function resolveGap(gapId, { answer, document_id = null }) {
  if (USE_MOCK) {
    return { ok: true, notified_user_id: 3 }
  }
  return request(`/api/gaps/${gapId}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ answer, document_id }),
  })
}
