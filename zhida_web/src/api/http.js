/**
 * HTTP 封装：原生 fetch + Bearer
 * D1 默认走 mock；接真后端时把 USE_MOCK 改为 false
 */
import { getToken, clearAuth } from './authStorage'

export const API_BASE = 'http://127.0.0.1:8000'

/** D1：true = 前端 mock；A 接口就绪后改为 false */
export const USE_MOCK = true

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

  if (resp.status === 401) {
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
