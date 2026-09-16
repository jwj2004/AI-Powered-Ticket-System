import { USE_MOCK, request } from './http'
import { MOCK_NOTIFICATIONS } from './mock/data'

/** GET /api/notifications */
export async function listNotifications() {
  if (USE_MOCK) {
    return MOCK_NOTIFICATIONS.map((n) => ({ ...n }))
  }
  return request('/api/notifications')
}

/** POST /api/notifications/{id}/read */
export async function markNotificationRead(id) {
  if (USE_MOCK) {
    const item = MOCK_NOTIFICATIONS.find((n) => n.notification_id === Number(id))
    if (item) item.read = true
    return { ok: true }
  }
  return request(`/api/notifications/${id}/read`, { method: 'POST' })
}

/** 未读数量（前端铃铛用） */
export async function getUnreadNotificationCount() {
  const list = await listNotifications()
  return list.filter((n) => !n.read).length
}
