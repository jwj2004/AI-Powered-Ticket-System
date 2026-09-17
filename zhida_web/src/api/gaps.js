import { USE_MOCK, request } from './http'
import { MOCK_GAPS } from './mock/data'

/** GET /api/gaps → 真后端为 { total, items }，对外统一返回数组 */
export async function listGaps() {
  if (USE_MOCK) {
    return MOCK_GAPS.map((g) => ({ ...g }))
  }
  const data = await request('/api/gaps')
  const items = Array.isArray(data) ? data : data?.items || []
  // 后端字段是 id，前端页面用 gap_id
  return items.map((g) => ({
    ...g,
    gap_id: g.gap_id ?? g.id,
  }))
}

/** POST /api/gaps/{gap_id}/resolve */
export async function resolveGap(gapId, { answer, document_id = null }) {
  if (USE_MOCK) {
    const item = MOCK_GAPS.find((g) => g.gap_id === Number(gapId))
    if (item) {
      item.status = 'resolved'
      item.answer = answer || null
      item.document_id = document_id
      item.resolved_at = new Date().toISOString().slice(0, 19)
    }
    return { ok: true, notified_user_id: item?.user_id ?? 3 }
  }
  return request(`/api/gaps/${gapId}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ answer, document_id }),
  })
}
