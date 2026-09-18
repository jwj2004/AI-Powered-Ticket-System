import { USE_MOCK, request } from './http'
import { setAuth } from './authStorage'
import {
  MOCK_USERS,
  MOCK_DOC_SPACES,
  MOCK_PENDING_USERS,
  mockNextUserId,
} from './mock/data'

/** POST /api/auth/login */
export async function login(username, password) {
  if (USE_MOCK) {
    const user = MOCK_USERS[username]
    if (!user || user.password !== password) {
      const err = new Error('用户名或密码错误')
      err.status = 401
      err.detail = '用户名或密码错误'
      throw err
    }
    if (user.status === 'pending') {
      const err = new Error('账号待审核')
      err.status = 403
      err.detail = '账号待审核'
      throw err
    }
    if (user.status === 'rejected') {
      const err = new Error('已被拒绝')
      err.status = 403
      err.detail = '已被拒绝'
      throw err
    }
    const data = {
      token: `mock_token_${user.username}`,
      role: user.role,
      username: user.username,
    }
    setAuth(data)
    return data
  }
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    skipAuthRedirect: true,
  })
  setAuth(data)
  return data
}

/**
 * POST /api/auth/register
 * body: { username, password, role }  role = ops | newbie
 */
export async function register({ username, password, role }) {
  if (USE_MOCK) {
    const name = String(username || '').trim()
    if (!name || !password) {
      const err = new Error('用户名和密码不能为空')
      err.detail = '用户名和密码不能为空'
      throw err
    }
    if (role !== 'ops' && role !== 'newbie') {
      const err = new Error('角色必须是 ops 或 newbie')
      err.detail = '角色必须是 ops 或 newbie'
      throw err
    }
    if (MOCK_USERS[name] || MOCK_PENDING_USERS.some((u) => u.username === name)) {
      const err = new Error('用户名已存在')
      err.status = 400
      err.detail = '用户名已存在'
      throw err
    }
    const id = mockNextUserId()
    MOCK_USERS[name] = {
      id,
      username: name,
      password,
      role,
      status: 'pending',
    }
    MOCK_PENDING_USERS.unshift({
      id,
      username: name,
      role,
      status: 'pending',
      created_at: new Date().toISOString().slice(0, 19),
    })
    return { ok: true, message: '申请已提交，等待管理员审核' }
  }
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password, role }),
    skipAuthRedirect: true,
  })
}

/** POST /api/users（仅 admin） */
export async function createUser({ username, password, role }) {
  if (USE_MOCK) {
    return { id: 99, ok: true }
  }
  return request('/api/users', {
    method: 'POST',
    body: JSON.stringify({ username, password, role }),
  })
}

/** GET /api/doc-spaces */
export async function listDocSpaces() {
  if (USE_MOCK) {
    return [...MOCK_DOC_SPACES]
  }
  return request('/api/doc-spaces')
}
