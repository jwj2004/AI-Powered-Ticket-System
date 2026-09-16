# 知答 · 企业内部知识库智能问答 Agent

员工登录后自由提问，系统从内部文档检索证据、带引用回答；管理员管理文档、处理知识缺口并查看数据看板。

## 环境要求

- Python 3.10+
- Node.js 18+
- （可选）Docker / Docker Compose

## 本地启动

### 后端

```bash
pip install -r requirements.txt
python scripts/init_db.py
python main.py
```

- 地址：http://127.0.0.1:8000
- Swagger：http://127.0.0.1:8000/docs

### 前端

```bash
cd zhida_web
npm install
npm run dev
```

- 地址：http://127.0.0.1:5173

> 前端默认 `USE_MOCK = true`（见 `zhida_web/src/api/http.js`）。接 A/B 真接口时改为 `false`。

## 演示账号（mock / 种子）

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `123456` | 管理员 |
| `zhangsan` | `123456` | 客服/运维（ops） |
| `lisi` | `123456` | 新人（newbie） |

## Docker 启动

```bash
docker compose up -d --build
```

| 服务 | 地址 |
|------|------|
| 前端（nginx） | http://127.0.0.1 |
| 后端（FastAPI） | http://127.0.0.1:8000 |

SQLite 数据目录挂载：`./db` → 容器 `/app/db`。

## 目录结构

```
AI-Powered-Ticket-System/
├── main.py                 # FastAPI 入口
├── requirements.txt
├── docker-compose.yml
├── Dockerfile              # 后端镜像
├── app/                    # A：数据与检索
├── backend/                # B：草稿/编排（演进中）
├── scripts/                # 建库灌数等脚本
├── data/ / seed_data/      # 种子 CSV
├── db/                     # SQLite（gitignore）
├── docs/                   # 开发文档与接口契约
└── zhida_web/              # C：Vue 前端
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    └── src/
        ├── api/            # 接口层（含 mock）
        ├── components/
        ├── router/
        └── views/          # 登录 / 问答 / 管理后台
```

## 团队分工（简述）

| 角色 | 负责 |
|------|------|
| **A · 数据与检索** | 用户/文档/向量检索、JWT、缺口与看板接口 |
| **B · 生成与编排** | `/api/chat`、LangGraph、无引用不输出 |
| **C · 前端与工程** | Vue 页面、mock 联调、docker-compose、README |

## 核心约定

- 接口契约：`docs/接口契约.md`
- Base URL：`http://127.0.0.1:8000`
- 字段 snake_case；空值用 `null`；错误 `{"detail": "..."}` + 4xx/5xx
- `confidence` 仅 `high` / `low`
