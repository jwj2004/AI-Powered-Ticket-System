/**
 * GET /api/logs
 */
import { USE_MOCK, request } from './http'
import { MOCK_LOGS } from './mock/data'

export async function listLogs() {
  if (USE_MOCK) {
    return MOCK_LOGS.map((row) => ({ ...row }))
  }
  const data = await request('/api/logs')
  const items = Array.isArray(data) ? data : data?.items || []
  // 后端字段 username → 页面用 operator
  return items.map((row) => ({
    id: row.id,
    created_at: row.created_at,
    operator: row.operator || row.username || '',
    action: row.action || '',
    detail: row.detail || row.resource || null,
  }))
}
