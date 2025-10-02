"""
MCP 프록시 서비스
Frontend에서 MCP 서버의 tools를 미리보기할 때 사용하는 프록시 서비스
HTTPS → HTTP Mixed Content 문제와 CORS 문제를 해결
Transport 디자인 패턴을 사용하여 모든 프로토콜을 일관되게 처리
"""

import asyncio
from typing import Dict, Any, List, Optional
from .transport import create_transport, JsonRpcClient, Transport


class MCPProxyService:
    """MCP 서버와 통신하는 프록시 서비스"""
    
    @staticmethod
    async def fetch_tools(url: str, protocol: str) -> Dict[str, Any]:
        """
        MCP 서버에서 tools 목록을 가져옵니다
        
        Args:
            url: MCP 서버 URL 또는 명령어
            protocol: 프로토콜 타입 (http, http-stream, websocket, stdio)
        
        Returns:
            Dict containing tools list and status
        """
        transport: Optional[Transport] = None
        try:
            # Transport 생성
            transport = create_transport(protocol, url)
            
            # JSON-RPC 클라이언트 생성
            client = JsonRpcClient(transport)
            
            # tools/list 요청
            response = await client.request("tools/list")
            
            # 응답 처리
            if "error" in response:
                return {
                    "success": False,
                    "tools": [],
                    "message": response["error"].get("message", "Unknown error")
                }
            
            tools = response.get("result", {}).get("tools", [])
            return {
                "success": True,
                "tools": tools,
                "message": "Tools fetched successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "tools": [],
                "message": f"Failed to fetch tools: {str(e)}"
            }
        finally:
            # Transport 정리
            if transport:
                await transport.close()

