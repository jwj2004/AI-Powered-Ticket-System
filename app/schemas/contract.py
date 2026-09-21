"""
Pydantic Schemas - 严格对齐 api_contract.md 接口契约
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================
# 一、错误码秒查 GET /api/lookup
# ============================================================
class LookupResponse(BaseModel):
    """错误码查询响应
    注意：未命中时返回 200 + 空字段，不是 404
    """
    code: str = Field(..., description="错误码，未命中时返回 'NOT_EXIST'")
    name: str = Field("", description="错误名称")
    meaning: str = Field("", description="错误含义")
    trigger_condition: str = Field("", description="触发条件")
    causes: List[str] = Field(default_factory=list, description="已知原因列表")
    solution: str = Field("", description="解决方案")
    related_versions: List[str] = Field(default_factory=list, description="关联版本列表")


# ============================================================
# 二、草稿生成 POST /api/draft（B 实现，A 不实现，但 A 要懂契约）
# ============================================================
class DraftRequest(BaseModel):
    """草稿生成请求"""
    raw_text: str = Field(..., description="客户原话，前端粘贴的内容")
    customer_id: Optional[str] = Field(None, description="客户ID，解析不到传 null")


class EvidenceItem(BaseModel):
    """相似工单证据项"""
    ticket_id: str = Field(..., description="来源工单号")
    summary: str = Field(..., description="一句话摘要")


class DraftResponse(BaseModel):
    """草稿生成响应
    注意：query_id 是契约补充字段，必须返回
    """
    query_id: str = Field(..., description="查询唯一ID，用于反馈上报")
    error_code: Optional[str] = Field(None, description="命中错误码，未命中为 null")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="相似工单证据，最多3条")
    draft: Optional[str] = Field(None, description="答复草稿，low置信度时为 null")
    confidence: str = Field(..., description="置信度：high / low")
    message: Optional[str] = Field(None, description="low置信度时的提示文案")


# ============================================================
# 三、反馈埋点 POST /api/feedback
# ============================================================
class FeedbackRequest(BaseModel):
    """反馈请求"""
    query_id: str = Field(..., description="查询ID")
    copied: bool = Field(False, description="是否复制了草稿")
    thumbs_down: bool = Field(False, description="是否点了踩")


class FeedbackResponse(BaseModel):
    """反馈响应"""
    ok: bool = Field(True, description="是否成功")


# ============================================================
# 四、内部检索接口 POST /api/retrieve（A 实现，B 调用）
# ============================================================
class RetrieveRequest(BaseModel):
    """内部检索请求"""
    query: str = Field(..., description="查询文本")
    customer_id: Optional[str] = Field(None, description="客户ID")
    top_k: int = Field(3, ge=1, le=10, description="返回条数")


class RetrieveTicket(BaseModel):
    """检索到的工单条目"""
    ticket_id: str = Field(..., description="工单ID")
    solution_text: str = Field(..., description="解决文案")
    score: float = Field(..., description="相似度得分")


class RetrieveChunk(BaseModel):
    """检索到的文档切块"""
    document_id: int
    title: str = ""
    chunk_index: int = 0
    content: str = ""
    score: float = 0.0


class RetrieveResponse(BaseModel):
    """内部检索响应"""
    error_code: Optional[str] = Field(None, description="识别到的错误码，未识别为 null")
    tickets: List[RetrieveTicket] = Field(default_factory=list, description="相似工单列表")
    chunks: List[RetrieveChunk] = Field(default_factory=list, description="相似文档切块")
