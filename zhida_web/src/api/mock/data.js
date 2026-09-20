/** mock 数据，字段对齐 docs/接口契约.md */

export const MOCK_USERS = {
  admin: { id: 1, username: 'admin', password: '123456', role: 'admin', status: 'active' },
  zhangsan: { id: 2, username: 'zhangsan', password: '123456', role: 'ops', status: 'active' },
  lisi: { id: 3, username: 'lisi', password: '123456', role: 'newbie', status: 'active' },
  /** 登录提示联调：账号待审核 */
  wangwu: { id: 10, username: 'wangwu', password: '123456', role: 'ops', status: 'pending' },
  /** 登录提示联调：已被拒绝 */
  zhaoliu: { id: 11, username: 'zhaoliu', password: '123456', role: 'newbie', status: 'rejected' },
}

/** 待审核注册申请（可变） */
export let MOCK_PENDING_USERS = [
  {
    id: 10,
    username: 'wangwu',
    role: 'ops',
    status: 'pending',
    created_at: '2026-09-17T10:00:00',
  },
  {
    id: 12,
    username: 'chenqi',
    role: 'newbie',
    status: 'pending',
    created_at: '2026-09-18T09:30:00',
  },
]

/** 已通过用户（可变；不含 pending/rejected/disabled） */
export let MOCK_ACTIVE_USERS = [
  { id: 1, username: 'admin', role: 'admin', status: 'active', created_at: '2026-09-01T08:00:00' },
  { id: 2, username: 'zhangsan', role: 'ops', status: 'active', created_at: '2026-09-10T08:00:00' },
  { id: 3, username: 'lisi', role: 'newbie', status: 'active', created_at: '2026-09-12T08:00:00' },
]

/** 已拒绝的注册申请 */
export let MOCK_REJECTED_USERS = [
  { id: 11, username: 'zhaoliu', role: 'newbie', status: 'rejected', created_at: '2026-09-16T08:00:00' },
]

/** 已禁用用户 */
export let MOCK_DISABLED_USERS = []

let _nextUserId = 100

export function mockNextUserId() {
  _nextUserId += 1
  return _nextUserId
}

/** 文档空间（可变；空间管理页增删） */
export const MOCK_DOC_SPACES = [
  { id: 1, name: '客服文档', description: '一线客服常用排查手册' },
  { id: 2, name: '运维文档', description: '运维与发布相关说明' },
  { id: 3, name: '新手指南', description: '新人入职与权限申请' },
]

/** 已在本会话禁用的用户 id（真后端列表上叠加状态） */
export const MOCK_DISABLED_USER_IDS = new Set()

/** 已合并掉的缺口 id（列表不再展示） */
export const MOCK_MERGED_GAP_IDS = new Set()

/** 待审批文档 */
export let MOCK_PENDING_DOCS = [
  {
    id: 201,
    title: '退款时效说明（草案）',
    submitter: 'zhangsan',
    submitted_at: '2026-09-17T11:20:00',
    status: 'pending',
  },
  {
    id: 202,
    title: '短信通道切换步骤',
    submitter: 'lisi',
    submitted_at: '2026-09-18T09:05:00',
    status: 'pending',
  },
]

/** 操作日志 */
export let MOCK_LOGS = [
  {
    id: 1,
    created_at: '2026-09-18T09:12:00',
    operator: 'admin',
    action: '上传文档',
    detail: '支付回调超时排查手册',
  },
  {
    id: 2,
    created_at: '2026-09-17T16:40:00',
    operator: 'admin',
    action: '编辑文档',
    detail: '订单导出超时说明',
  },
  {
    id: 3,
    created_at: '2026-09-17T15:02:00',
    operator: 'admin',
    action: '处理缺口',
    detail: '新人怎么申请系统权限？',
  },
  {
    id: 4,
    created_at: '2026-09-16T11:18:00',
    operator: 'admin',
    action: '删除文档',
    detail: '旧版回调地址说明',
  },
]

let _nextLogId = 100

/** 记一条 mock 操作日志 */
export function pushMockLog({ operator, action, detail }) {
  _nextLogId += 1
  MOCK_LOGS.unshift({
    id: _nextLogId,
    created_at: new Date().toISOString().slice(0, 19),
    operator: operator || 'admin',
    action,
    detail: detail || null,
  })
}

/** 文档被引用次数（看板 Top5 / 列表列） */
export const MOCK_DOC_CITATIONS = [
  { document_id: 1, title: '支付回调超时排查手册', citation_count: 28 },
  { document_id: 2, title: '订单导出超时说明', citation_count: 21 },
  { document_id: 3, title: '新人入职 FAQ', citation_count: 14 },
  { document_id: 4, title: '退款流程说明', citation_count: 9 },
  { document_id: 5, title: '短信通道切换指南', citation_count: 6 },
]

/** 可变列表，上传/编辑/删除会改它（会话内 mock） */
export let MOCK_DOCUMENTS = [
  {
    id: 1,
    title: '支付回调超时排查手册',
    space: '客服文档',
    space_id: 1,
    version: 3,
    updated_at: '2026-09-15T10:00:00',
    owner: 'admin',
  },
  {
    id: 2,
    title: '订单导出超时说明',
    space: '运维文档',
    space_id: 2,
    version: 1,
    updated_at: '2026-09-14T09:00:00',
    owner: 'admin',
  },
  {
    id: 3,
    title: '新人入职 FAQ',
    space: '新手指南',
    space_id: 3,
    version: 2,
    updated_at: '2026-09-12T16:30:00',
    owner: 'admin',
  },
]

