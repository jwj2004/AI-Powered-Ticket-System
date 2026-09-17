import { USE_MOCK, request } from './http'
import { MOCK_DASHBOARD, MOCK_GAPS } from './mock/data'

/**
 * GET /api/dashboard
 * 后端新结构：questions / documents / gaps / top_questions / conversations
 * 对外统一成页面用的扁平字段
 */
export async function getDashboard() {
  if (USE_MOCK) {
    const pending_gaps = MOCK_GAPS.filter((g) => g.status === 'pending').length
    return { ...MOCK_DASHBOARD, pending_gaps }
  }

  const data = await request('/api/dashboard')
  const q = data?.questions || {}
  const docs = data?.documents || {}
  const gaps = data?.gaps || {}
  const conv = data?.conversations || {}
  const conf = q.confidence_distribution || {}

  // 命中率：后端为 0–1
  const rawHit = Number(q.hit_rate)
  const hitRate = Number.isNaN(rawHit) ? 0 : rawHit > 1 ? rawHit / 100 : rawHit

  // Top：title + message_count → question + count
  const top_questions = (data?.top_questions || []).map((t) => ({
    question: t.title || t.question || `会话#${t.conversation_id ?? ''}`,
    count: t.message_count ?? t.count ?? 0,
  }))

  // 无 daily_trend：用置信度分布做柱图数据
  const confEntries = Object.entries(conf)
  const daily_trend =
    confEntries.length > 0
      ? confEntries.map(([date, count]) => ({ date: String(date), count: Number(count) || 0 }))
      : [
          { date: '今日会话', count: conv.today ?? 0 },
          { date: '本周会话', count: conv.this_week ?? 0 },
          { date: '全部会话', count: conv.total ?? 0 },
        ]

  return {
    total_today: q.total_today ?? 0,
    hit_rate: hitRate,
    doc_count: docs.total ?? 0,
    pending_gaps: gaps.pending ?? 0,
    top_questions,
    daily_trend,
    chart_trend_title: confEntries.length > 0 ? '置信度分布' : '会话概览',
  }
}
