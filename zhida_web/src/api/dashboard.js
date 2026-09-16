import { USE_MOCK, request } from './http'
import { MOCK_DASHBOARD, MOCK_GAPS } from './mock/data'

/** GET /api/dashboard */
export async function getDashboard() {
  if (USE_MOCK) {
    const pending_gaps = MOCK_GAPS.filter((g) => g.status === 'pending').length
    return { ...MOCK_DASHBOARD, pending_gaps }
  }
  return request('/api/dashboard')
}
