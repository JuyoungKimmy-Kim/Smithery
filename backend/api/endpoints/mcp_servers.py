from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import asyncio

from backend.database import get_db

logger = logging.getLogger(__name__)
from backend.service import MCPServerService, UserService, MCPProxyService, AnalyticsService
from backend.service.notification_service import NotificationService
from backend.database.model import User
from backend.api.schemas import (
    MCPServerCreate, MCPServerResponse, MCPServerUpdate,
    SearchRequest, SearchResponse, FavoriteRequest, FavoriteResponse,
    AdminApprovalRequest, TagResponse, PreviewToolsRequest, PreviewToolsResponse,
    AnnouncementRequest, PreviewPromptsRequest, PreviewPromptsResponse,
    PreviewResourcesRequest, PreviewResourcesResponse, TopUserResponse
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

@router.post("/preview-prompts", response_model=PreviewPromptsResponse)
async def preview_mcp_prompts(request: PreviewPromptsRequest):
    """
    MCP 서버에서 prompts를 미리보기합니다.
    HTTPS -> HTTP Mixed Content 문제와 CORS 문제를 해결하기 위한 프록시 엔드포인트
    """
    try:
        result = await MCPProxyService.fetch_prompts(request.url, request.protocol)
        return PreviewPromptsResponse(
            prompts=result.get("prompts", []),
            success=result.get("success", False),
            message=result.get("message")
        )
    except Exception as e:
        return PreviewPromptsResponse(
            prompts=[],
            success=False,
            message=f"Failed to preview prompts: {str(e)}"
        )

@router.post("/preview-resources", response_model=PreviewResourcesResponse)
async def preview_mcp_resources(request: PreviewResourcesRequest):
    """
    MCP 서버에서 resources를 미리보기합니다.
    HTTPS -> HTTP Mixed Content 문제와 CORS 문제를 해결하기 위한 프록시 엔드포인트
    """
    try:
        result = await MCPProxyService.fetch_resources(request.url, request.protocol)
        return PreviewResourcesResponse(
            resources=result.get("resources", []),
            success=result.get("success", False),
            message=result.get("message")
        )
    except Exception as e:
        return PreviewResourcesResponse(
            resources=[],
            success=False,
            message=f"Failed to preview resources: {str(e)}"
        )

@router.get("/", response_model=List[MCPServerResponse])
def get_mcp_servers(
    status: str = Query("approved", description="서버 상태 (approved, pending)"),
    category: Optional[str] = Query(None, description="카테고리"),
    sort: str = Query("favorites", description="정렬 기준 (favorites, created_at)"),
    order: str = Query("desc", description="정렬 순서 (asc, desc)"),
    limit: int = Query(20, description="조회 개수"),
    offset: int = Query(0, description="오프셋"),
    db: Session = Depends(get_db)
):
    """
    MCP 서버 목록을 조회합니다.

    - sort=favorites: 즐겨찾기 수 기준 정렬 (기본값)
    - sort=created_at: 등록일 기준 정렬
    - order=desc: 내림차순 (기본값)
    - order=asc: 오름차순

    Examples:
    - GET /?sort=favorites&limit=3  # Top 3 인기 서버
    - GET /?sort=created_at&limit=3 # Latest 3 서버
    """
    mcp_service = MCPServerService(db)

    # sort와 order 파라미터로 통합 조회
    mcps = mcp_service.get_mcp_servers(
        status=status,
        category=category,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset
    )

    # 각 MCP 서버에 favorites_count 추가
    for mcp in mcps:
        mcp.favorites_count = mcp_service.get_mcp_server_favorites_count(mcp.id)

    return mcps

@router.get("/top-users", response_model=List[TopUserResponse])
def get_top_users(
    limit: int = Query(3, description="조회 개수", le=10),
    db: Session = Depends(get_db)
):
    """Top Contributors를 조회합니다. (등록한 MCP 서버 수 기준)"""
    user_service = UserService(db)
    return user_service.get_top_users(limit)

@router.get("/{mcp_server_id}/favorites/count")
def get_mcp_server_favorites_count(mcp_server_id: int, db: Session = Depends(get_db)):
    """특정 MCP 서버의 즐겨찾기 수를 조회합니다."""
    mcp_service = MCPServerService(db)
    count = mcp_service.get_mcp_server_favorites_count(mcp_server_id)
    return {"mcp_server_id": mcp_server_id, "favorites_count": count}

@router.get("/{mcp_server_id}", response_model=MCPServerResponse)
def get_mcp_server(
    mcp_server_id: int,
    request: Request,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """특정 MCP 서버의 상세 정보를 조회합니다.

    Args:
        mcp_server_id: MCP 서버 ID
        source: 유입 경로 (search, list, direct 등)
    """

    mcp_service = MCPServerService(db)
    analytics_service = AnalyticsService(db)
    mcp_server = mcp_service.get_mcp_server_with_tools(mcp_server_id)

    if not mcp_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP Server not found"
        )

    # Analytics: 서버 조회 이벤트 추적
    try:
        referrer = request.headers.get("referer", "")
        analytics_service.track_server_view(
            mcp_server_id=mcp_server_id,
            referrer=referrer,
            source=source
        )
    except Exception as e:
        logger.error(f"Failed to track server view event: {e}")

    return mcp_server

@router.post("/search", response_model=SearchResponse)
def search_mcp_servers(
    search_request: SearchRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """MCP 서버를 검색합니다."""
    mcp_service = MCPServerService(db)
    analytics_service = AnalyticsService(db)

    # keyword와 tags 모두 처리
    if search_request.keyword and search_request.tags:
        # 둘 다 있으면 AND 조건으로 검색
        mcp_servers = mcp_service.search_mcp_servers_with_tags(
            search_request.keyword, search_request.tags, search_request.status
        )
    elif search_request.tags:
        # tags만 있으면 tag 검색
        mcp_servers = mcp_service.get_mcp_servers_by_tags(
            search_request.tags, search_request.status
        )
    elif search_request.keyword:
        # keyword만 있으면 keyword 검색
        mcp_servers = mcp_service.search_mcp_servers(
            search_request.keyword, search_request.status
        )
    else:
        # 둘 다 없으면 모든 서버 반환
        mcp_servers = mcp_service.get_approved_mcp_servers()

    # Analytics: 검색 이벤트 추적
    if search_request.keyword:  # 검색어가 있을 때만 추적
        try:
            analytics_service.track_search(
                keyword=search_request.keyword,
                results_count=len(mcp_servers),
                tags=search_request.tags
            )
        except Exception as e:
            logger.error(f"Failed to track search event: {e}")

    return SearchResponse(
        mcp_servers=mcp_servers,
        total_count=len(mcp_servers)
    )

@router.post("/{mcp_server_id}/favorite", response_model=FavoriteResponse)
def add_favorite(
    mcp_server_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MCP 서버를 즐겨찾기에 추가합니다."""
    user_service = UserService(db)
    analytics_service = AnalyticsService(db)
    success = user_service.add_favorite(current_user.id, mcp_server_id)

    if success:
        # 알림 생성 (MCP 소유자에게)
        try:
            notification_service = NotificationService(db)
            notification_service.create_favorite_notification(
                mcp_server_id=mcp_server_id,
                favoriter_user_id=current_user.id
            )
        except Exception as e:
            logger.error(f"Failed to create favorite notification: {e}")
            # 알림 생성 실패해도 즐겨찾기는 성공으로 처리

        # Analytics: 즐겨찾기 추가 이벤트 추적
        try:
            analytics_service.track_favorite_add(
                mcp_server_id=mcp_server_id,
                user_id=current_user.id
            )
        except Exception as e:
            logger.error(f"Failed to track favorite add event: {e}")

        return FavoriteResponse(success=True, message="즐겨찾기에 추가되었습니다.")
    else:
        return FavoriteResponse(success=False, message="이미 즐겨찾기에 추가되어 있습니다.")

@router.delete("/{mcp_server_id}/favorite", response_model=FavoriteResponse)
def remove_favorite(
    mcp_server_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MCP 서버를 즐겨찾기에서 제거합니다."""
    user_service = UserService(db)
    analytics_service = AnalyticsService(db)
    success = user_service.remove_favorite(current_user.id, mcp_server_id)

    if success:
        # Analytics: 즐겨찾기 제거 이벤트 추적
        try:
            analytics_service.track_favorite_remove(
                mcp_server_id=mcp_server_id,
                user_id=current_user.id
            )
        except Exception as e:
            logger.error(f"Failed to track favorite remove event: {e}")

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

@router.post("/{mcp_server_id}/health-check")
async def check_server_health(
    background_tasks: BackgroundTasks,
    mcp_server_id: int,
    db: Session = Depends(get_db)
):
    """
    MCP 서버의 헬스 체크를 백그라운드에서 시작합니다.
    즉시 응답을 반환하고, GET /{id}로 결과를 확인할 수 있습니다.
    """
    try:
        logger.info(f"Health check requested for server ID: {mcp_server_id}")

        # 서버 존재 확인
        mcp_service = MCPServerService(db)
        mcp_server = mcp_service.get_mcp_server_by_id(mcp_server_id)

        if not mcp_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP Server not found"
            )

        # 백그라운드 태스크로 health check 시작
        async def run_health_check():
            logger.info(f"Starting background health check for server {mcp_server_id}")
            # 새로운 DB 세션 생성 (백그라운드 태스크용)
            from backend.database import SessionLocal
            bg_db = SessionLocal()
            try:
                bg_service = MCPServerService(bg_db)
                result = await bg_service.check_server_health(mcp_server_id)
                logger.info(f"Background health check completed for server {mcp_server_id}: {result}")
            except Exception as e:
                logger.error(f"Background health check error for server {mcp_server_id}: {str(e)}", exc_info=True)
            finally:
                bg_db.close()

        # asyncio task로 생성 (FastAPI background_tasks는 async를 제대로 처리 못함)
        asyncio.create_task(run_health_check())

        # 즉시 응답 반환
        return {
            "id": mcp_server_id,
            "message": "Health check started",
            "status": "checking",
            "current_health_status": mcp_server.health_status,
            "last_health_check": mcp_server.last_health_check.isoformat() if mcp_server.last_health_check else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )