/**
 * 网络异常提示：http 层发出，AppRoot 订阅展示顶部红条
 */
const EVENT = 'zhida:network-error'

export function emitNetworkError() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(EVENT))
}

export function onNetworkError(handler) {
  if (typeof window === 'undefined') return () => {}
  window.addEventListener(EVENT, handler)
  return () => window.removeEventListener(EVENT, handler)
}
