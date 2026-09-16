"""30 条回灌：用 mock 检索检查 high/low 分流是否稳定。"""

from backend.agent.graph import get_graph
from backend.agent.rules import LOW_MESSAGE, REFUSE_MESSAGE

# expected: high | low_gap | refuse
EVAL_CASES = [
    ("订单导出超时怎么办？", "high", "ops"),
    ("一次导出太多是不是会超时", "high", "ops"),
    ("PAY_CALLBACK_TIMEOUT 怎么处理", "high", "ops"),
    ("微信付了钱订单还是待支付", "high", "ops"),
    ("优惠券核销失败怎么办", "high", "ops"),
    ("物流轨迹一直不更新", "high", "ops"),
    ("买家付款后后台还是待支付", "high", "ops"),
    ("导出任务排队了怎么办", "high", "ops"),
    ("券已经过期核销报错", "high", "ops"),
    ("承运商已揽收但后台没轨迹", "high", "ops"),
    ("今天天气怎么样", "refuse", "ops"),
    ("帮我写一首诗", "refuse", "ops"),
    ("你是谁啊", "refuse", "ops"),
    ("讲个笑话来听听", "refuse", "ops"),
    ("今天星期几", "refuse", "ops"),
    ("量子加密证书在工单里怎么配置", "low_gap", "ops"),
    ("数据库分片策略文档在哪", "low_gap", "ops"),
    ("机房空调设定温度是多少", "low_gap", "ops"),
    ("员工食堂菜单今天有什么", "low_gap", "ops"),
    ("VPN 证书指纹怎么轮换", "low_gap", "ops"),
    ("按周拆分导出可以吗", "high", "ops"),
    ("补单之后还要改回调地址吗", "high", "ops"),
    ("活动叠加导致券不能用", "high", "ops"),
    ("支付回调地址升级后要核对吗", "high", "ops"),
    ("高峰时段导出要注意什么", "high", "ops"),
    ("错误码 PAY_CALLBACK_TIMEOUT 的标准解法", "high", "ops"),
    ("订单导出超过五万条", "high", "ops"),
    ("随便聊聊吧", "refuse", "ops"),
    ("内部没有的冷门故障码 XYZ_UNKNOWN_BUG 怎么修", "low_gap", "ops"),
    ("如何提交工单不要发客户手机号", "high", "newbie"),
]


def test_eval_thirty_questions_confidence_split():
    graph = get_graph()
    assert len(EVAL_CASES) == 30
    for question, expected, role in EVAL_CASES:
        result = graph.invoke(
            {
                "message": question,
                "user_id": 2,
                "username": "ops",
                "role": role,
                "history": [],
                "route_kind": "rag",
                "lookup": None,
                "chunks": [],
                "reply": "",
                "citations": [],
                "confidence": "low",
                "gap_id": None,
                "create_gap": False,
            }
        )
        conf = result.get("confidence")
        if expected == "high":
            assert conf == "high", question
            assert result.get("reply")
            assert result.get("reply") not in {LOW_MESSAGE, REFUSE_MESSAGE}
        elif expected == "refuse":
            assert conf == "low", question
            assert result.get("reply") == REFUSE_MESSAGE
            assert result.get("create_gap") is False
        else:
            assert conf == "low", question
            assert result.get("reply") == LOW_MESSAGE
            assert result.get("create_gap") is True
