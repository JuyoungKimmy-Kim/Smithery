"""
MCP 프록시 서비스
Frontend에서 MCP 서버의 tools를 미리보기할 때 사용하는 프록시 서비스
HTTPS → HTTP Mixed Content 문제와 CORS 문제를 해결
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


class MCPProxyService:
    """MCP 서버와 통신하는 프록시 서비스"""
    
    # 공통 타임아웃 설정
    HTTP_TIMEOUT = 10  # HTTP 요청 타임아웃
    STREAM_TIMEOUT = 30  # 스트림 타임아웃
    WEBSOCKET_TIMEOUT = 30  # WebSocket 타임아웃
    STDIO_TIMEOUT = 30  # STDIO 타임아웃
    
    @staticmethod
    def _create_success_response(tools: list, message: str = "Tools fetched successfully") -> Dict[str, Any]:
        """성공 응답 생성"""
        return {
            "success": True,
            "tools": tools,
            "message": message
        }
    
    @staticmethod
    def _create_error_response(message: str, tools: list = None) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "success": False,
            "tools": tools or [],
            "message": message
        }
    
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
                return MCPProxyService._create_error_response(f"Unsupported protocol: {protocol}")
        except Exception as e:
            return MCPProxyService._create_error_response(f"Failed to fetch tools: {str(e)}")
    
    @staticmethod
    async def _fetch_http(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP 프로토콜로 tools 가져오기 (POST → GET fallback → Stream)"""
        return await MCPProxyService._fetch_http_auto(url, payload)
    
    @staticmethod
    async def _fetch_http_auto(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        HTTP transport 자동 감지 및 fallback:
        1️⃣ POST 시도
        2️⃣ 3xx Redirect 처리
        3️⃣ 405/403 시 GET fallback (여러 엔드포인트 시도)
        4️⃣ Content-Type 기반 자동 감지
        """
        async with aiohttp.ClientSession() as session:
            try:
                # 1️⃣ 기본 POST 요청
                async with session.post(
                    url,
                    json=payload,
                    headers={
                        "Accept": "application/json, text/event-stream, application/x-ndjson"
                    },
                    timeout=aiohttp.ClientTimeout(total=MCPProxyService.HTTP_TIMEOUT),
                    allow_redirects=False
                ) as response:
                    
                    # 3xx Redirect 처리
                    if response.status in (301, 302, 303, 307, 308):
                        redirect_url = response.headers.get("Location")
                        if redirect_url:
                            return await MCPProxyService._fetch_http_auto(redirect_url, payload)
                    
                    # 405 / 403 → GET fallback
                    if response.status in (403, 405):
                        return await MCPProxyService._try_http_get(session, url)
                    
                    # 정상 응답 처리
                    content_type = response.headers.get("Content-Type", "")
                    
                    if response.status == 200:
                        if "application/json" in content_type:
                            try:
                                data = await response.json()
                                tools = data.get("result", {}).get("tools", [])
                                return MCPProxyService._create_success_response(tools)
                            except Exception as e:
                                return MCPProxyService._create_error_response(f"Failed to parse JSON: {str(e)}")
                        elif "application/x-ndjson" in content_type or "text/event-stream" in content_type:
                            return await MCPProxyService._parse_stream_response(response)
                        else:
                            text = await response.text()
                            return MCPProxyService._create_error_response(f"Unknown content-type: {content_type}, response: {text[:100]}")
                    
                    # 기타 상태 코드에 대해서는 HTTP-stream 시도
                    return await MCPProxyService._fetch_http_stream(url, payload)
                    
            except aiohttp.ClientError as e:
                return MCPProxyService._create_error_response(f"HTTP client error: {str(e)}")
            except Exception as e:
                return MCPProxyService._create_error_response(f"HTTP request failed: {str(e)}")
    
    @staticmethod
    async def _try_http_get(session: aiohttp.ClientSession, base_url: str) -> Dict[str, Any]:
        """GET fallback: 여러 엔드포인트 시도"""
        candidates = ["", "/tools", "/tools/list"]
        for path in candidates:
            test_url = base_url.rstrip("/") + path
            try:
                async with session.get(
                    test_url,
                    headers={"Accept": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=MCPProxyService.HTTP_TIMEOUT)
                ) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            tools = data.get("result", {}).get("tools", [])
                            return MCPProxyService._create_success_response(tools, f"Tools fetched successfully via GET {test_url}")
                        except aiohttp.ContentTypeError:
                            text = await response.text()
                            continue
                        except Exception as e:
                            continue
            except Exception:
                continue
        
        return MCPProxyService._create_error_response(f"GET fallback failed for all endpoints: {candidates}")
    
    @staticmethod
    async def _parse_stream_response(response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Parse NDJSON or SSE stream."""
        tools = []
        async for raw_line in response.content:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            if line.startswith("data:"):
                line = line[5:].strip()
                if line == "[DONE]":
                    break
            try:
                obj = json.loads(line)
                if "result" in obj and "tools" in obj["result"]:
                    tools = obj["result"]["tools"]
                    break
                elif "tools" in obj:
                    tools = obj["tools"]
                    break
                elif isinstance(obj, list) and len(obj) > 0:
                    tools = obj
                    break
            except json.JSONDecodeError:
                continue
        
        if tools:
            return MCPProxyService._create_success_response(tools, "Tools fetched successfully from stream")
        else:
            return MCPProxyService._create_error_response("No tools found in stream response")
    
    @staticmethod
    async def _fetch_http_stream(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        HTTP-stream (NDJSON or SSE) 프로토콜 지원.
        서버가 'application/x-ndjson' 또는 'text/event-stream'으로 응답하는 경우 모두 커버.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={
                    "Accept": "application/x-ndjson, text/event-stream, application/json"
                },
                timeout=aiohttp.ClientTimeout(total=MCPProxyService.STREAM_TIMEOUT)
            ) as response:
                content_type = response.headers.get("Content-Type", "")

                # 1️⃣ 일반 JSON 응답
                if "application/json" in content_type and response.status == 200:
                    try:
                        data = await response.json()
                        tools = data.get("result", {}).get("tools", [])
                        return MCPProxyService._create_success_response(tools)
                    except Exception:
                        pass

                # 2️⃣ 스트림 응답 (NDJSON / SSE)
                return await MCPProxyService._parse_stream_response(response)
    
    @staticmethod
    async def _fetch_websocket(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 프로토콜로 tools 가져오기"""
        try:
            # http:// -> ws:// 변환
            ws_url = url.replace('http://', 'ws://').replace('https://', 'wss://')
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    ws_url, 
                    timeout=MCPProxyService.WEBSOCKET_TIMEOUT
                ) as ws:
                    # JSON-RPC 요청 전송
                    await ws.send_json(payload)
                    
                    # 응답 대기
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                
                                # ID가 일치하는 응답만 처리
                                if data.get('id') == payload['id']:
                                    tools = data.get("result", {}).get("tools", [])
                                    return MCPProxyService._create_success_response(tools)
                            except json.JSONDecodeError:
                                continue
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            return MCPProxyService._create_error_response(
                                f"WebSocket error: {ws.exception() or 'Unknown error'}"
                            )
                        elif msg.type == aiohttp.WSMsgType.CLOSE:
                            return MCPProxyService._create_error_response(
                                f"WebSocket closed: code={msg.data}, reason={msg.extra}"
                            )
                    
                    return MCPProxyService._create_error_response("No response from WebSocket server")
        except aiohttp.ClientError as e:
            return MCPProxyService._create_error_response(f"WebSocket connection error: {str(e)}")
        except Exception as e:
            return MCPProxyService._create_error_response(f"WebSocket connection failed: {str(e)}")
    
    @staticmethod
    async def _fetch_stdio(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        stdio 기반 로컬 MCP 서버 실행 후 JSON-RPC 송수신.
        예: command='node my_mcp_server.js' 또는 './mcp-server'
        """
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            req = json.dumps(payload) + "\n"
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=req.encode()),
                timeout=MCPProxyService.STDIO_TIMEOUT
            )

            if stderr:
                # stderr는 로깅만 하고 무시
                stderr_msg = stderr.decode('utf-8')[:200]
            else:
                stderr_msg = None

            # stdout에서 JSON 응답 찾기
            for line in stdout.decode().splitlines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get('id') == payload['id']:
                            tools = data.get("result", {}).get("tools", [])
                            return MCPProxyService._create_success_response(tools)
                    except json.JSONDecodeError:
                        continue
            
            error_msg = f"No valid JSON response from stdio process"
            if stderr_msg:
                error_msg += f": {stderr_msg}"
            return MCPProxyService._create_error_response(error_msg)
            
        except asyncio.TimeoutError:
            return MCPProxyService._create_error_response(
                f"STDIO process timeout after {MCPProxyService.STDIO_TIMEOUT}s"
            )
        except Exception as e:
            return MCPProxyService._create_error_response(f"STDIO process failed: {str(e)}")

