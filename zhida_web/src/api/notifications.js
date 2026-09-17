import { USE_MOCK, request } from './http'
import { MOCK_NOTIFICATIONS } from './mock/data'

/**
 * GET /api/notifications
 * 真后端：{ total, unread, items }
 * 对外统一：{ items, unread, total }
 */
export async function listNotifications() {
  if (USE_MOCK) {
    const items = MOCK_NOTIFICATIONS.map((n) => ({ ...n }))
    return {
      items,
      unread: items.filter((n) => !n.read).length,
      total: items.length,
    }
  }
  const data = await request('/api/notifications')
  const items = (data?.items || []).map((n) => ({
    ...n,
    // 后端字段是 id，前端铃铛用 notification_id
    notification_id: n.notification_id ?? n.id,
  }))
  return {
    items,
    unread: data?.unread ?? items.filter((n) => !n.read).length,
    total: data?.total ?? items.length,
  }
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
  const { unread } = await listNotifications()
  return unread
}
