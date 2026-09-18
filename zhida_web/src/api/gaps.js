import { USE_MOCK, request } from './http'
import { getUsername } from './authStorage'
import { MOCK_GAPS, MOCK_MERGED_GAP_IDS, pushMockLog } from './mock/data'

function hideMerged(list) {
  return list.filter((g) => !MOCK_MERGED_GAP_IDS.has(Number(g.gap_id)))
}

/** GET /api/gaps → 真后端为 { total, items }，对外统一返回数组 */
export async function listGaps() {
  if (USE_MOCK) {
    return hideMerged(MOCK_GAPS.map((g) => ({ ...g })))
  }
  const data = await request('/api/gaps')
  const items = Array.isArray(data) ? data : data?.items || []
  // 后端字段是 id，前端页面用 gap_id
  return hideMerged(items.map((g) => ({
    ...g,
    gap_id: g.gap_id ?? g.id,
  })))
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

/**
 * POST /api/gaps/{gap_id}/merge
 * body: { target_gap_id }
 * 后端未就绪，固定走 mock：源缺口从列表消失
 */
export async function mergeGaps(sourceId, targetId) {
  const source = Number(sourceId)
  const target = Number(targetId)
  if (!source || !target) {
    const err = new Error('请选择要合并的缺口')
    err.detail = '请选择要合并的缺口'
    throw err
  }
  if (source === target) {
    const err = new Error('不能与自身合并')
    err.detail = '不能与自身合并'
    throw err
  }
  MOCK_MERGED_GAP_IDS.add(source)
  const idx = MOCK_GAPS.findIndex((g) => g.gap_id === source)
  const removed = idx >= 0 ? MOCK_GAPS.splice(idx, 1)[0] : null
  pushMockLog({
    operator: getUsername() || 'admin',
    action: '合并缺口',
    detail: removed?.question || `#${source} → #${target}`,
  })
  return { ok: true, merged_into: target }
}
