/**
 * 文档审批。后端未就绪，固定走 mock。
 */
import { getUsername } from './authStorage'
import { MOCK_PENDING_DOCS, pushMockLog } from './mock/data'

function fail(detail) {
  const err = new Error(detail)
  err.detail = detail
  throw err
}

/** GET /api/documents/pending */
export async function listPendingDocs() {
  return MOCK_PENDING_DOCS
    .filter((d) => d.status === 'pending')
    .map((d) => ({ ...d }))
}

/** POST /api/documents/{id}/approve */
export async function approveDoc(id) {
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

/** POST /api/documents/{id}/reject */
export async function rejectDoc(id) {
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