export const MOCK_DOCUMENT_DETAILS = {
  1: {
    id: 1,
    title: '支付回调超时排查手册',
    content:
      '买家已付款但订单长时间未变成已支付时，先核对回调地址。\n升级到 v4.2 后回调路径变为 /api/v2/pay/notify。',
    space_id: 1,
    version: 3,
  },
  2: {
    id: 2,
    title: '订单导出超时说明',
    content: '一次导出建议不超过 5 万条。超过阈值会触发任务超时，可按周拆分导出。',
    space_id: 2,
    version: 1,
  },
  3: {
    id: 3,
    title: '新人入职 FAQ',
    content: '如何申请权限、如何提交工单、常用系统入口说明。',
    space_id: 3,
    version: 2,
  },
}

export let MOCK_GAPS = [
  {
    gap_id: 5,
    question: '订单导出超时怎么办？',
    user_id: 3,
    username: 'lisi',
    status: 'pending',
    created_at: '2026-09-15T14:00:00',
  },
  {
    gap_id: 6,
    question: '短信通道怎么换？',
    user_id: 2,
    username: 'zhangsan',
    status: 'pending',
    created_at: '2026-09-15T16:20:00',
  },
  {
    gap_id: 7,
    question: '如何开通 API？',
    user_id: 3,
    username: 'lisi',
    status: 'pending',
    created_at: '2026-09-16T08:10:00',
  },
  {
    gap_id: 8,
    question: '新人怎么申请系统权限？',
    user_id: 3,
    username: 'lisi',
    status: 'resolved',
    created_at: '2026-09-13T09:05:00',
  },
]

/** 可变通知列表 */
export let MOCK_NOTIFICATIONS = [
  {
    notification_id: 1,
    gap_id: 5,
    question: '订单导出超时怎么办？',
    answer: '订单导出超过5万条会超时，按周拆分导出即可。',
    read: false,
    created_at: '2026-09-16T09:00:00',
  },
  {
    notification_id: 2,
    gap_id: 6,
    question: '短信通道怎么换？',
    answer: '在「设置-通知」切换供应商并完成验证。',
    read: false,
    created_at: '2026-09-16T10:20:00',
  },
  {
    notification_id: 3,
    gap_id: 7,
    question: '如何开通 API？',
    answer: '联系管理员开通企业版 API 模块。',
    read: true,
    created_at: '2026-09-15T18:00:00',
  },
]

export const MOCK_DASHBOARD = {
  total_today: 45,
  hit_rate: 0.78,
  top_questions: [
    { question: '订单导出超时', count: 8 },
    { question: '支付回调超时', count: 6 },
    { question: '短信通道切换', count: 5 },
    { question: '如何开通 API', count: 4 },
    { question: '新人权限申请', count: 3 },
  ],
  daily_trend: [
    { date: '09-10', count: 28 },
    { date: '09-11', count: 32 },
    { date: '09-12', count: 25 },
    { date: '09-13', count: 40 },
    { date: '09-14', count: 36 },
    { date: '09-15', count: 42 },
    { date: '09-16', count: 45 },
  ],
  doc_count: 32,
  pending_gaps: 5,
}

export let MOCK_FAQ = [
  {
    id: 1,
    question: '订单导出超时怎么办？',
    answer: '一次导出不要超过 5 万条，可按周拆分。',
    gap_id: null,
  },
]

/** 可变会话列表 */
export let MOCK_CONVERSATIONS = [
  {
    conversation_id: 1,
    title: '订单导出超时',
    updated_at: '2026-09-15T14:00:00',
  },
  {
    conversation_id: 2,
    title: '支付回调排查',
    updated_at: '2026-09-14T11:20:00',
  },
  {
    conversation_id: 3,
    title: '新人权限申请',
    updated_at: '2026-09-13T09:05:00',
  },
]

export const MOCK_CONVERSATION_MESSAGES = {
  1: [
    {
      role: 'user',
      content: '订单导出超时怎么办？',
      created_at: '2026-09-15T14:00:00',
    },
    {
      role: 'assistant',
      content:
        '订单导出超时通常是因为一次导出超过 5 万条。建议按周拆分导出，并检查导出任务队列。',
      citations: [
        { document_id: 2, title: '订单导出超时说明', chunk_index: 3 },
      ],
      confidence: 'high',
      message_id: 101,
      created_at: '2026-09-15T14:00:05',
    },
  ],
  2: [
    {
      role: 'user',
      content: '微信付了钱订单还是待支付',
      created_at: '2026-09-14T11:20:00',
    },
    {
      role: 'assistant',
      content:
        '这通常是支付回调超时。请先确认商户后台是否已扣款，再核对回调地址是否与当前版本一致。',
      citations: [
        { document_id: 1, title: '支付回调超时排查手册', chunk_index: 1 },
        { document_id: 1, title: '支付回调超时排查手册', chunk_index: 2 },
      ],
      confidence: 'high',
      message_id: 102,
      created_at: '2026-09-14T11:20:08',
    },
  ],
  3: [
    {
      role: 'user',
      content: '新人怎么申请系统权限？',
      created_at: '2026-09-13T09:05:00',
    },
    {
      role: 'assistant',
      content: '这个问题我没找到可靠依据，已记录，管理员补全后会通知你。',
      citations: [],
      confidence: 'low',
      gap_id: 8,
      message_id: 103,
      created_at: '2026-09-13T09:05:06',
    },
  ],
}

/** 可点击引用时展示的 chunk 片段 */
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
