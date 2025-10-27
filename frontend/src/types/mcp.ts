export enum TransportType {
  SSE = "sse",
  STREAMABLE_HTTP = "streamable-http",
  STDIO = "stdio"
}

export enum ProtocolType {
  HTTP = "http",
  HTTP_STREAM = "http-stream", 
  WEBSOCKET = "websocket",
  STDIO = "stdio"
}

export interface MCPServerProperty {
  name: string;
  description?: string;
  type?: string;
  required: boolean;
}

export interface MCPServerTool {
  name: string;
  description: string;
  parameters: MCPServerProperty[];
  // MCP 서버에서 받은 원본 데이터를 위한 선택적 속성들
  inputSchema?: {
    type: string;
    properties?: { [key: string]: any };
    required?: string[];
  };
}

export interface MCPServerResource {
  name: string;
  description: string;
  url: string;
}

export interface User {
  id: number;
  username: string;
  nickname: string;
  email: string;
  avatar_url?: string;
}

export interface MCPServer {
  id: string;
  github_link: string;
  name: string;
  description: string;
  transport: TransportType;
  protocol: ProtocolType;
  category?: string;
  tags?: string[];
  status?: string;
  announcement?: string;
  tools: MCPServerTool[];
  resources: MCPServerResource[];
  config?: any;
  created_at?: string;
  updated_at?: string;
  owner?: User;
  owner_id?: number;
}

export interface Post {
  category: string;
  tags: string;
  title: string;
  desc: string;
  date: string;
  author: {
    img: string;
    name: string;
  };
} 