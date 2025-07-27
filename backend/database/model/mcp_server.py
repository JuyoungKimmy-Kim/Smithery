from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class TransportType(str, Enum):
    sse = "sse"
    streamable_http = "streamable-http"
    stdio = "stdio"


class MCPServerProperty(BaseModel):
    name: str
    description: Optional[str] = None
    required: bool


class MCPServerTool(BaseModel):
    name: str
    description: str
    input_properties: List[MCPServerProperty]


class MCPServerResource(BaseModel):
    name: str
    description: str
    url: str


class MCPServer(BaseModel):
    id: str
    github_link: str
    name: str
    description: str
    transport: TransportType
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    tools: List[MCPServerTool] = Field(default_factory=list)
    resources: List[MCPServerResource] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
