/** 用户端本地数据：按用户名分桶，存在 localStorage */

function key(username, name) {
  return `zhida_u:${username || ''}:${name}`
}

function readList(username, name) {
  try {
    const raw = localStorage.getItem(key(username, name))
    const data = raw ? JSON.parse(raw) : []
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

function writeList(username, name, list) {
  localStorage.setItem(key(username, name), JSON.stringify(list))
}

const GUIDE_PENDING = 'zhida_guide_pending'

/** 缺省自动弹出；只有用户勾选「不再自动弹出」才关掉 */
export function guideAutoEnabled(username) {
  return localStorage.getItem(key(username, 'guide_auto')) !== '0'
}

export function setGuideAuto(username, on) {
  localStorage.setItem(key(username, 'guide_auto'), on ? '1' : '0')
}

/** 登录成功时调用：本次登录待弹出引导（刷新同一会话只弹一次，下次登录还会弹） */
export function markGuidePending(username) {
  if (!guideAutoEnabled(username)) {
    sessionStorage.removeItem(GUIDE_PENDING)
    return
  }
  sessionStorage.setItem(GUIDE_PENDING, username || '')
}

export function consumeGuidePending(username) {
  if (sessionStorage.getItem(GUIDE_PENDING) !== (username || '')) return false
  sessionStorage.removeItem(GUIDE_PENDING)
  return guideAutoEnabled(username)
}

export function loadReadFaq(username) {
  return readList(username, 'faq_read').map((id) => Number(id))
}

export function markFaqRead(username, id) {
  const ids = loadReadFaq(username)
  const num = Number(id)
  if (!ids.includes(num)) ids.push(num)
  writeList(username, 'faq_read', ids)
  return ids
}

export function loadFavorites(username) {
  return readList(username, 'favorites')
}

export function saveFavorites(username, list) {
  writeList(username, 'favorites', list)
}

export function loadRecentDocs(username) {
  return readList(username, 'recent_docs')
}

export function saveRecentDocs(username, list) {
  writeList(username, 'recent_docs', list.slice(0, 5))
}

export function loadMyFeedback(username) {
  return readList(username, 'feedback')
}

export function saveMyFeedback(username, list) {
  writeList(username, 'feedback', list)
}
