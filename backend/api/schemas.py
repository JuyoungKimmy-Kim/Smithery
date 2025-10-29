from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

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
    nickname: str
    is_admin: str
    avatar_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MCPServerPropertyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    required: bool = False

class MCPServerToolCreate(BaseModel):
    name: str
    description: str
    parameters: List[MCPServerPropertyCreate] = []

class MCPServerCreate(BaseModel):
    name: str
    github_link: str
    description: str
    category: Optional[str] = None
    protocol: str
    server_url: Optional[str] = None
    tags: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tools: Optional[List[MCPServerToolCreate]] = []

class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    protocol: Optional[str] = None
    server_url: Optional[str] = None
    tags: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tools: Optional[List[MCPServerToolCreate]] = []

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
    type: Optional[str] = None
    required: bool = False
    
    class Config:
        from_attributes = True

class MCPServerResponse(BaseModel):
    id: int
    name: str
    github_link: str
    description: str
    category: Optional[str] = None
    status: str
    protocol: str
    server_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    announcement: Optional[str] = None
    health_status: str = "unknown"
    last_health_check: Optional[datetime] = None
    tools: List[MCPServerToolResponse] = []
    tags: List['TagResponse'] = []
    owner: Optional[UserResponse] = None
    favorites_count: int = 0
    
    class Config:
        from_attributes = True

class TagResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    keyword: str
    category: Optional[str] = None
    status: str = 'approved'

class SearchResponse(BaseModel):
    mcp_servers: List[MCPServerResponse]
    total_count: int

class FavoriteRequest(BaseModel):
    mcp_server_id: int

class FavoriteResponse(BaseModel):
    success: bool
    message: str

class AdminApprovalRequest(BaseModel):
    mcp_server_id: int
    action: str

class PreviewToolsRequest(BaseModel):
    url: str
    protocol: str

class PreviewToolResponse(BaseModel):
    name: str
    description: Optional[str] = None
    inputSchema: Optional[Dict[str, Any]] = None

class PreviewToolsResponse(BaseModel):
    tools: List[PreviewToolResponse]
    success: bool
    message: Optional[str] = None

class AnnouncementRequest(BaseModel):
    announcement: Optional[str] = None
    
    @validator('announcement')
    def validate_announcement_length(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('Announcement must be 1000 characters or less')
        return v
