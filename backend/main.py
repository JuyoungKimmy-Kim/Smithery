from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_database
from backend.api import auth_router, mcp_servers_router, comments_router

# FastAPI 앱 생성
app = FastAPI(
    title="MCP Server Marketplace",
    description="MCP Server 등록 및 관리 플랫폼",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router, prefix="/api/v1")
app.include_router(mcp_servers_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 데이터베이스 초기화"""
    print("데이터베이스를 초기화합니다...")
    init_database()
    print("애플리케이션이 시작되었습니다.")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "MCP Server Marketplace API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 