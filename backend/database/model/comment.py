from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mcp_server_id = Column(Integer, ForeignKey('mcp_servers.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=True)  # 삭제된 댓글은 NULL로 설정
    is_deleted = Column(Boolean, default=False, nullable=False)
    rating = Column(Numeric(2, 1), nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    mcp_server = relationship("MCPServer", backref="comments")
    user = relationship("User", backref="comments")
