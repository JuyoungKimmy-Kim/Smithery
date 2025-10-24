from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.service import MCPServerService, UserService, MCPProxyService
from backend.database.model import User
from backend.api.schemas import (
    MCPServerCreate, MCPServerResponse, MCPServerUpdate,
    SearchRequest, SearchResponse, FavoriteRequest, FavoriteResponse,
    AdminApprovalRequest, TagResponse, PreviewToolsRequest, PreviewToolsResponse,
    AnnouncementRequest
)
from backend.api.auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/mcp-servers", tags=["mcp-servers"])

@router.post("/", response_model=MCPServerResponse)
def create_mcp_server(
    mcp_server_data: MCPServerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 MCP 서버를 생성합니다."""
    
    mcp_service = MCPServerService(db)
    
    try:
        mcp_server = mcp_service.create_mcp_server(
            mcp_server_data.dict(), current_user.id
        )
        return mcp_server
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create MCP server: {str(e)}"
        )

@router.post("/preview")
def preview_mcp_server(github_link: dict, db: Session = Depends(get_db)):
    """GitHub 링크에서 도구 정보를 미리보기합니다."""
    try:
        mcp_service = MCPServerService(db)
        github_url = github_link.get("github_link", "")
        
        if not github_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub link is required"
            )
        
        # GitHub 링크에서 도구 정보 추출 (skeleton 구현)
        tools_data = mcp_service._extract_tools_from_github(github_url)
        
        return {
            "tools": tools_data,
            "resources": []  # 현재는 resources는 빈 배열로 반환
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/preview-tools", response_model=PreviewToolsResponse)
async def preview_mcp_tools(request: PreviewToolsRequest):
    """
    MCP 서버에서 tools를 미리보기합니다.
    HTTPS -> HTTP Mixed Content 문제와 CORS 문제를 해결하기 위한 프록시 엔드포인트
    """
    try:
        result = await MCPProxyService.fetch_tools(request.url, request.protocol)
        return PreviewToolsResponse(
            tools=result.get("tools", []),
            success=result.get("success", False),
            message=result.get("message")
        )
    except Exception as e:
        return PreviewToolsResponse(
            tools=[],
            success=False,
            message=f"Failed to preview tools: {str(e)}"
        )

@router.get("/", response_model=List[MCPServerResponse])
def get_mcp_servers(
    status: str = Query("approved", description="서버 상태"),
    category: Optional[str] = Query(None, description="카테고리"),
    limit: int = Query(20, description="조회 개수"),
    offset: int = Query(0, description="오프셋"),
    db: Session = Depends(get_db)
):
    """MCP 서버 목록을 조회합니다."""
    mcp_service = MCPServerService(db)
    
    if status == "approved":
        mcps = mcp_service.get_approved_mcp_servers(limit, offset)
    elif status == "pending":
        mcps = mcp_service.get_pending_mcp_servers()
    else:
        mcps = mcp_service.get_approved_mcp_servers(limit, offset)
    
    # 각 MCP 서버에 favorites_count 추가
    for mcp in mcps:
        mcp.favorites_count = mcp_service.get_mcp_server_favorites_count(mcp.id)
        print(f"MCP {mcp.id} ({mcp.name}): favorites_count = {mcp.favorites_count}")
    
    return mcps

@router.get("/{mcp_server_id}/favorites/count")
def get_mcp_server_favorites_count(mcp_server_id: int, db: Session = Depends(get_db)):
    """특정 MCP 서버의 즐겨찾기 수를 조회합니다."""
    mcp_service = MCPServerService(db)
    count = mcp_service.get_mcp_server_favorites_count(mcp_server_id)
    return {"mcp_server_id": mcp_server_id, "favorites_count": count}

@router.get("/{mcp_server_id}", response_model=MCPServerResponse)
def get_mcp_server(mcp_server_id: int, db: Session = Depends(get_db)):
    """특정 MCP 서버의 상세 정보를 조회합니다."""
    
    mcp_service = MCPServerService(db)
    mcp_server = mcp_service.get_mcp_server_with_tools(mcp_server_id)
    
    if not mcp_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    return mcp_server

@router.post("/search", response_model=SearchResponse)
def search_mcp_servers(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """MCP 서버를 검색합니다."""
    mcp_service = MCPServerService(db)
    
    if search_request.category:
        mcp_servers = mcp_service.get_mcp_servers_by_category(
            search_request.category, search_request.status
        )
    else:
        mcp_servers = mcp_service.search_mcp_servers(
            search_request.keyword, search_request.status
        )
    
    return SearchResponse(
        mcp_servers=mcp_servers,
        total_count=len(mcp_servers)
    )

@router.post("/{mcp_server_id}/favorite", response_model=FavoriteResponse)
def add_favorite(
    mcp_server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MCP 서버를 즐겨찾기에 추가합니다."""
    user_service = UserService(db)
    success = user_service.add_favorite(current_user.id, mcp_server_id)
    
    if success:
        return FavoriteResponse(success=True, message="즐겨찾기에 추가되었습니다.")
    else:
        return FavoriteResponse(success=False, message="이미 즐겨찾기에 추가되어 있습니다.")

@router.delete("/{mcp_server_id}/favorite", response_model=FavoriteResponse)
def remove_favorite(
    mcp_server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MCP 서버를 즐겨찾기에서 제거합니다."""
    user_service = UserService(db)
    success = user_service.remove_favorite(current_user.id, mcp_server_id)
    
    if success:
        return FavoriteResponse(success=True, message="즐겨찾기에서 제거되었습니다.")
    else:
        return FavoriteResponse(success=False, message="즐겨찾기에 존재하지 않습니다.")

@router.get("/user/favorites", response_model=List[MCPServerResponse])
def get_user_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 즐겨찾기 목록을 조회합니다."""
    user_service = UserService(db)
    return user_service.get_user_favorites(current_user.id)

@router.get("/user/my-servers", response_model=List[MCPServerResponse])
def get_user_mcp_servers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자가 등록한 MCP 서버 목록을 조회합니다. (mypage용 - pending 포함)"""
    user_service = UserService(db)
    return user_service.get_user_all_mcp_servers(current_user.id)

@router.get("/user/{username}", response_model=List[MCPServerResponse])
def get_user_mcp_servers_by_username(
    username: str,
    db: Session = Depends(get_db)
):
    """특정 사용자가 등록한 MCP 서버 목록을 조회합니다."""
    user_service = UserService(db)
    servers = user_service.get_user_mcp_servers_by_username(username)
    
    if not servers and not user_service.get_user_by_username(username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return servers

# 관리자 전용 엔드포인트
@router.post("/admin/approve", response_model=MCPServerResponse)
def approve_mcp_server(
    approval_request: AdminApprovalRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """MCP 서버를 승인하거나 거부합니다."""
    mcp_service = MCPServerService(db)
    
    if approval_request.action == "approve":
        mcp_server = mcp_service.approve_mcp_server(approval_request.mcp_server_id)
        if not mcp_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP Server not found"
            )
        return mcp_server
    elif approval_request.action == "reject":
        mcp_server = mcp_service.reject_mcp_server(approval_request.mcp_server_id)
        if not mcp_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP Server not found"
            )
        return mcp_server
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use 'approve' or 'reject'"
        )

@router.post("/admin/approve-all", response_model=dict)
def approve_all_pending_servers(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """모든 승인 대기중인 MCP 서버를 일괄 승인합니다."""
    mcp_service = MCPServerService(db)
    result = mcp_service.approve_all_pending_servers()
    return {
        "message": f"{result['approved_count']}개의 서버가 승인되었습니다.",
        "approved_count": result['approved_count']
    }

@router.delete("/admin/{mcp_server_id}")
def delete_mcp_server(
    mcp_server_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """MCP 서버를 삭제합니다."""
    mcp_service = MCPServerService(db)
    success = mcp_service.delete_mcp_server(mcp_server_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    return {"message": "MCP Server deleted successfully"}

@router.get("/tags/popular", response_model=List[TagResponse])
def get_popular_tags(
    limit: int = Query(10, description="조회 개수"),
    db: Session = Depends(get_db)
):
    """인기 태그 목록을 조회합니다."""
    mcp_service = MCPServerService(db)
    return mcp_service.get_popular_tags(limit)

@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    """모든 카테고리 목록을 조회합니다."""
    mcp_service = MCPServerService(db)
    return mcp_service.get_categories()

@router.put("/{mcp_server_id}", response_model=MCPServerResponse)
def update_mcp_server(
    mcp_server_id: int,
    mcp_server_data: MCPServerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MCP 서버를 수정합니다. 등록자만 수정 가능합니다."""
    
    mcp_service = MCPServerService(db)
    
    # MCP 서버 존재 확인 및 소유자 확인
    existing_server = mcp_service.get_mcp_server_by_id(mcp_server_id)
    if not existing_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    
    # 등록자 또는 관리자만 수정 가능
    if existing_server.owner_id != current_user.id and current_user.is_admin != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the server owner or admin can update this server"
        )
    
    
    # 서버 수정
    updated_server = mcp_service.update_mcp_server(mcp_server_id, mcp_server_data)
    if not updated_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    return updated_server

@router.delete("/{mcp_server_id}")
def delete_mcp_server_by_owner(
    mcp_server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MCP 서버를 삭제합니다. 등록자만 삭제 가능합니다."""
    mcp_service = MCPServerService(db)
    
    # MCP 서버 존재 확인 및 소유자 확인
    existing_server = mcp_service.get_mcp_server_by_id(mcp_server_id)
    if not existing_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    # 등록자 또는 관리자만 삭제 가능
    if existing_server.owner_id != current_user.id and current_user.is_admin != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the server owner or admin can delete this server"
        )
    
    # 서버 삭제
    success = mcp_service.delete_mcp_server(mcp_server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    return {"message": "MCP Server deleted successfully"}

@router.put("/{mcp_server_id}/announcement", response_model=MCPServerResponse)
def update_mcp_server_announcement(
    mcp_server_id: int,
    announcement_data: AnnouncementRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MCP 서버의 공지사항을 추가하거나 수정합니다. 소유자만 가능합니다. 최대 1000자까지 입력 가능합니다."""
    mcp_service = MCPServerService(db)
    
    # MCP 서버 존재 확인 및 소유자 확인
    existing_server = mcp_service.get_mcp_server_by_id(mcp_server_id)
    if not existing_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    # 소유자만 공지사항 수정 가능
    if existing_server.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the server owner can update announcement"
        )
    
    # 공지사항 업데이트
    updated_server = mcp_service.update_mcp_server_announcement(
        mcp_server_id, announcement_data.announcement
    )
    if not updated_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    return updated_server

@router.delete("/{mcp_server_id}/announcement", response_model=MCPServerResponse)
def delete_mcp_server_announcement(
    mcp_server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MCP 서버의 공지사항을 삭제합니다. 소유자만 가능합니다."""
    mcp_service = MCPServerService(db)
    
    # MCP 서버 존재 확인 및 소유자 확인
    existing_server = mcp_service.get_mcp_server_by_id(mcp_server_id)
    if not existing_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    # 소유자만 공지사항 삭제 가능
    if existing_server.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the server owner can delete announcement"
        )
    
    # 공지사항 삭제 (None으로 설정)
    updated_server = mcp_service.update_mcp_server_announcement(mcp_server_id, None)
    if not updated_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )
    
    return updated_server 