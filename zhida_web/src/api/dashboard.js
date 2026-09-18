import { USE_MOCK, request } from './http'
import { MOCK_DASHBOARD, MOCK_GAPS } from './mock/data'

/**
 * GET /api/dashboard
 * 兼容两种结构：
 * 1) 嵌套：questions / documents / gaps / conversations
 * 2) 扁平：total_today / hit_rate / doc_count / pending_gaps / top_questions
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
  const conf = q.confidence_distribution || data?.confidence_distribution || {}

  // 命中率：可能是 0–1 或 0–100
  const rawHit = Number(q.hit_rate ?? data?.hit_rate)
  const hitRate = Number.isNaN(rawHit) ? 0 : rawHit > 1 ? rawHit / 100 : rawHit

  // Top：兼容 title/message_count 与 question/count
  const top_questions = (data?.top_questions || []).map((t) => ({
    question: t.question || t.title || `会话#${t.conversation_id ?? ''}`,
    count: t.count ?? t.message_count ?? 0,
  }))

  // 无 daily_trend：置信度分布 → 会话概览 → Top 提问量（保证左图有柱）
  const confEntries = Object.entries(conf)
  const hasDaily = Array.isArray(data?.daily_trend) && data.daily_trend.length > 0
  const hasConfChart = confEntries.length > 0
  const hasConv =
    (conv.today ?? conv.this_week ?? conv.total) != null &&
    Number(conv.today || 0) + Number(conv.this_week || 0) + Number(conv.total || 0) > 0

  let daily_trend
  let chart_trend_title
  if (hasDaily) {
    daily_trend = data.daily_trend
    chart_trend_title = '近7日趋势'
  } else if (hasConfChart) {
    daily_trend = confEntries.map(([date, count]) => ({
      date: String(date),
      count: Number(count) || 0,
    }))
    chart_trend_title = '置信度分布'
  } else if (hasConv) {
    daily_trend = [
      { date: '今日会话', count: conv.today ?? 0 },
      { date: '本周会话', count: conv.this_week ?? 0 },
      { date: '全部会话', count: conv.total ?? 0 },
    ]
    chart_trend_title = '会话概览'
  } else {
    daily_trend = top_questions.slice(0, 5).map((t) => ({
      date: String(t.question).slice(0, 8),
      count: t.count,
    }))
    chart_trend_title = '热门提问量'
  }

  return {
    total_today: q.total_today ?? data?.total_today ?? 0,
    hit_rate: hitRate,
    doc_count: docs.total ?? data?.doc_count ?? 0,
    pending_gaps: gaps.pending ?? data?.pending_gaps ?? 0,
    top_questions,
    daily_trend,
    chart_trend_title,
  }
}
