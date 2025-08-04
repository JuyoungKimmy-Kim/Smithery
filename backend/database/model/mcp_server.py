from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class TransportType(str, Enum):
    sse = "sse"
    streamable_http = "streamable-http"
    stdio = "stdio"


class MCPServerStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    private = "private"


class MCPServerProperty(BaseModel):
    name: str
    description: Optional[str] = None
    required: bool
    type: Optional[str] = None
    default: Optional[str] = None


class MCPServerTool(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    parameters: List[MCPServerProperty] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class MCPServerResource(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    url: Optional[str] = None
    created_at: Optional[datetime] = None


class MCPServer(BaseModel):
    id: Optional[int] = None
    github_link: str
    name: str
    description: str
    transport: TransportType = TransportType.stdio
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: MCPServerStatus = MCPServerStatus.pending
    config: dict = Field(default_factory=dict)
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    tools: List[MCPServerTool] = Field(default_factory=list)
    resources: List[MCPServerResource] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MCPServerCreate(BaseModel):
    github_link: str
    name: str
    description: str
    transport: TransportType = TransportType.stdio
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[MCPServerStatus] = None


class MCPServerResponse(BaseModel):
    id: int
    github_link: str
    name: str
    description: str
    transport: TransportType
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: MCPServerStatus
    config: dict
    created_by: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    tools: List[MCPServerTool]
    resources: List[MCPServerResource]
    created_at: datetime
    updated_at: datetime
