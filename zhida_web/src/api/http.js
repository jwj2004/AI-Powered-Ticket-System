/**
 * HTTP 封装：原生 fetch + Bearer
 * 默认走真后端；本地纯前端演示时可把 USE_MOCK 改为 true
 */
import { getToken, clearAuth } from './authStorage'

export const API_BASE = 'http://127.0.0.1:8000'

/** false = 真后端；true = 前端 mock */
export const USE_MOCK = false

export async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers || {}),
  }

  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (resp.status === 401 && !options.skipAuthRedirect) {
    clearAuth()
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    }
  }

  const data = await resp.json().catch(() => ({}))
  if (!resp.ok) {
    const err = new Error(data.detail || `请求失败（${resp.status}）`)
    err.status = resp.status
    err.detail = data.detail
    throw err
  }
  return data
}
