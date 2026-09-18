/**
 * 文档空间 CRUD。后端未就绪，固定走 mock。
 */
import { getUsername } from './authStorage'
import { MOCK_DOC_SPACES, pushMockLog } from './mock/data'

function fail(detail) {
  const err = new Error(detail)
  err.detail = detail
  throw err
}

/** GET /api/doc-spaces（管理页） */
export async function listManagedSpaces() {
  return MOCK_DOC_SPACES.map((s) => ({
    id: s.id,
    name: s.name,
    description: s.description || '',
  }))
}

/** POST /api/doc-spaces */
export async function createSpace({ name, description }) {
  const title = String(name || '').trim()
  if (!title) fail('请填写空间名称')
  if (MOCK_DOC_SPACES.some((s) => s.name === title)) fail('空间名称已存在')
  const id = Math.max(0, ...MOCK_DOC_SPACES.map((s) => s.id)) + 1
  const row = {
    id,
    name: title,
    description: String(description || '').trim(),
  }
  MOCK_DOC_SPACES.push(row)
  pushMockLog({
    operator: getUsername() || 'admin',
    action: '新增空间',
    detail: title,
  })
  return { ...row }
}

/** DELETE /api/doc-spaces/{id} */
export async function deleteSpace(id) {
  const num = Number(id)
  const idx = MOCK_DOC_SPACES.findIndex((s) => s.id === num)
  if (idx < 0) fail('空间不存在')
  const [removed] = MOCK_DOC_SPACES.splice(idx, 1)
  pushMockLog({
    operator: getUsername() || 'admin',
    action: '删除空间',
    detail: removed.name,
  })
  return { ok: true }
}
