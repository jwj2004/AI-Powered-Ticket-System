import { USE_MOCK, request } from './http'
import { MOCK_DASHBOARD } from './mock/data'

/** GET /api/dashboard */
export async function getDashboard() {
  if (USE_MOCK) {
    return { ...MOCK_DASHBOARD }
  }
  return request('/api/dashboard')
}
