# 知答 MVP - A 模块（数据检索后端）

> 负责：建表灌数据、错误码秒查、向量召回、客户上下文、埋点表
> 目标：让系统"查得到、查得准"

## 技术栈

- **Web 框架**: FastAPI 0.112.2
- **ORM**: SQLAlchemy 2.0
- **数据库**: SQLite（本地）/ MySQL（部署）
- **向量检索**: FAISS + sentence-transformers (BGE)
- **日志**: loguru
- **配置**: pydantic-settings + .env

## 快速开始

```powershell
# 1. 创建虚拟环境
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. D1 一键初始化（建表+灌数据+向量索引）
python scripts/setup_d1.py

# 4. 启动服务
python main.py

# 5. 打开 API 文档
# http://127.0.0.1:8000/docs
```

## 项目结构

```
zhida/
├── app/
│   ├── api/                 # API 路由
│   │   └── lookup_retrieve.py   # A 负责的三个接口
│   ├── core/                # 核心配置
│   │   ├── config.py            # 配置（pydantic-settings）
│   │   ├── database.py          # SQLAlchemy 连接
│   │   └── logger.py            # loguru 日志
│   ├── models/              # SQLAlchemy 模型
│   │   ├── error_code.py
│   │   ├── customer_asset.py
│   │   ├── ticket.py
│   │   ├── query_log.py
│   │   └── vector_index_meta.py
│   ├── schemas/             # Pydantic Schema（接口契约）
│   │   └── contract.py
│   └── services/            # 业务逻辑层
│       ├── vector_retriever.py  # FAISS 向量检索 + 错误码识别
│       └── query_service.py     # 错误码查询 + 埋点
├── data/                    # 原始 CSV 数据
├── db/                      # SQLite 数据库 + FAISS 索引
├── scripts/                 # 初始化脚本
│   ├── init_db.py           # 建表 + 灌数据
│   ├── build_faiss_index.py # FAISS 向量索引构建
│   └── setup_d1.py          # D1 一键初始化
├── tests/                   # pytest 测试
├── main.py                  # FastAPI 入口
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## 接口清单（A 负责）

| 接口 | 方法 | 说明 | 调用方 |
|------|------|------|--------|
| `/api/lookup` | GET | 错误码秒查 | C（浮层） |
| `/api/retrieve` | POST | 内部向量检索 | B（草稿生成） |
| `/api/feedback` | POST | 埋点反馈 | C（浮层） |
| `/health` | GET | 健康检查 | — |

## 接口契约

严格遵循 `api_contract.md`，核心约定：

- 字段命名：snake_case
- 空值：用 `null`，不用空字符串
- 置信度：只有 `high` / `low`
- 错误码未命中：返回 200 + `code: "NOT_EXIST"`，不是 404

## 开发规范

- 分支：`feat/lookup-retrieve`
- 只修改 A 职责范围内的文件
- 每次提交前 `git status` 检查变更文件
- 接口变更必须先改 `api_contract.md`，PR 带 `[contract]`
