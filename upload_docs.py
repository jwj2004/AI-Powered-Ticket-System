import requests

BASE = "http://localhost:8000"

# 1. 登录获取 token
resp = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"})
token = resp.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Token: {token[:30]}...")

# 2. 创建文档空间
for name, desc in [("支付系统", "支付超时、退款失败等支付相关文档"), ("云运维", "云服务器宕机、K8s Pod异常等运维文档")]:
    r = requests.post(f"{BASE}/api/doc-spaces", headers=headers, json={"name": name, "description": desc})
    print(f"创建空间 {name}: {r.json()}")

# 3. 上传文档
docs = [
    ("data/支付超时处理方案.txt", 1),
    ("data/API网关限流熔断配置.txt", 1),
    ("data/ECS实例宕机排查.txt", 2),
    ("data/ECS实例运维FAQ.txt", 2),
    ("data/K8s Pod故障排查.txt", 2),
    ("data/数据库连接池满了排查.txt", 2),
]

doc_ids = []
for filepath, space_id in docs:
    with open(filepath, "rb") as f:
        r = requests.post(
            f"{BASE}/api/documents/upload",
            headers=headers,
            files={"file": f},
            data={"space_id": space_id},
        )
    print(f"上传 {filepath}: {r.status_code} {r.json()}")
    if r.status_code == 200:
        doc_ids.append(r.json()["id"])

# 4. 审批文档
for doc_id in doc_ids:
    r = requests.post(f"{BASE}/api/documents/{doc_id}/approve", headers=headers)
    print(f"审批文档 {doc_id}: {r.json()}")

# 5. 测试 RAG 检索
questions = [
    "支付超时了怎么办？",
    "ECS服务器宕机了怎么排查？",
    "K8s Pod一直重启是什么原因？",
    "数据库连接池满了怎么处理？",
]
for q in questions:
    r = requests.post(f"{BASE}/api/chat", headers=headers, json={"message": q})
    data = r.json()
    print(f"\n问: {q}")
    print(f"答: {data['reply'][:200]}")
    print(f"置信度: {data['confidence']}")
    print(f"引用: {data['citations']}")
