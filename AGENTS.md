# 「知答」B 模块 · Cursor 协作说明

> 配套文档：《知答-MVP-工单智能副驾-开发文档》《接口契约》《团队分工》。

---

## 一、项目一句话

「知答」是 SaaS 售后工单智能副驾 MVP：一线客服在工单页面唤起前端浮层（C 用 Vue3 实现），粘贴客户原话，系统返回错误码释义 + 历史解法 + 可复制的答复草稿；证据不足时明说"没把握"，绝不硬编。

## 二、我的角色（B · 草稿生成后端）

三人并行开发，契约 D1 已冻结、不再改。我只管**草稿生成**这一条线：

| 角色 | 负责 | 与我相关 |
|------|------|---------|
| A · 数据检索后端 | 错误码秒查、向量召回、客户上下文、埋点表 | **我调用 A 的 `/api/retrieve`** |
| **B · 我** | **LLM prompt、草稿生成、"无引用不输出"硬规则、引用拼接** | `/api/draft` |
| C · 前端与工程 | FastAPI 骨架、**Vue3 前端浮层**、部署 | **C 调用我的 `/api/draft`** |

## 三、技术栈（已定，不要擅自改）

- Python 3.10 + FastAPI + Uvicorn
- LLM：DeepSeek Chat（或 Qwen），走 OpenAI 兼容接口
- 编排：**线性 pipeline** `retrieve → build_context → llm_generate`，一个函数调一个函数，不引入 LangGraph
- 向量检索/数据层在 A 手里，我不直接碰数据库
- 前端由 C 负责：**Vue3 + Vite**，调我的 `POST /api/draft`。我只需保证 FastAPI 开好 CORS（白名单含 Vue 开发地址 `http://localhost:5173`），接口契约不变
- 全部同步返回，不做 SSE；超时 10 秒

## 四、我负责的接口：`POST /api/draft`（契约冻结）

**Request**
```json
{
  "raw_text": "客户说已经微信付了198块钱，但是后台订单一直是待支付",
  "customer_id": "C003"   // 可空，解析不到就传 null
}
```

**Response 200（证据充分）**
```json
{
  "query_id": "q_20260915_abc123",   // ← 必带！C 复制草稿时要拿它调 /api/feedback
  "error_code": "PAY_CALLBACK_TIMEOUT",
  "evidence": [
    { "ticket_id": "T20260715001", "summary": "同现象：微信付款后订单待支付..." }
  ],
  "draft": "您好，已为您核实该笔订单。您当前店铺版本 v3.8.5...",
  "confidence": "high"
}
```

**Response 200（证据不足，"宁可不答"）**
```json
{
  "query_id": "q_20260915_abc123",
  "error_code": null,
  "evidence": [],
  "draft": null,
  "confidence": "low",
  "message": "未找到可靠依据，建议转二线处理"
}
```

字段约束（不可违反）：

| 字段 | 规则 |
|------|------|
| `query_id` | 每次调用生成唯一 ID（如 `q_日期_随机串`），必带 |
| `error_code` | 命中错误码返回 code，否则 `null`（不是 `""`） |
| `evidence` | 相似工单摘要，最多 3 条；没找到就是空数组 |
| `evidence[].summary` | 一句话摘要，**不要把整段 solution 塞进来** |
| `draft` | `confidence=low` 时**必须为 null** |
| `confidence` | 只有 `"high"` / `"low"` 两个值，禁止 `"medium"` |
| `message` | 只有 `confidence=low` 时才有 |

## 五、我调用的接口：`POST /api/retrieve`（A 实现，我不对外）

**Request**
```json
{ "query": "客户说付了钱订单没更新", "customer_id": "C003", "top_k": 3 }
```

**Response 200**
```json
{
  "error_code": "PAY_CALLBACK_TIMEOUT",   // A 从客户原话识别，识别不到就是 null
  "tickets": [
    { "ticket_id": "T20260715001", "solution_text": "...", "score": 0.87 }
  ]
}
```

> D2 阶段 A 会先返回写死的 3 条假证据，我用假数据把"证据→草稿"链路跑通；D3 再接真实检索。所以我的客户端调用要封装好，只留一个 `retrieve(query, customer_id, top_k)` 接口，方便切换 mock/真实。

## 六、通用契约约定（代码里必须体现）

- 字段命名 **snake_case**
- 时间用 ISO 字符串，不用时间戳
- 空值用 JSON `null`，**不用空字符串**
- 错误返回统一 `{"detail": "错误说明"}` + 4xx/5xx，不在 200 里塞 error
- 全部 UTF-8、同步返回

## 七、核心业务规则（比代码更重要的红线）

