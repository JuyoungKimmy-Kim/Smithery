from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.dao.user_dao import UserDAO
from backend.database.model.mcp_server import (
    MCPServer,
    MCPServerTool,
    MCPServerResource,
    TransportType,
    MCPServerCreate,
    MCPServerUpdate,
    MCPServerStatus
)
from backend.database.model.user import User, UserCreate, UserLogin, UserResponse
from backend.service.mcp_server_service import MCPServerService
from backend.service.auth_service import AuthService
from backend.middleware.auth_middleware import (
    get_current_user,
    get_current_admin_user,
    get_optional_current_user,
    get_auth_service
)
from typing import List, Optional
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="DS Smithery API", 
    version="1.0.0",
    description="MCP Server Marketplace API"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 연결
def get_mcp_dao():
    dao = MCPServerDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    return dao

def get_user_dao():
    dao = UserDAO("mcp_market.db")
    dao.connect()
    dao.create_table()
    return dao

# MCP 서버 서비스 인스턴스 생성
def get_mcp_service():
    github_token = os.getenv("GITHUB_TOKEN")
    return MCPServerService(github_token)

# ==================== 인증 API ====================

@app.post("/api/auth/register", response_model=dict)
def register_user(user_create: UserCreate):
    """사용자 등록"""
    try:
        auth_service = get_auth_service()
        user = auth_service.register_user(user_create)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        
        return {
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=dict)
def login_user(user_login: UserLogin):
    """사용자 로그인"""
    try:
        auth_service = get_auth_service()
        result = auth_service.login_user(user_login)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me", response_model=dict)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보 조회"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "avatar_url": current_user.avatar_url,
        "created_at": current_user.created_at
    }

# ==================== MCP 서버 API ====================

