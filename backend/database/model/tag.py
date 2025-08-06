from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.sql import func
from .base import Base

# MCP Server와 Tag의 다대다 관계를 위한 중간 테이블
mcp_server_tags = Table(
    'mcp_server_tags',
    Base.metadata,
    Column('mcp_server_id', Integer, ForeignKey('mcp_servers.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 