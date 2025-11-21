from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 알림을 받는 유저
    type = Column(String(50), nullable=False)  # 'comment', 'favorite', 'status_change', 'new_mcp'
    message = Column(Text, nullable=False)  # 알림 메시지 (예: "XXX님이 XXX mcp를 즐겨찾기에 추가하였습니다")
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관련 정보 (선택적)
    mcp_server_id = Column(Integer, ForeignKey('mcp_servers.id'), nullable=True)  # 관련 MCP 서버
    related_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 액션을 수행한 유저

    # 관계
    user = relationship("User", foreign_keys=[user_id], backref="notifications")
    mcp_server = relationship("MCPServer", backref="notifications")
    related_user = relationship("User", foreign_keys=[related_user_id])