@app.get("/api/mcps/approved", response_model=List[dict])
def get_approved_mcps():
    """승인된 MCP 서버 목록 조회 (공개)"""
    try:
        dao = get_mcp_dao()
        mcps = dao.get_approved_mcp_servers()
        dao.close()
        return jsonable_encoder(mcps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcps/pending", response_model=List[dict])
def get_pending_mcps(current_admin: User = Depends(get_current_admin_user)):
    """승인 대기 중인 MCP 서버 목록 조회 (관리자용)"""
    try:
        dao = get_mcp_dao()
        mcps = dao.get_pending_mcp_servers()
        dao.close()
        return jsonable_encoder(mcps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcps/my", response_model=List[dict])
def get_my_mcps(current_user: User = Depends(get_current_user)):
    """내가 등록한 MCP 서버 목록 조회"""
    try:
        dao = get_mcp_dao()
        mcps = dao.get_mcp_servers_by_user(current_user.id)
        dao.close()
        return jsonable_encoder(mcps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcps/{mcp_id}", response_model=dict)
def get_mcp(mcp_id: int):
    """특정 MCP 서버 조회"""
    try:
        dao = get_mcp_dao()
        mcp = dao.get_mcp_server(mcp_id)
        dao.close()
        
        if not mcp:
            raise HTTPException(status_code=404, detail="MCP server not found")
        
        return jsonable_encoder(mcp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcps", response_model=dict)
def create_mcp(mcp: MCPServerCreate, current_user: User = Depends(get_current_user)):
    """새로운 MCP 서버 생성"""
    try:
        dao = get_mcp_dao()
        mcp_service = get_mcp_service()

        # MCP 서버 생성
        mcp_server_id = dao.create_mcp_server(mcp, current_user.id)
        
        if not mcp_server_id:
            raise HTTPException(status_code=400, detail="Failed to create MCP server")

        # GitHub 링크에서 tools와 resources 정보 자동 추출
        if mcp.github_link:
            print(f"GitHub 링크에서 tools와 resources 정보 추출 중: {mcp.github_link}")
            
            # Python 정적 분석 시도
            static_result = mcp_service.extract_python_mcp_static_only(mcp.github_link)
            
            if "error" not in static_result and (static_result.get("mcp_tools") or static_result.get("mcp_resources")):
                # Python 정적 분석 결과 사용
                print("Python 정적 분석 결과 사용")
                tools = static_result.get("mcp_tools", [])
                resources = static_result.get("mcp_resources", [])
                
                # 도구와 리소스 추가
                if tools:
                    dao.add_tools_to_server(mcp_server_id, tools)
                if resources:
                    dao.add_resources_to_server(mcp_server_id, resources)
                
                print(f"Python 정적 분석 - Tools: {len(tools)}개, Resources: {len(resources)}개")
            else:
                # 기존 방식으로 fallback
                print("기존 방식으로 tools 정보 추출")
                extracted_tools = mcp_service.read_mcp_server_tool_list(mcp.github_link)
                
                if extracted_tools:
                    # 추출된 tools를 MCPServerTool 형식으로 변환
                    tools = []
                    for tool_data in extracted_tools:
                        tool = MCPServerTool(
                            name=tool_data.get("name", ""),
                            description=tool_data.get("description", ""),
                            parameters=[]
                        )
                        tools.append(tool)
                    
                    dao.add_tools_to_server(mcp_server_id, tools)

        dao.close()
        
        return {
            "message": "MCP server created successfully",
            "mcp_id": mcp_server_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcps/{mcp_id}/approve", response_model=dict)
def approve_mcp(mcp_id: int, current_admin: User = Depends(get_current_admin_user)):
    """MCP 서버 승인 (관리자용)"""
    try:
        dao = get_mcp_dao()
        success = dao.update_mcp_server_status(mcp_id, MCPServerStatus.approved, current_admin.id)
        dao.close()
        
        if not success:
            raise HTTPException(status_code=404, detail="MCP server not found")
        
        return {"message": "MCP server approved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcps/{mcp_id}/reject", response_model=dict)
def reject_mcp(mcp_id: int, current_admin: User = Depends(get_current_admin_user)):
    """MCP 서버 거부 (관리자용)"""
    try:
        dao = get_mcp_dao()
        success = dao.update_mcp_server_status(mcp_id, MCPServerStatus.rejected, current_admin.id)
        dao.close()
        
        if not success:
            raise HTTPException(status_code=404, detail="MCP server not found")
        
        return {"message": "MCP server rejected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/mcps/{mcp_id}", response_model=dict)
def delete_mcp(mcp_id: int, current_admin: User = Depends(get_current_admin_user)):
    """MCP 서버 삭제 (관리자용)"""
    try:
        dao = get_mcp_dao()
        success = dao.delete_mcp_server(mcp_id)
        dao.close()
        
        if not success:
            raise HTTPException(status_code=404, detail="MCP server not found")
        
        return {"message": "MCP server deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 즐겨찾기 API ====================

@app.post("/api/favorites/{mcp_id}", response_model=dict)
def add_favorite(mcp_id: int, current_user: User = Depends(get_current_user)):
    """즐겨찾기 추가"""
    try:
        dao = get_mcp_dao()
        success = dao.add_favorite(current_user.id, mcp_id)
        dao.close()
        
        if not success:
            raise HTTPException(status_code=400, detail="Already in favorites or MCP server not found")
        
        return {"message": "Added to favorites successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/favorites/{mcp_id}", response_model=dict)
def remove_favorite(mcp_id: int, current_user: User = Depends(get_current_user)):
    """즐겨찾기 제거"""
    try:
        dao = get_mcp_dao()
        success = dao.remove_favorite(current_user.id, mcp_id)
        dao.close()
        
        if not success:
            raise HTTPException(status_code=404, detail="Favorite not found")
        
        return {"message": "Removed from favorites successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/favorites", response_model=List[dict])
def get_favorites(current_user: User = Depends(get_current_user)):
    """사용자 즐겨찾기 목록 조회"""
    try:
        dao = get_mcp_dao()
        favorites = dao.get_user_favorites(current_user.id)
        dao.close()
        return jsonable_encoder(favorites)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 검색 API ====================

@app.get("/api/search", response_model=List[dict])
def search_mcps(q: str):
    """키워드로 MCP 서버 검색"""
    try:
        dao = get_mcp_dao()
        results = dao.search_mcp_servers(q)
        dao.close()
        return jsonable_encoder(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 기존 API (하위 호환성) ====================

@app.get("/api/mcps", response_model=List[dict])
def get_all_mcps():
    """모든 MCP 서버 목록 조회 (기존 API - 승인된 것만 반환)"""
    try:
        dao = get_mcp_dao()
        mcps = dao.get_approved_mcp_servers()
        dao.close()
        return jsonable_encoder(mcps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcps/preview", response_model=dict)
def preview_mcp_server(github_link: dict):
    """MCP 서버 미리보기 (기존 API)"""
    try:
        mcp_service = get_mcp_service()
        result = mcp_service.extract_python_mcp_static_only(github_link["github_link"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 관리자 API ====================

@app.get("/api/admin/users", response_model=List[dict])
def get_all_users(current_admin: User = Depends(get_current_admin_user)):
    """모든 사용자 목록 조회 (관리자용)"""
    try:
        dao = get_user_dao()
        users = dao.get_all_users()
        dao.close()
        
        # 비밀번호 해시는 제외하고 반환
        user_list = []
        for user in users:
            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
            user_list.append(user_dict)
        
        return user_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )
