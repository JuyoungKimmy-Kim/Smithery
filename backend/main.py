from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_database
from backend.api import auth_router, mcp_servers_router, comments_router, playground_router

# Rate limiter 설정
limiter = Limiter(key_func=get_remote_address)

# FastAPI 앱 생성
app = FastAPI(
    title="MCP Server Marketplace",
    description="MCP Server 등록 및 관리 플랫폼",
    version="1.0.0"
)

# Rate limiter를 앱에 연결
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(playground_router, prefix="/api/v1")

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
    """
    Enhanced health check endpoint with resource monitoring
    Useful for monitoring backend stability and resource usage
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "status": "healthy",
            "memory": {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),  # Resident Set Size
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),  # Virtual Memory Size
                "percent": round(process.memory_percent(), 2)
            },
            "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
            "num_threads": process.num_threads(),
            "connections": len(process.connections())
        }
    except ImportError:
        # Fallback if psutil is not installed
        return {
            "status": "healthy",
            "note": "Install psutil for detailed metrics: pip install psutil"
        }
    except Exception as e:
        # If health check itself fails, still return something
        return {
            "status": "healthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    import signal
    import sys
    import logging

    logger = logging.getLogger(__name__)

    def handle_shutdown(sig, frame):
        """Graceful shutdown handler for SIGTERM and SIGINT"""
        logger.info(f"Received shutdown signal ({sig}), cleaning up...")
        sys.exit(0)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    logger.info("Starting FastAPI application with Uvicorn...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=180,   # Keep-alive timeout for long-running requests
        limit_concurrency=50,      # Max concurrent connections to prevent resource exhaustion
        limit_max_requests=1000,   # Restart worker after N requests to prevent memory leaks
        log_level="info"
    ) 