/**
 * 本地打字机：按字回调，SSE 就绪后可换成流式推送
 * @param {string} text
 * @param {(partial: string) => void} onTick
 * @param {{ interval?: number, shouldContinue?: () => boolean }} options
 */
export async function typewrite(text, onTick, options = {}) {
  const full = text ?? ''
  const interval = options.interval ?? 18
  const shouldContinue = options.shouldContinue || (() => true)

  if (!full) {
    onTick('')
    return
  }

  for (let i = 1; i <= full.length; i++) {
    if (!shouldContinue()) return
    onTick(full.slice(0, i))
    await new Promise((r) => setTimeout(r, interval))
  }
}
