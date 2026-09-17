import { USE_MOCK, request } from './http'
import { MOCK_DASHBOARD, MOCK_GAPS } from './mock/data'

/** GET /api/dashboard */
export async function getDashboard() {
  if (USE_MOCK) {
    const pending_gaps = MOCK_GAPS.filter((g) => g.status === 'pending').length
    return { ...MOCK_DASHBOARD, pending_gaps }
  }
  const data = await request('/api/dashboard')
  // 对齐页面字段；后端暂无 doc_count / pending_gaps / daily_trend，先兜底
  const rawHit = Number(data?.hit_rate)
  // 后端 hit_rate 为 0–100；看板组件按 0–1 再 *100 显示
  const hitRate01 = Number.isNaN(rawHit) ? 0 : rawHit > 1 ? rawHit / 100 : rawHit
  return {
    total_today: data?.today_question_count ?? data?.total_today ?? 0,
    hit_rate: hitRate01,
    total_feedback: data?.total_feedback ?? 0,
    top_questions: data?.top_questions || [],
    doc_count: data?.doc_count ?? 0,
    pending_gaps: data?.pending_gaps ?? 0,
    daily_trend: data?.daily_trend || [],
  }
}
