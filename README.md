# 知答 · 工单智能副驾 MVP

一线客服粘贴客户原话，系统返回错误码释义、相似历史工单和可复制的答复草稿。

## 环境要求

- Python 3.10+
- Node.js 18+

## 后端启动

```bash
# 建议使用虚拟环境（示例）
# python3.10 -m venv ~/zhida && source ~/zhida/bin/activate

pip install -r requirements.txt
python scripts/init_db.py
python main.py
```

- 地址：http://127.0.0.1:8000
- Swagger：http://127.0.0.1:8000/docs

> 向量索引（FAISS）由 A 负责，D3 再构建；未建索引时检索可能走降级逻辑，不影响前端联调基本路径。

## 前端启动

```bash
cd zhida_web
npm install
npm run dev
```

- 地址：http://127.0.0.1:5173

## 默认端口

| 服务 | 地址 |
|------|------|
| 后端 FastAPI | http://127.0.0.1:8000 |
| 前端 Vite | http://127.0.0.1:5173 |

## 团队分工

| 角色 | 负责 |
|------|------|
| **A · 数据检索** | 错误码秒查、向量召回、客户上下文、埋点表；`/api/lookup`、`/api/retrieve`、`/api/feedback` |
| **B · 草稿生成** | LLM 草稿流水线、无引用不输出；`/api/draft`（内部调 A 的 retrieve） |
| **C · 前端与工程** | FastAPI 骨架与 CORS、Vue3 页面、接口契约与部署说明 |

## 核心接口（契约冻结）

- `GET /api/lookup?code=XXX`
- `POST /api/draft` body: `{ raw_text, customer_id }`
- `POST /api/feedback` body: `{ query_id, copied, thumbs_down }`
- `GET /api/health`

字段均为 snake_case；空值用 JSON `null`；错误统一 `{"detail": "..."}` + 4xx/5xx。
