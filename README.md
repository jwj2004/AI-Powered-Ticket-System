# 知答 - 企业内部知识库智能问答 Agent

基于 RAG 的企业内部知识库智能问答系统，服务客服、运维、新人、管理员四类人群。

让企业内部知识可被自然语言检索，降低新人上手成本，提升客服 / 运维效率。

## 功能特性

- 🤖 **智能问答**：RAG 检索 + DeepSeek LLM 生成 + SSE 流式输出 + 引用来源
- 📚 **文档管理**：上传 / 在线编辑 / 预览 / 版本管理 / 删除 / 审批 / 空间管理
- 🔍 **知识缺口**：答不上来自动记录 → 管理员补文档 → 自动通知提问者
- ❓ **FAQ 管理**：新建 / 编辑 / 删除 / 待确认发布 / 新人引导
- 📊 **数据看板**：问答量 / 命中率 / 热门问题 / 置信度分布 / 引用统计
- 👥 **用户管理**：注册审核 / 角色管理 (admin/ops/newbie) / 禁用 / 恢复 / 已拒绝已禁用 tab
- 🎯 **用户端增强**：新人引导 / 收藏回答 / 错误码直查 / 最近文档 / 我的反馈 / 快捷提问模板 / 学习进度
- 📝 **操作日志**：管理员操作全记录
- 🔐 **权限隔离**：三种角色，不同文档空间权限
- 🐳 **Docker 部署**：一键启动
- 🌐 **局域网访问**：支持多人同时使用

## 技术栈

- **后端**：Python 3.10 + FastAPI + SQLAlchemy + SQLite
- **AI**：BGE-small-zh 向量模型 + FAISS 向量检索 + DeepSeek API + LangGraph 多节点编排
- **前端**：Vue 3 + Vite + Vue Router + WangEditor 富文本 + ECharts
- **认证**：JWT + bcrypt
- **部署**：Docker + docker-compose + nginx

## 快速启动（Docker，推荐）

```bash
git clone https://github.com/jwj2004/AI-Powered-Ticket-System.git
cd AI-Powered-Ticket-System
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY / LLM_API_KEY / JWT_SECRET
docker-compose up -d --build
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/rebuild_doc_index.py
```

访问：

- 前端：http://localhost
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 手动启动

```bash
# 后端
pip install -r requirements.txt
python scripts/init_db.py
python scripts/rebuild_doc_index.py
python main.py

# 前端
cd zhida_web
npm install
npm run dev
```

手动启动时，后端在 http://127.0.0.1:8000，前端开发服务在 http://127.0.0.1:5173。

## 默认账号

| 角色 | 用户名 | 密码 | 权限 |
| --- | --- | --- | --- |
| 管理员 | admin | admin123 | 全部功能 |
| 客服 / 运维 | ops01 | ops123 | 问答 + 客服 / 运维文档 |
| 新人 | newbie01 | newbie123 | 问答 + 新手指南 |

## 项目结构

```
AI-Powered-Ticket-System/
├── app/                    # A：数据与检索
│   ├── api/                # 接口（auth/users/documents/chat/gaps/faq/...）
│   ├── models/             # 数据库模型
│   ├── services/           # 向量检索、文档处理
│   └── core/               # 配置
├── backend/                # B：生成与编排
│   ├── agent/              # LangGraph 编排（路由→检索→质量→生成）
│   ├── config.py           # B 配置
│   └── store.py            # 缓存、数据存储
├── zhida_web/              # C：前端
│   ├── src/
│   │   ├── views/          # 页面（登录/问答/管理后台）
│   │   ├── api/            # 接口层
│   │   ├── router/         # 路由
│   │   └── components/     # 组件
│   └── package.json
├── scripts/                # 脚本（init_db/rebuild_doc_index/...）
├── data/                   # 种子数据（CSV）
├── docs/                   # 开发文档、接口契约
├── docker-compose.yml
├── Dockerfile
├── main.py
├── requirements.txt
└── README.md
```

## 三人分工

| 成员 | 模块 | 职责 |
| --- | --- | --- |
| A | 数据与检索 | 用户 / 文档 / 会话 / 缺口 / FAQ / 看板 接口 + 向量检索 + 数据库 |
| B | 生成与编排 | LangGraph 五节点编排 + LLM 调用 + SSE 流式 + 检索改写 |
| C | 前端与工程 | Vue 全页面 + 管理后台 + 用户端增强 + Docker + 美化 |

## 演示流程

1. 注册新账号 → admin 审核 → 登录
2. 问答：问「支付回调超时怎么处理」→ 看引用来源和流式回答
3. 问一个文档里没有的问题 → 自动记入知识缺口
4. admin 进知识缺口 → 补文档 → 提问者收到通知
5. 文档管理：上传 / 在线编辑 / 预览 / 版本
6. FAQ 管理：新建 / 发布
7. 数据看板：看问答量 / 命中率 / 热门问题
8. 用户管理：改角色 / 禁用 / 恢复
