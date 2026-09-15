"""
知答 MVP - 数据检索服务（A 模块）
启动入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import log
from app.api import lookup_router

app = FastAPI(
    title=settings.app_name,
    description="知答 MVP - 数据检索后端（A 模块）",
    version="0.1.0",
)

# CORS - 允许油猴脚本跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(lookup_router)


@app.get("/health", summary="健康检查")
def health_check():
    return {"status": "ok", "service": "lookup-retrieve"}


@app.on_event("startup")
async def startup_event():
    log.success(f"{settings.app_name} 启动成功")
    log.info(f"API 文档: http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug,
    )
