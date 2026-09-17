import { USE_MOCK, request } from './http'
import { setAuth } from './authStorage'
import { MOCK_USERS, MOCK_DOC_SPACES } from './mock/data'

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
  })
  setAuth(data)
  return data
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