1. **无引用不输出**：检索为空或低置信 → 不返回 draft，只回 `confidence=low + message="未找到可靠依据，建议转二线处理"`。**宁可不说，绝不编造。**
2. **错误码命中优先走结构化 solution**：A 返回 `error_code` 时，`error_code` 表的 `solution` 字段本身就是高质量话术——**直接以它为主生成草稿，不靠 LLM 自由发挥**。这是质量兜底，也是最快路径。
3. **草稿必须带引用**：草稿里出现的每个事实，都要能在 `evidence` 里找到来源；客户版本号这类个性化信息来自客户上下文，也要说明来源。
4. **引用拼接规范**：草稿结构 = 客套开头（带客户版本号）→ 问题核实结论 → 解决步骤（来自 evidence/solution）→ 收尾。不要把整段 solution 原样塞进 evidence。
5. **置信度判定**：只有 high/low。命中错误码或高质量相似工单 → high；否则 low。

## 八、建议的代码结构（可按你实际仓库调整）

```
backend/
├── main.py                  # FastAPI 入口（C 维护骨架，你只挂路由）
├── draft/
│   ├── router.py            # POST /api/draft 路由 + Pydantic 请求/响应模型
│   ├── service.py           # 生成流水线：retrieve → build_context → llm_generate
│   ├── prompts.py           # 2 套 prompt：①错误码命中版 ②纯相似工单版
│   ├── rules.py             # "无引用不输出"硬规则、置信度判定
│   └── cite.py              # evidence → 草稿的引用拼接
├── clients/
│   └── retrieve_client.py   # 封装 A 的 /api/retrieve（mock/真实可切换）
└── config.py                # LLM 配置、超时、日志
```

## 九、开发节奏（照这个顺序让 Cursor 干活）

| 天 | 任务 | 完成标准 |
|----|------|---------|
| D1 | 写 2 套 prompt（错误码命中版 / 纯相似工单版），先跑 10 个例子看效果 | prompt 能产出结构合理的草稿 |
| D2 | 调 `/api/retrieve` 的 mock，用假证据把"证据→草稿"链路跑通 | 不接真实检索也能返回完整草稿 |
| D3 | 接 A 的真实检索 + 客户版本号 + 引用拼接，完整实现 `/api/draft` | 端到端可用 |
| D4 | "无引用不输出"硬规则 + 置信度判定 + 单元测试 | 问库里没有的问题必须说"没把握" |
| D5 | 根据 A 的 30 条回灌评测结果调 prompt、调硬规则阈值 | 草稿"改两句就能发"比例 ≥ 50% |

## 十、和 Cursor 协作的固定开场白（直接复制）

**首次启动**：
> 请先阅读项目根目录的 AGENTS.md（或我粘贴的说明），我们开始开发「知答」项目的 B 模块（草稿生成后端）。我负责 POST /api/draft，内部调用 A 的 POST /api/retrieve，接口契约已冻结。当前进度：D1，先写两套 prompt 模板（错误码命中版 / 纯相似工单版），并用 10 个示例问题跑一遍看效果。

**写代码前强调约束**：
> 严格遵守接口契约：字段 snake_case、空值用 null 不用空字符串、confidence 只有 high/low、confidence=low 时 draft 必须为 null、错误统一返回 {"detail": "..."}。

**实现硬规则时**：
> 实现"无引用不输出"硬规则：当检索结果为空或置信度低时，必须返回 confidence=low、draft=null、evidence=[]、message="未找到可靠依据，建议转二线处理"，绝对不允许编造内容。

**单步任务模板**：
> 在 backend/draft/ 下实现 service.py 的生成流水线（retrieve → build_context → llm_generate），调用 clients/retrieve_client.py，输出字段严格匹配 /api/draft 契约。写完给我看代码和边界情况说明。

## 十一、Cursor 使用技巧

1. **项目规则二选一**：整仓库用根目录 `AGENTS.md`；只想约束 B 模块就在 `backend/` 下建 `.cursor/rules/` 目录写规则文件（Cursor 会按目录生效）。
2. **用 `@` 引用文件**：让 Cursor 读 `接口契约.md`、`retrieve_client.py` 再动手，不要让它凭印象写。
3. **分步推进，别一次全要**：先契约/骨架 → 再单接口 → 再硬规则 → 再测试，每步让它自检一遍契约字段。
4. **让它先讲方案再写码**：复杂逻辑（如置信度判定）先问它"打算怎么设计"，确认后再写。
5. **测试写进规则**：要求每个接口带单元测试，D4 验收时会用 30 条回灌数据卡硬规则。
6. **契约变更走群里**：接口契约冻结，Cursor 想改字段名/类型时一律拒绝，提示走三人 review 流程。
#（注：内容由AI生成）
