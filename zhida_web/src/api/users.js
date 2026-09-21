import { USE_MOCK, request } from './http'
import { getUsername } from './authStorage'
import {
  MOCK_USERS,
  MOCK_PENDING_USERS,
  MOCK_ACTIVE_USERS,
  MOCK_REJECTED_USERS,
  MOCK_DISABLED_USERS,
  MOCK_DISABLED_USER_IDS,
  pushMockLog,
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

/** GET /api/users?status=active */
export async function listActiveUsers() {
  if (USE_MOCK) {
    return MOCK_ACTIVE_USERS.map((u) => ({ ...u, status: 'active' }))
  }
  const data = await request('/api/users?status=active')
  return normalizeList(data)
}

/** GET /api/users?status=rejected */
export async function listRejectedUsers() {
  if (USE_MOCK) {
    return MOCK_REJECTED_USERS.map((u) => ({ ...u }))
  }
  const data = await request('/api/users?status=rejected')
  return normalizeList(data)
}

/** GET /api/users?status=disabled */
export async function listDisabledUsers() {
  if (USE_MOCK) {
    return MOCK_DISABLED_USERS.map((u) => ({ ...u }))
  }
  const data = await request('/api/users?status=disabled')
  return normalizeList(data)
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
    MOCK_REJECTED_USERS.unshift({
      id: u.id,
      username: u.username,
      role: u.role,
      status: 'rejected',
      created_at: u.created_at || new Date().toISOString().slice(0, 19),
    })
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

/** PATCH /api/users/{id}  body: { role } */
export async function updateRole(id, role) {
  if (USE_MOCK) {
    const num = Number(id)
    const me = getUsername()
    const u = MOCK_ACTIVE_USERS.find((x) => x.id === num)
    if (!u) {
      const err = new Error('用户不存在')
      err.detail = '用户不存在'
      throw err
    }
    if (me && u.username === me) {
      const err = new Error('不能修改自己的角色')
      err.detail = '不能修改自己的角色'
      throw err
    }
    if (!['admin', 'ops', 'newbie'].includes(role)) {
      const err = new Error('role 必须是 admin/ops/newbie')
      err.detail = 'role 必须是 admin/ops/newbie'
      throw err
    }
    u.role = role
    const mu = MOCK_USERS[u.username]
    if (mu) mu.role = role
    return { ok: true }
  }
  return request(`/api/users/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ role }),
  })
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

/**
 * POST /api/users/{id}/disable
 */
export async function disableUser(id) {
  if (USE_MOCK) {
    const num = Number(id)
    const me = getUsername()
    const active = MOCK_ACTIVE_USERS.find((u) => u.id === num)
    if (active && me && active.username === me) {
      const err = new Error('不能禁用当前登录账号')
      err.detail = '不能禁用当前登录账号'
      throw err
    }
    if (MOCK_DISABLED_USER_IDS.has(num)) {
      const err = new Error('该用户已禁用')
      err.detail = '该用户已禁用'
      throw err
    }
    MOCK_DISABLED_USER_IDS.add(num)
    const idx = MOCK_ACTIVE_USERS.findIndex((u) => u.id === num)
    const moved = idx >= 0 ? MOCK_ACTIVE_USERS.splice(idx, 1)[0] : active
    if (moved) {
      MOCK_DISABLED_USERS.unshift({ ...moved, status: 'disabled' })
    }
    const mu = Object.values(MOCK_USERS).find((u) => u.id === num)
    if (mu) mu.status = 'disabled'
    pushMockLog({
      operator: me || 'admin',
      action: '禁用用户',
      detail: moved?.username || mu?.username || `用户#${num}`,
    })
    return { ok: true, status: 'disabled' }
  }
  return request(`/api/users/${id}/disable`, { method: 'POST' })
}

/** POST /api/users/{id}/enable — 已拒绝重新同意 / 已禁用启用 */
export async function enableUser(id) {
  if (USE_MOCK) {
    const num = Number(id)
    let moved = null
    const ri = MOCK_REJECTED_USERS.findIndex((u) => u.id === num)
    if (ri >= 0) moved = MOCK_REJECTED_USERS.splice(ri, 1)[0]
    const di = MOCK_DISABLED_USERS.findIndex((u) => u.id === num)
    if (!moved && di >= 0) moved = MOCK_DISABLED_USERS.splice(di, 1)[0]
    if (!moved) {
      const err = new Error('用户状态无法启用')
      err.detail = '用户状态无法启用'
      throw err
    }
    MOCK_DISABLED_USER_IDS.delete(num)
    const active = {
      id: moved.id,
      username: moved.username,
      role: moved.role,
      status: 'active',
      created_at: moved.created_at || new Date().toISOString().slice(0, 19),
    }
    MOCK_ACTIVE_USERS.unshift(active)
    const mu = MOCK_USERS[moved.username]
    if (mu) mu.status = 'active'
    return { ok: true }
  }
  return request(`/api/users/${id}/enable`, { method: 'POST' })
}
