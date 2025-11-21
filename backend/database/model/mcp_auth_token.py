"""
MCP Auth Token Model
Stores encrypted authentication tokens for MCP servers per user
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from backend.database.database import Base


class MCPAuthToken(Base):
    """
    Authentication tokens for MCP servers
    Tokens are encrypted before storage for security
    """
    __tablename__ = "mcp_auth_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mcp_server_id = Column(Integer, ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False)
    token_encrypted = Column(Text, nullable=False)  # Encrypted token
    token_hint = Column(String(10), nullable=True)  # Last 4 chars or hint
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<MCPAuthToken(id={self.id}, user_id={self.user_id}, mcp_server_id={self.mcp_server_id})>"
