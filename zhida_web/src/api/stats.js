/**
 * 文档引用统计。后端未就绪，固定走 mock。
 */
import { MOCK_DOC_CITATIONS } from './mock/data'

/** 给文档列表补 citation_count（按 id，其次按标题） */
export function withCitationCounts(docs) {
  const byId = new Map(MOCK_DOC_CITATIONS.map((x) => [x.document_id, x.citation_count]))
  const byTitle = new Map(MOCK_DOC_CITATIONS.map((x) => [x.title, x.citation_count]))
  return (docs || []).map((d) => ({
    ...d,
    citation_count: byId.get(d.id) ?? byTitle.get(d.title) ?? d.citation_count ?? 0,
  }))
}

/** GET /api/stats/doc-citations → Top N */
export async function getCitationTop(limit = 5) {
  return [...MOCK_DOC_CITATIONS]
    .sort((a, b) => b.citation_count - a.citation_count)
    .slice(0, limit)
    .map((x) => ({ ...x }))
}
