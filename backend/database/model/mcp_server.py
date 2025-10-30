from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from .tag import mcp_server_tags

class MCPServer(Base):
    __tablename__ = 'mcp_servers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    github_link = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    status = Column(String(20), default='pending')
    protocol = Column(String(20), nullable=False)
    server_url = Column(String(500), nullable=True)
    config = Column(JSON, nullable=True)
    announcement = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    health_status = Column(String(20), default='unknown')
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    owner = relationship("User", back_populates="mcp_servers")
    tools = relationship("MCPServerTool", back_populates="mcp_server", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=mcp_server_tags, backref="mcp_servers")
    favorites = relationship("UserFavorite", back_populates="mcp_server")

class MCPServerTool(Base):
    __tablename__ = 'mcp_server_tools'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    mcp_server_id = Column(Integer, ForeignKey('mcp_servers.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    mcp_server = relationship("MCPServer", back_populates="tools")
    parameters = relationship("MCPServerProperty", back_populates="tool", cascade="all, delete-orphan")

class MCPServerProperty(Base):
    __tablename__ = 'mcp_server_properties'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(50), nullable=True)
    required = Column(Boolean, default=False)
    tool_id = Column(Integer, ForeignKey('mcp_server_tools.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tool = relationship("MCPServerTool", back_populates="parameters")
