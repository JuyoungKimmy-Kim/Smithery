from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

# User 관련 스키마
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ADLoginRequest(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: str
    avatar_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Tool 관련 스키마
class MCPServerPropertyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = None  # type 필드 추가
    required: bool = False

class MCPServerToolCreate(BaseModel):
    name: str
    description: str
    parameters: List[MCPServerPropertyCreate] = []

# MCP Server 관련 스키마
class MCPServerCreate(BaseModel):
    name: str
    github_link: str
    description: str
    category: str
    protocol: str  # 프로토콜 타입 추가
    tags: Optional[str] = None  # 콤마로 구분된 태그 문자열
    config: Optional[Dict[str, Any]] = None
    tools: Optional[List[MCPServerToolCreate]] = []  # tools 추가

class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    protocol: Optional[str] = None  # 프로토콜 타입 추가
    tags: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tools: Optional[List[MCPServerToolCreate]] = []  # tools 추가

class MCPServerToolResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parameters: List['MCPServerPropertyResponse'] = []
    
    class Config:
        from_attributes = True

class MCPServerPropertyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    type: Optional[str] = None  # type 필드 추가
    required: bool = False
    
    class Config:
        from_attributes = True

class MCPServerResponse(BaseModel):
    id: int
    name: str
    github_link: str
    description: str
    category: str
    status: str
    protocol: str  # 프로토콜 타입 추가
    config: Optional[Dict[str, Any]] = None
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tools: List[MCPServerToolResponse] = []
    tags: List['TagResponse'] = []
    owner: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

class TagResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

# 검색 관련 스키마
class SearchRequest(BaseModel):
    keyword: str
    category: Optional[str] = None
    status: str = 'approved'

class SearchResponse(BaseModel):
    mcp_servers: List[MCPServerResponse]
    total_count: int

# 즐겨찾기 관련 스키마
class FavoriteRequest(BaseModel):
    mcp_server_id: int

class FavoriteResponse(BaseModel):
    success: bool
    message: str

# 관리자 승인 관련 스키마
class AdminApprovalRequest(BaseModel):
    mcp_server_id: int
    action: str  # 'approve' 또는 'reject'
