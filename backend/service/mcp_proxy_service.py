"""
MCP 프록시 서비스
Frontend에서 MCP 서버의 tools를 미리보기할 때 사용하는 프록시 서비스
HTTPS → HTTP Mixed Content 문제와 CORS 문제를 해결
"""

import asyncio
import aiohttp
import json
import subprocess
from typing import Dict, Any, List, Optional


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
        json_rpc_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "params": {}
        }
        
        try:
            if protocol == "http":
                return await MCPProxyService._fetch_http(url, json_rpc_request)
            elif protocol == "http-stream":
                return await MCPProxyService._fetch_http_stream(url, json_rpc_request)
            elif protocol == "websocket":
                return await MCPProxyService._fetch_websocket(url, json_rpc_request)
            elif protocol == "stdio":
                return await MCPProxyService._fetch_stdio(url, json_rpc_request)
            else:
                return {
                    "success": False,
                    "tools": [],
                    "message": f"Unsupported protocol: {protocol}"
                }
        except Exception as e:
            return {
                "success": False,
                "tools": [],
                "message": f"Failed to fetch tools: {str(e)}"
            }
    
    @staticmethod
    async def _fetch_http(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP 프로토콜로 tools 가져오기"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tools = data.get("result", {}).get("tools", [])
                    return {
                        "success": True,
                        "tools": tools,
                        "message": "Tools fetched successfully"
                    }
                else:
                    return {
                        "success": False,
                        "tools": [],
                        "message": f"HTTP request failed with status {response.status}"
                    }
    
    @staticmethod
    async def _fetch_http_stream(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP-Stream (SSE) 프로토콜로 tools 가져오기"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    # JSON 응답인 경우
                    if 'application/json' in content_type:
                        data = await response.json()
                        tools = data.get("result", {}).get("tools", [])
                        return {
                            "success": True,
                            "tools": tools,
                            "message": "Tools fetched successfully"
                        }
                    
                    # SSE 스트림인 경우
                    tools = []
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data:'):
                            try:
                                data_str = line_str[5:].strip()
                                if data_str and data_str != '[DONE]':
                                    data = json.loads(data_str)
                                    
                                    # 다양한 응답 형식 처리
                                    if 'result' in data and 'tools' in data['result']:
                                        tools = data['result']['tools']
                                        break
                                    elif isinstance(data, list) and len(data) > 0:
                                        tools = data
                                        break
                                    elif 'tools' in data:
                                        tools = data['tools']
                                        break
                            except json.JSONDecodeError:
                                continue
                    
                    return {
                        "success": True,
                        "tools": tools,
                        "message": "Tools fetched successfully"
                    }
                else:
                    return {
                        "success": False,
                        "tools": [],
                        "message": f"HTTP-Stream request failed with status {response.status}"
                    }
    
    @staticmethod
    async def _fetch_websocket(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 프로토콜로 tools 가져오기"""
        try:
            # http:// -> ws:// 변환
            ws_url = url.replace('http://', 'ws://').replace('https://', 'wss://')
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(ws_url, timeout=10) as ws:
                    # JSON-RPC 요청 전송
                    await ws.send_json(payload)
                    
                    # 응답 대기
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            # ID가 일치하는 응답만 처리
                            if data.get('id') == payload['id']:
                                tools = data.get("result", {}).get("tools", [])
                                return {
                                    "success": True,
                                    "tools": tools,
                                    "message": "Tools fetched successfully"
                                }
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                    
                    return {
                        "success": False,
                        "tools": [],
                        "message": "No response from WebSocket server"
                    }
        except Exception as e:
            return {
                "success": False,
                "tools": [],
                "message": f"WebSocket connection failed: {str(e)}"
            }
    
    @staticmethod
    async def _fetch_stdio(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """STDIO 프로토콜로 tools 가져오기"""
        try:
            # 명령어를 공백으로 분리
            cmd_parts = command.split()
            if not cmd_parts:
                return {
                    "success": False,
                    "tools": [],
                    "message": "Invalid command"
                }
            
            # 프로세스 실행
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # JSON-RPC 요청 전송
            request_str = json.dumps(payload) + "\n"
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=request_str.encode('utf-8')),
                timeout=10
            )
            
            # 응답 파싱
            if stdout:
                try:
                    data = json.loads(stdout.decode('utf-8'))
                    if data.get('id') == payload['id']:
                        tools = data.get("result", {}).get("tools", [])
                        return {
                            "success": True,
                            "tools": tools,
                            "message": "Tools fetched successfully"
                        }
                except json.JSONDecodeError:
                    pass
            
            return {
                "success": False,
                "tools": [],
                "message": f"STDIO process error: {stderr.decode('utf-8') if stderr else 'Unknown error'}"
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "tools": [],
                "message": "STDIO process timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "tools": [],
                "message": f"STDIO process failed: {str(e)}"
            }

