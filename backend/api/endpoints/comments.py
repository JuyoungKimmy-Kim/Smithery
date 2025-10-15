from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field, field_validator

from backend.database import get_db
from backend.database.model import User, Comment
from backend.database.dao.comment_dao import CommentDAO
from backend.api.auth import get_current_user
from backend.utils.rate_limiter import rate_limiter

router = APIRouter(prefix="/comments", tags=["comments"])

# Pydantic 스키마
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="댓글 내용 (최대 500자)")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('댓글 내용을 입력해주세요.')
        if len(v) > 500:
            raise ValueError('댓글은 500자를 초과할 수 없습니다.')
        return v.strip()

class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="댓글 내용 (최대 500자)")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('댓글 내용을 입력해주세요.')
        if len(v) > 500:
            raise ValueError('댓글은 500자를 초과할 수 없습니다.')
        return v.strip()

class CommentResponse(BaseModel):
    id: int
    content: str
    is_deleted: bool
    user_id: int
    created_at: str
    updated_at: str
    user_nickname: str
    
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
    # Rate Limiting: 1분당 최대 5개 댓글 생성 가능
    rate_limiter.check_rate_limit(
        user_id=current_user.id,
        max_requests=5,
        window_seconds=60
    )
    
    comment_dao = CommentDAO(db)
    
    # 댓글 생성
    comment = comment_dao.create_comment(
        mcp_server_id=mcp_server_id,
        user_id=current_user.id,
        content=comment_data.content
    )
    
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        is_deleted=comment.is_deleted,
        user_id=comment.user_id,
        created_at=comment.created_at.isoformat(),
        updated_at=comment.updated_at.isoformat() if comment.updated_at else comment.created_at.isoformat(),
        user_nickname=current_user.nickname
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
            user_nickname=comment.user.nickname
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
    # Rate Limiting: 1분당 최대 10개 댓글 수정 가능
    rate_limiter.check_rate_limit(
        user_id=current_user.id,
        max_requests=10,
        window_seconds=60
    )
    
    comment_dao = CommentDAO(db)
    
    # 댓글 수정
    comment = comment_dao.update_comment(
        comment_id=comment_id,
        content=comment_data.content,
        user_id=current_user.id
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
        user_nickname=current_user.nickname
    )

@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """댓글을 삭제합니다. (작성자만 삭제 가능)"""
    # Rate Limiting: 1분당 최대 10개 댓글 삭제 가능
    rate_limiter.check_rate_limit(
        user_id=current_user.id,
        max_requests=10,
        window_seconds=60
    )
    
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