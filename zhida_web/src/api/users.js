import { USE_MOCK, request } from './http'
import {
  MOCK_USERS,
  MOCK_PENDING_USERS,
  MOCK_ACTIVE_USERS,
} from './mock/data'

function normalizeList(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  if (Array.isArray(data?.users)) return data.users
  return []
}

/** GET /api/users/pending */
export async function listPendingUsers() {
  if (USE_MOCK) {
    return MOCK_PENDING_USERS.map((u) => ({ ...u }))
  }
  const data = await request('/api/users/pending')
  return normalizeList(data)
}

/** GET /api/users — 已通过（active）用户列表 */
export async function listActiveUsers() {
  if (USE_MOCK) {
    return MOCK_ACTIVE_USERS.map((u) => ({ ...u }))
  }
  const data = await request('/api/users')
  return normalizeList(data).filter((u) => !u.status || u.status === 'active')
}

/** POST /api/users/{id}/approve */
export async function approveUser(id) {
  if (USE_MOCK) {
    const idx = MOCK_PENDING_USERS.findIndex((u) => u.id === Number(id))
    if (idx < 0) {
      const err = new Error('用户不存在')
      err.detail = '用户不存在'
      throw err
    }
    const [u] = MOCK_PENDING_USERS.splice(idx, 1)
    const active = {
      id: u.id,
      username: u.username,
      role: u.role,
      status: 'active',
      created_at: u.created_at || new Date().toISOString().slice(0, 19),
    }
    MOCK_ACTIVE_USERS.unshift(active)
    const mu = MOCK_USERS[u.username]
    if (mu) mu.status = 'active'
    else {
      MOCK_USERS[u.username] = {
        id: u.id,
        username: u.username,
        password: '123456',
        role: u.role,
        status: 'active',
      }
    }
    return { ok: true }
  }
  return request(`/api/users/${id}/approve`, { method: 'POST' })
}

/** POST /api/users/{id}/reject */
export async function rejectUser(id) {
  if (USE_MOCK) {
    const idx = MOCK_PENDING_USERS.findIndex((u) => u.id === Number(id))
    if (idx < 0) {
      const err = new Error('用户不存在')
      err.detail = '用户不存在'
      throw err
    }
    const [u] = MOCK_PENDING_USERS.splice(idx, 1)
    const mu = MOCK_USERS[u.username]
    if (mu) mu.status = 'rejected'
    else {
      MOCK_USERS[u.username] = {
        id: u.id,
        username: u.username,
        password: '123456',
        role: u.role,
        status: 'rejected',
      }
    }
    return { ok: true }
  }
  return request(`/api/users/${id}/reject`, { method: 'POST' })
}

/** POST /api/users/{id}/make-admin */
export async function makeAdmin(id) {
  if (USE_MOCK) {
    const u = MOCK_ACTIVE_USERS.find((x) => x.id === Number(id))
    if (!u) {
      const err = new Error('用户不存在')
      err.detail = '用户不存在'
      throw err
    }
    u.role = 'admin'
    const mu = MOCK_USERS[u.username]
    if (mu) mu.role = 'admin'
    return { ok: true }
  }
  return request(`/api/users/${id}/make-admin`, { method: 'POST' })
}
