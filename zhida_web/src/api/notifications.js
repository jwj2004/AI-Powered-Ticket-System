import { USE_MOCK, request } from './http'
import { MOCK_NOTIFICATIONS } from './mock/data'

/** GET /api/notifications */
export async function listNotifications() {
  if (USE_MOCK) {
    return [...MOCK_NOTIFICATIONS]
  }
  return request('/api/notifications')
}

/** POST /api/notifications/{id}/read */
export async function markNotificationRead(id) {
  if (USE_MOCK) {
    return { ok: true }
  }
  return request(`/api/notifications/${id}/read`, { method: 'POST' })
}
