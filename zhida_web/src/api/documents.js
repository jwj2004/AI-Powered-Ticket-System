import { USE_MOCK, request } from './http'
import {
  MOCK_DOCUMENTS,
  MOCK_DOCUMENT_DETAIL,
  MOCK_DOC_SPACES,
} from './mock/data'

/** GET /api/documents */
export async function listDocuments() {
  if (USE_MOCK) {
    return [...MOCK_DOCUMENTS]
  }
  return request('/api/documents')
}

/** GET /api/documents/{id} */
export async function getDocument(id) {
  if (USE_MOCK) {
    return { ...MOCK_DOCUMENT_DETAIL, id: Number(id) }
  }
  return request(`/api/documents/${id}`)
}

/** POST /api/documents/upload */
export async function uploadDocument(file, spaceId) {
  if (USE_MOCK) {
    return { id: 3, title: file?.name || 'mock.pdf', chunks: 12 }
  }
  const form = new FormData()
  form.append('file', file)
  form.append('space_id', String(spaceId))
  return request('/api/documents/upload', { method: 'POST', body: form })
}

/** PUT /api/documents/{id} */
export async function updateDocument(id, { title, content, space_id }) {
  if (USE_MOCK) {
    return { id: Number(id), version: 4 }
  }
  return request(`/api/documents/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ title, content, space_id }),
  })
}

/** DELETE /api/documents/{id} */
export async function deleteDocument(id) {
  if (USE_MOCK) {
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
