/**
 * 文档审批：未审批 = approved === false
 */
import { USE_MOCK, request } from './http'
import { getUsername } from './authStorage'
import { MOCK_PENDING_DOCS, pushMockLog } from './mock/data'

function fail(detail) {
  const err = new Error(detail)
  err.detail = detail
  throw err
}

/** 待审批列表（无独立 pending 接口时从文档列表筛 approved=false） */
export async function listPendingDocs() {
  if (USE_MOCK) {
    return MOCK_PENDING_DOCS
      .filter((d) => d.status === 'pending')
      .map((d) => ({ ...d }))
  }
  const data = await request('/api/documents')
  const items = Array.isArray(data) ? data : data?.items || []
  return items
    .filter((d) => d.approved === false || d.approved === 0)
    .map((d) => ({
      id: d.id,
      title: d.title,
      submitter: d.owner || d.submitter || '',
      submitted_at: d.updated_at || d.submitted_at || '',
      status: 'pending',
    }))
}

/** POST /api/documents/{id}/approve */
export async function approveDoc(id) {
  if (USE_MOCK) {
    const row = MOCK_PENDING_DOCS.find((d) => d.id === Number(id))
    if (!row || row.status !== 'pending') fail('文档不存在或已处理')
    row.status = 'approved'
    pushMockLog({
      operator: getUsername() || 'admin',
      action: '通过文档',
      detail: row.title,
    })
    return { ok: true }
  }
  return request(`/api/documents/${id}/approve`, { method: 'POST' })
}

/** POST /api/documents/{id}/reject */
export async function rejectDoc(id) {
  if (USE_MOCK) {
    const row = MOCK_PENDING_DOCS.find((d) => d.id === Number(id))
    if (!row || row.status !== 'pending') fail('文档不存在或已处理')
    row.status = 'rejected'
    pushMockLog({
      operator: getUsername() || 'admin',
      action: '拒绝文档',
      detail: row.title,
    })
    return { ok: true }
  }
  return request(`/api/documents/${id}/reject`, { method: 'POST' })
}
