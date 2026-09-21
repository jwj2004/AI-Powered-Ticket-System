/**
 * HTTP 封装：原生 fetch + Bearer
 * 默认走真后端；本地纯前端演示时可把 USE_MOCK 改为 true
 */
import { getToken, clearAuth } from './authStorage'
import { emitNetworkError } from './networkError'

export const API_BASE = 'http://192.168.10.57:8000'

/** false = 真后端；true = 前端 mock */
export const USE_MOCK = false

/** 默认超时（毫秒）；超时也视为网络异常 */
const DEFAULT_TIMEOUT_MS = 30000

export async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers || {}),
  }

  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const timeoutMs = options.timeout ?? DEFAULT_TIMEOUT_MS
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  let resp
  try {
    resp = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    })
  } catch (e) {
    // 断网 / 超时 / 后端未启动：顶部红条，避免白屏
    emitNetworkError()
    const err = new Error('网络异常，请检查后端服务')
    err.network = true
    err.detail = '网络异常，请检查后端服务'
    throw err
  } finally {
    clearTimeout(timer)
  }

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
