import { USE_MOCK, request } from './http'
import {
  MOCK_DOCUMENTS,
  MOCK_DOCUMENT_DETAILS,
  MOCK_DOC_SPACES,
} from './mock/data'

function formatNow() {
  return new Date().toISOString().slice(0, 19)
}

function spaceName(spaceId) {
  const s = MOCK_DOC_SPACES.find((x) => x.id === Number(spaceId))
  return s ? s.name : '未分类'
}

/** GET /api/documents */
export async function listDocuments() {
  if (USE_MOCK) {
    return MOCK_DOCUMENTS.map((d) => ({ ...d }))
  }
  return request('/api/documents')
}

/** GET /api/documents/{id} */
export async function getDocument(id) {
  if (USE_MOCK) {
    const num = Number(id)
    const detail = MOCK_DOCUMENT_DETAILS[num]
    if (detail) return { ...detail }
    const row = MOCK_DOCUMENTS.find((d) => d.id === num)
    return {
      id: num,
      title: row?.title || '未命名文档',
      content: '',
      space_id: row?.space_id || 1,
      version: row?.version || 1,
    }
  }
  return request(`/api/documents/${id}`)
}

/** POST /api/documents/upload */
export async function uploadDocument(file, spaceId) {
  if (USE_MOCK) {
    const id = Math.max(0, ...MOCK_DOCUMENTS.map((d) => d.id)) + 1
    const title = (file?.name || '未命名文档').replace(/\.[^.]+$/, '') || '未命名文档'
    const now = formatNow()
    const sid = Number(spaceId)
    MOCK_DOCUMENTS.unshift({
      id,
      title,
      space: spaceName(sid),
      space_id: sid,
      version: 1,
      updated_at: now,
      owner: 'admin',
    })
    MOCK_DOCUMENT_DETAILS[id] = {
      id,
      title,
      content: `（mock）已上传文件：${file?.name || ''}`,
      space_id: sid,
      version: 1,
    }
    return { id, title, chunks: 12 }
  }
  const form = new FormData()
  form.append('file', file)
  form.append('space_id', String(spaceId))
  return request('/api/documents/upload', { method: 'POST', body: form })
}

/** PUT /api/documents/{id} */
export async function updateDocument(id, { title, content, space_id }) {
  if (USE_MOCK) {
    const num = Number(id)
    const row = MOCK_DOCUMENTS.find((d) => d.id === num)
    const detail = MOCK_DOCUMENT_DETAILS[num] || {
      id: num,
      title: '',
      content: '',
      space_id: 1,
      version: 1,
    }
    detail.title = title
    detail.content = content
    detail.space_id = Number(space_id)
    detail.version = (detail.version || 1) + 1
    MOCK_DOCUMENT_DETAILS[num] = detail
    if (row) {
      row.title = title
      row.space_id = Number(space_id)
      row.space = spaceName(space_id)
      row.version = detail.version
      row.updated_at = formatNow()
    }
    return { id: num, version: detail.version }
  }
  return request(`/api/documents/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ title, content, space_id }),
  })
}

/** DELETE /api/documents/{id} */
export async function deleteDocument(id) {
  if (USE_MOCK) {
    const num = Number(id)
    const idx = MOCK_DOCUMENTS.findIndex((d) => d.id === num)
    if (idx >= 0) MOCK_DOCUMENTS.splice(idx, 1)
    delete MOCK_DOCUMENT_DETAILS[num]
    return { ok: true }
  }
  return request(`/api/documents/${id}`, { method: 'DELETE' })
}

/** GET /api/documents/{id}/versions */
export async function listDocumentVersions(id) {
  if (USE_MOCK) {
    return [
      { version: 1, created_at: '2026-09-01T10:00:00' },
      { version: 2, created_at: '2026-09-10T10:00:00' },
      { version: 3, created_at: '2026-09-15T10:00:00' },
    ]
  }
  return request(`/api/documents/${id}/versions`)
}

export { MOCK_DOC_SPACES }
