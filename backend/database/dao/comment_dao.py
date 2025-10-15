from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional, List, Dict, Any
from backend.database.model import Comment, User

class CommentDAO:
    def __init__(self, db: Session):
        self.db = db
    
    def create_comment(self, mcp_server_id: int, user_id: int, content: str) -> Comment:
        """새 댓글을 생성합니다."""
        comment = Comment(
            mcp_server_id=mcp_server_id,
            user_id=user_id,
            content=content
        )
        
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment
    
    def get_comments_by_mcp_server(self, mcp_server_id: int, limit: int = None, offset: int = 0) -> List[Comment]:
        """특정 MCP 서버의 댓글 목록을 조회합니다. (삭제된 댓글도 포함)"""
        query = self.db.query(Comment).options(
            joinedload(Comment.user)
        ).filter(Comment.mcp_server_id == mcp_server_id).order_by(desc(Comment.created_at))
        
        if limit:
            query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_comment_by_id(self, comment_id: int) -> Optional[Comment]:
        """ID로 댓글을 조회합니다."""
        return self.db.query(Comment).options(
            joinedload(Comment.user)
        ).filter(Comment.id == comment_id).first()
    
    def update_comment(self, comment_id: int, content: str, user_id: int) -> Optional[Comment]:
        """댓글을 수정합니다. (작성자만 수정 가능)"""
        comment = self.db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.user_id == user_id,
            Comment.is_deleted == False  # 삭제된 댓글은 수정 불가
        ).first()
        
        if comment:
            comment.content = content
            self.db.commit()
            self.db.refresh(comment)
        
        return comment
    
    def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """댓글을 소프트 삭제합니다. (작성자만 삭제 가능)"""
        comment = self.db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.user_id == user_id,
            Comment.is_deleted == False  # 이미 삭제된 댓글은 다시 삭제 불가
        ).first()
        
        if comment:
            comment.content = None  # 내용을 NULL로 설정
            comment.is_deleted = True  # 삭제 표시
            self.db.commit()
            return True
        
        return False
    
    def get_comment_count_by_mcp_server(self, mcp_server_id: int) -> int:
        """특정 MCP 서버의 댓글 수를 조회합니다."""
        return self.db.query(Comment).filter(Comment.mcp_server_id == mcp_server_id).count()
    
    def is_comment_owner(self, comment_id: int, user_id: int) -> bool:
        """사용자가 댓글의 작성자인지 확인합니다."""
        comment = self.db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.user_id == user_id,
            Comment.is_deleted == False  # 삭제된 댓글은 소유권 확인 불가
        ).first()
        
        return comment is not None
