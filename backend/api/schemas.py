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

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: str
    avatar_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# MCP Server 관련 스키마
class MCPServerCreate(BaseModel):
    name: str
    github_link: str
    description: str
    category: str
    tags: Optional[str] = None  # 콤마로 구분된 태그 문자열
    config: Optional[Dict[str, Any]] = None

class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

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
    
    class Config:
        from_attributes = True

class MCPServerResponse(BaseModel):
    id: int
    name: str
    github_link: str
    description: str
    category: str
    status: str
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

# 관리자 관련 스키마
class AdminApprovalRequest(BaseModel):
    mcp_server_id: int
    action: str  # 'approve' 또는 'reject'

# Forward references 해결
MCPServerToolResponse.model_rebuild()
MCPServerResponse.model_rebuild() 