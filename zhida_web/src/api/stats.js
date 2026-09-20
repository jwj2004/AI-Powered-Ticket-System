/**
 * 文档引用统计。
 * 真后端：GET /api/stats/doc-citations（字段 citations）。
 * 不用 document.view_count。
 */
import { USE_MOCK, request } from './http'
import { MOCK_DOC_CITATIONS } from './mock/data'

function normalizeStats(rows) {
  return (rows || []).map((x) => ({
    document_id: x.document_id,
    title: x.title,
    citation_count: Number(x.citation_count ?? x.citations ?? 0),
  }))
}

/** GET /api/stats/doc-citations */
export async function listDocCitations() {
  if (USE_MOCK) {
    return normalizeStats(MOCK_DOC_CITATIONS)
  }
  const data = await request('/api/stats/doc-citations')
  const items = Array.isArray(data) ? data : data?.items || []
  return normalizeStats(items)
}

/** 把 stats 结果映射到文档列表。未出现的文档记 0。 */
export function withCitationCounts(docs, stats) {
  const byId = new Map((stats || []).map((x) => [x.document_id, x.citation_count]))
  const byTitle = new Map((stats || []).map((x) => [x.title, x.citation_count]))
  return (docs || []).map((d) => ({
    ...d,
    citation_count: byId.get(d.id) ?? byTitle.get(d.title) ?? 0,
  }))
}

/** 文档引用 Top N */
export async function getCitationTop(limit = 5) {
  const rows = await listDocCitations()
  return [...rows].sort((a, b) => b.citation_count - a.citation_count).slice(0, limit)
}
