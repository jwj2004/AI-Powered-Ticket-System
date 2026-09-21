"""知答问答入口：POST /api/chat。默认 SSE，Accept: application/json 时同步 JSON。"""

from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from backend.agent.service import iter_chat_sse, run_chat
from backend.auth import CurrentUser, get_current_user
from backend import store

router = APIRouter(prefix="/api", tags=["问答 (B模块)"])


class ChatRequest(BaseModel):
    """契约字段为 message。联调期间若前端仍传 query，也映射到 message。"""

    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(
        ...,
        validation_alias=AliasChoices("message", "query"),
        description="用户问题（契约字段名 message）",
    )
    conversation_id: Optional[int] = None
    stream: Optional[bool] = None

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("message 不能为空")
        return text


class Citation(BaseModel):
    document_id: int
    title: str
    chunk_index: int


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    message_id: int
    gap_id: Optional[int] = None


def wants_sse(body: ChatRequest, request: Request) -> bool:
    """默认 SSE；仅显式要求 JSON 或 stream=false 时同步返回。"""
    if body.stream is True:
        return True
    if body.stream is False:
        return False
    accept = (request.headers.get("accept") or "").lower()
    parts = [p.strip().split(";")[0] for p in accept.split(",") if p.strip()]
    if "text/event-stream" in parts:
        return True
    if "application/json" in parts:
        return False
    return True


@router.post("/chat")
def chat(
    body: ChatRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    store.init_db()
    try:
        if wants_sse(body, request):
            return StreamingResponse(
                iter_chat_sse(
                    message=body.message,
                    conversation_id=body.conversation_id,
                    user=user,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        result = run_chat(
            message=body.message,
            conversation_id=body.conversation_id,
            user=user,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"问答失败: {exc}") from exc
    return JSONResponse(ChatResponse(**result).model_dump(exclude_none=True))
