"""POST /api/draft 路由与 Pydantic 契约模型。"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.draft.service import generate_draft

router = APIRouter(tags=["draft"])


class DraftRequest(BaseModel):
    raw_text: str = Field(..., description="客户原话")
    customer_id: Optional[str] = Field(
        default=None,
        description="客户 ID；解析不到传 null",
    )

    @field_validator("raw_text")
    @classmethod
    def raw_text_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("raw_text 不能为空")
        return text

    @field_validator("customer_id")
    @classmethod
    def empty_customer_id_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class EvidenceItem(BaseModel):
    ticket_id: str
    summary: str


class DraftResponse(BaseModel):
    query_id: str
    error_code: Optional[str] = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    draft: Optional[str] = None
    confidence: Literal["high", "low"]
    message: Optional[str] = None


@router.post(
    "/api/draft",
    response_model=DraftResponse,
    response_model_exclude_unset=True,
)
def create_draft(body: DraftRequest) -> DraftResponse:
    try:
        result = generate_draft(raw_text=body.raw_text, customer_id=body.customer_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"草稿生成失败: {exc}") from exc

    # 契约：low 时 draft/error_code 必须显式为 null；message 仅 low 时出现
    if result.get("confidence") == "low":
        return DraftResponse(
            query_id=result["query_id"],
            error_code=None,
            evidence=[],
            draft=None,
            confidence="low",
            message=result.get("message") or "未找到可靠依据，建议转二线处理",
        )

    return DraftResponse(
        query_id=result["query_id"],
        error_code=result.get("error_code"),
        evidence=result.get("evidence") or [],
        draft=result.get("draft"),
        confidence="high",
    )
