/**
 * 简易内容渲染：HTML 原样；Markdown / 纯文本做轻量转换
 * 不引入 marked 等依赖
 */
export function looksLikeHtml(text) {
  if (!text) return false
  return /<\/?[a-z][\s\S]*>/i.test(text)
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** Markdown → 安全 HTML（子集） */
export function markdownToHtml(src) {
  const lines = String(src || '').replace(/\r\n/g, '\n').split('\n')
  const out = []
  let inUl = false
  let inOl = false

  function closeLists() {
    if (inUl) {
      out.push('</ul>')
      inUl = false
    }
    if (inOl) {
      out.push('</ol>')
      inOl = false
    }
  }

  function inline(text) {
    let t = escapeHtml(text)
    t = t.replace(/`([^`]+)`/g, '<code>$1</code>')
    t = t.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    t = t.replace(/\*([^*]+)\*/g, '<em>$1</em>')
    return t
  }

  for (const raw of lines) {
    const line = raw
    const heading = /^(#{1,3})\s+(.+)$/.exec(line)
    if (heading) {
      closeLists()
      const level = heading[1].length
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`)
      continue
    }
    const ul = /^[-*]\s+(.+)$/.exec(line)
    if (ul) {
      if (inOl) {
        out.push('</ol>')
        inOl = false
      }
      if (!inUl) {
        out.push('<ul>')
        inUl = true
      }
      out.push(`<li>${inline(ul[1])}</li>`)
      continue
    }
    const ol = /^(\d+)\.\s+(.+)$/.exec(line)
    if (ol) {
      if (inUl) {
        out.push('</ul>')
        inUl = false
      }
      if (!inOl) {
        out.push('<ol>')
        inOl = true
      }
      out.push(`<li>${inline(ol[2])}</li>`)
      continue
    }
    closeLists()
    if (!line.trim()) {
      out.push('')
      continue
    }
    out.push(`<p>${inline(line)}</p>`)
  }
  closeLists()
  return out.join('\n')
}

/** 统一成可 v-html 的 HTML */
export function renderDocContent(content) {
  if (!content) return '<p class="empty-content">（无内容）</p>'
  if (looksLikeHtml(content)) return content
  return markdownToHtml(content)
}
