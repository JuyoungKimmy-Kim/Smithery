from sqlalchemy import Column, Integer, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class PlaygroundUsage(Base):
    __tablename__ = 'playground_usage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    mcp_server_id = Column(Integer, ForeignKey('mcp_servers.id'), nullable=False)
    query_count = Column(Integer, default=0, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="playground_usage")
    mcp_server = relationship("MCPServer", backref="playground_usage")
