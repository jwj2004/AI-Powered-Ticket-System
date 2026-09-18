/**
 * GET /api/logs
 * 后端未就绪，固定走 mock。
 */
import { MOCK_LOGS } from './mock/data'

export async function listLogs() {
  return MOCK_LOGS.map((row) => ({ ...row }))
}
