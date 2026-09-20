# 「知答」B 模块 · Cursor 协作说明（完整版）

> 配套文档：《知答-完整版-开发文档》《接口契约(2).md》（v3）。
> 项目已从工单副驾改为企业知识库问答 Agent。B 负责生成与编排，不改 A/C 目录。

## 一、我的角色（B · 生成与编排）

| 角色 | 负责 | 与我相关 |
|------|------|---------|
| A · 数据与检索 | JWT 正式用户、文档上传/切块/FAISS、lookup | 我调用 A 的检索与 `/api/lookup`；A 未就绪时用 mock 文档块 |
| **B · 我** | **LangGraph 五节点、/api/chat、多轮与跨会话、缺口闭环、SSE、混合检索** | chat / conversations / feedback / gaps.resolve / notifications |
| C · 前端与工程 | 登录页、问答页、管理后台 | C 调我的 `/api/chat`（JSON 或 SSE），请求头带 JWT |

## 二、技术栈

- Python 3.10 + FastAPI + LangGraph
- LLM：DeepSeek（OpenAI 兼容）；无 Key 时模板拼接
- 会话/缺口/通知/热门缓存：B 本地 SQLite（`DATABASE_PATH`）
- 向量检索在 A；B 侧做查询改写、BM25+向量 RRF、cross-encoder 重排
- `POST /api/chat` 默认 SSE（meta / token / done）；`Accept: application/json` 或 `stream=false` 时同步 JSON
- 除 `/api/auth/login` 与 `/api/health` 外需要 `Authorization: Bearer <token>`
- `confidence` 为 `high` / `medium` / `low`；空值用 `null`
- 角色：`admin` / `ops` / `newbie`
- JWT 密钥与 A 统一为 `zhida-jwt-shared-2026`（`JWT_SECRET` / `SHARED_JWT_SECRET`），不要另起一套

## 三、B 对外接口（契约 v3）

- `POST /api/auth/login` — 仅供 B 独立联调的种子账号（admin/ops/newbie）
- `POST /api/chat` — 实现只在 `app/api/chat.py`（默认 SSE：`meta` → `token*` → `done`；`Accept: application/json` 或 `stream=false` 时同步 JSON）。`backend/routers.py` 不再注册该路径。
- `POST /api/feedback` — `{ message_id, useful }`
- `GET /api/conversations`
- `GET /api/conversations/{id}/messages`
- `GET /api/gaps`（admin）→ `{ total, items }`
- `POST /api/gaps/{gap_id}/resolve`（admin，补答案后通知原提问者；若带 document_id 则通知 A 重新向量化）
- `GET /api/notifications` → `{ total, unread, items }`
- `POST /api/notifications/{id}/read`

证据不足时 `reply` 固定为：「这个问题我没找到可靠依据，已记录，管理员补全后会通知你。」

## 四、LangGraph 节点

路由 → 检索（改写 + 混合召回 + 重排）→ 质量 → 生成 → 反馈

不要改契约字段名。不要修改 A、C 文件夹。
