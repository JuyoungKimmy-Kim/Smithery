from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from typing import Optional

from backend.database import get_db
from backend.database.model import User, Comment
from backend.database.dao.comment_dao import CommentDAO
from backend.service.notification_service import NotificationService
from backend.api.auth import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])

# Pydantic 스키마
class CommentCreate(BaseModel):
    content: str
    rating: float

class CommentUpdate(BaseModel):
    content: str
    rating: Optional[float] = None

class CommentResponse(BaseModel):
    id: int
    content: str
    is_deleted: bool
    user_id: int
    created_at: str
    updated_at: str
    user_nickname: str
    user_avatar_url: str
    rating: float
    
    class Config:
        from_attributes = True

@router.post("/mcp-servers/{mcp_server_id}/comments", response_model=CommentResponse)
async def create_comment(
    mcp_server_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """MCP 서버에 댓글을 생성합니다."""
    comment_dao = CommentDAO(db)
    
    # rating 검증 (0~5, 0.5 단위)
    if comment_data.rating < 0 or comment_data.rating > 5:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="rating must be between 0 and 5")
    if abs((comment_data.rating * 2) - round(comment_data.rating * 2)) > 1e-9:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="rating must be in 0.5 increments")

    # 댓글 생성
    comment = comment_dao.create_comment(
        mcp_server_id=mcp_server_id,
        user_id=current_user.id,
        content=comment_data.content,
        rating=comment_data.rating
    )

    # 알림 생성 (MCP 소유자에게)
    notification_service = NotificationService(db)
    notification_service.create_comment_notification(
        mcp_server_id=mcp_server_id,
        commenter_user_id=current_user.id
    )

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        is_deleted=comment.is_deleted,
        user_id=comment.user_id,
        created_at=comment.created_at.isoformat(),
        updated_at=comment.updated_at.isoformat() if comment.updated_at else comment.created_at.isoformat(),
        user_nickname=current_user.nickname,
        user_avatar_url=current_user.avatar_url or '/image/avatar1.jpg'
        , rating=float(comment.rating)
    )

@router.get("/mcp-servers/{mcp_server_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    mcp_server_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """특정 MCP 서버의 댓글 목록을 조회합니다."""
    comment_dao = CommentDAO(db)
    
    comments = comment_dao.get_comments_by_mcp_server(
        mcp_server_id=mcp_server_id,
        limit=limit,
        offset=offset
    )
    
    return [
        CommentResponse(
            id=comment.id,
            content=comment.content if not comment.is_deleted else "작성자의 요청으로 삭제된 댓글입니다.",
            is_deleted=comment.is_deleted,
            user_id=comment.user_id,
            created_at=comment.created_at.isoformat(),
            updated_at=comment.updated_at.isoformat() if comment.updated_at else comment.created_at.isoformat(),
            user_nickname=comment.user.nickname,
            user_avatar_url=comment.user.avatar_url or '/image/avatar1.jpg',
            rating=float(comment.rating)
        )
        for comment in comments
    ]

@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """댓글을 수정합니다. (작성자만 수정 가능)"""
    comment_dao = CommentDAO(db)
    
    # rating 검증 (선택 입력)
    if comment_data.rating is not None:
        if comment_data.rating < 0 or comment_data.rating > 5:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="rating must be between 0 and 5")
        if abs((comment_data.rating * 2) - round(comment_data.rating * 2)) > 1e-9:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="rating must be in 0.5 increments")

    # 댓글 수정
    comment = comment_dao.update_comment(
        comment_id=comment_id,
        content=comment_data.content,
        user_id=current_user.id,
        rating=comment_data.rating
    )
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="댓글을 찾을 수 없거나 수정 권한이 없습니다."
        )
    
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        is_deleted=comment.is_deleted,
        user_id=comment.user_id,
        created_at=comment.created_at.isoformat(),
        updated_at=comment.updated_at.isoformat() if comment.updated_at else comment.created_at.isoformat(),
        user_nickname=current_user.nickname,
        user_avatar_url=current_user.avatar_url or '/image/avatar1.jpg',
        rating=float(comment.rating)
    )

@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """댓글을 삭제합니다. (작성자만 삭제 가능)"""
    comment_dao = CommentDAO(db)
    
    # 댓글 삭제
    success = comment_dao.delete_comment(
        comment_id=comment_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="댓글을 찾을 수 없거나 삭제 권한이 없습니다."
        )
    
    return {"message": "댓글이 성공적으로 삭제되었습니다."}

@router.get("/mcp-servers/{mcp_server_id}/count")
async def get_comment_count(
    mcp_server_id: int,
    db: Session = Depends(get_db)
):
    """특정 MCP 서버의 댓글 수를 조회합니다."""
    comment_dao = CommentDAO(db)
    
    count = comment_dao.get_comment_count_by_mcp_server(mcp_server_id)
    
    return {"count": count}