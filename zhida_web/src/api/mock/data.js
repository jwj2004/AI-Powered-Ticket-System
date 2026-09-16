/** D1 mock 数据，字段对齐 docs/接口契约.md */

export const MOCK_USERS = {
  admin: { username: 'admin', password: '123456', role: 'admin' },
  zhangsan: { username: 'zhangsan', password: '123456', role: 'ops' },
  lisi: { username: 'lisi', password: '123456', role: 'newbie' },
}

export const MOCK_DOC_SPACES = [
  { id: 1, name: '客服文档' },
  { id: 2, name: '运维文档' },
  { id: 3, name: '新手指南' },
]

export const MOCK_DOCUMENTS = [
  {
    id: 1,
    title: '支付回调超时排查手册',
    space: '客服文档',
    version: 3,
    updated_at: '2026-09-15T10:00:00',
    owner: 'admin',
  },
  {
    id: 2,
    title: '订单导出超时说明',
    space: '运维文档',
    version: 1,
    updated_at: '2026-09-14T09:00:00',
    owner: 'admin',
  },
]

export const MOCK_DOCUMENT_DETAIL = {
  id: 1,
  title: '支付回调超时排查手册',
  content: '<p>买家已付款但订单长时间未变成已支付时，先核对回调地址。</p>',
  space_id: 1,
  version: 3,
}

export const MOCK_GAPS = [
  {
    gap_id: 5,
    question: '订单导出超时怎么办？',
    user_id: 3,
    username: 'lisi',
    status: 'pending',
    created_at: '2026-09-15T14:00:00',
  },
]

export const MOCK_NOTIFICATIONS = [
  {
    notification_id: 1,
    gap_id: 5,
    question: '订单导出超时怎么办？',
    answer: '订单导出超过5万条会超时，按周拆分导出即可。',
    read: false,
    created_at: '2026-09-16T09:00:00',
  },
]

export const MOCK_DASHBOARD = {
  total_today: 45,
  hit_rate: 0.78,
  top_questions: [{ question: '订单导出超时', count: 8 }],
  doc_count: 32,
  pending_gaps: 5,
}

export const MOCK_FAQ = [
  {
    id: 1,
    question: '订单导出超时怎么办？',
    answer: '一次导出不要超过 5 万条，可按周拆分。',
  },
]

export const MOCK_CONVERSATIONS = [
  {
    conversation_id: 1,
    title: '订单导出超时',
    updated_at: '2026-09-15T14:00:00',
  },
]

/** 可点击引用时展示的 chunk 片段（D2 mock） */
export const MOCK_CITATION_CHUNKS = {
  '2:3': {
    document_id: 2,
    title: '订单导出超时说明',
    chunk_index: 3,
    content:
      '一次导出建议不超过 5 万条。超过阈值会触发任务超时。可按周拆分导出，或在后台「导出任务」查看队列状态。',
  },
  '1:1': {
    document_id: 1,
    title: '支付回调超时排查手册',
    chunk_index: 1,
    content:
      '买家已付款但订单长时间未变成已支付时，先在支付商户后台确认扣款，再核对商城回调地址是否与商户平台一致。',
  },
  '1:2': {
    document_id: 1,
    title: '支付回调超时排查手册',
    chunk_index: 2,
    content:
      '店铺升级到 v4.2 后，回调路径变更为 /api/v2/pay/notify，需在商户平台同步更新。',
  },
}
