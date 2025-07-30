export enum TransportType {
  SSE = "sse",
  STREAMABLE_HTTP = "streamable-http",
  STDIO = "stdio"
}

export interface MCPServerProperty {
  name: string;
  description?: string;
  required: boolean;
}

export interface MCPServerTool {
  name: string;
  description: string;
  input_properties: MCPServerProperty[];
}

export interface MCPServerResource {
  name: string;
  description: string;
  url: string;
}

export interface MCPServer {
  id: string;
  github_link: string;
  name: string;
  description: string;
  transport: TransportType;
  category?: string;
  tags?: string[];
  status?: string;
  tools: MCPServerTool[];
  resources: MCPServerResource[];
  config?: any;
  created_at?: string;
  updated_at?: string;
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