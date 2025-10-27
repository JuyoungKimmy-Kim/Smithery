"""
MCP 프록시 서비스
Frontend에서 MCP 서버의 tools를 미리보기할 때 사용하는 프록시 서비스
HTTPS → HTTP Mixed Content 문제와 CORS 문제를 해결
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPProxyService:
    """MCP 서버와 통신하는 프록시 서비스"""
    
    # 공통 타임아웃 설정
    HTTP_TIMEOUT = 10  # HTTP 요청 타임아웃
    STREAM_TIMEOUT = 30  # 스트림 타임아웃
    WEBSOCKET_TIMEOUT = 30  # WebSocket 타임아웃
    STDIO_TIMEOUT = 30  # STDIO 타임아웃
    AUTO_FETCH_TIMEOUT = 60  # 전체 자동 감지 타임아웃 (최대 총 3단계 시도)
    
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
        logger.info(f"[MCP Proxy] Starting fetch_tools - URL: {url}, Protocol: {protocol}")
        
        json_rpc_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "params": {}
        }
        
        try:
            result = None
            if protocol == "http":
                logger.info("[MCP Proxy] Using HTTP protocol")
                result = await MCPProxyService._fetch_http(url, json_rpc_request)
            elif protocol == "http-stream":
                logger.info("[MCP Proxy] Using HTTP-Stream protocol")
                result = await MCPProxyService._fetch_http_stream(url, json_rpc_request)
            elif protocol == "websocket":
                logger.info("[MCP Proxy] Using WebSocket protocol")
                result = await MCPProxyService._fetch_websocket(url, json_rpc_request)
            elif protocol == "stdio":
                logger.info("[MCP Proxy] Using STDIO protocol")
                result = await MCPProxyService._fetch_stdio(url, json_rpc_request)
            else:
                logger.error(f"[MCP Proxy] Unsupported protocol: {protocol}")
                return MCPProxyService._create_error_response(f"Unsupported protocol: {protocol}")
            
            logger.info(f"[MCP Proxy] fetch_tools completed - Success: {result.get('success')}, Tools count: {len(result.get('tools', []))}")
            return result
        except Exception as e:
            logger.error(f"[MCP Proxy] fetch_tools failed: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"Failed to fetch tools: {str(e)}")
    
    @staticmethod
    async def _fetch_http(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP 프로토콜로 tools 가져오기"""
        return await MCPProxyService._fetch_http_auto(url, payload)
    
    @staticmethod
    async def _fetch_http_auto(url: str, req: Dict[str, Any]) -> Dict[str, Any]:
        """
        HTTP 자동 감지: POST → GET → SSE/session
        1. POST (JSON-RPC) 시도
        2. GET-only fallback
        3. Session-based (/mcp → /messages) 시도
        """
        logger.info(f"[HTTP Auto] Starting - URL: {url}")
        
        try:
            return await asyncio.wait_for(
                MCPProxyService._fetch_http_auto_impl(url, req),
                timeout=MCPProxyService.AUTO_FETCH_TIMEOUT
            )
        except (asyncio.TimeoutError, asyncio.CancelledError) as e:
            logger.error(f"[HTTP Auto] Timeout or cancelled: {type(e).__name__}")
            return MCPProxyService._create_error_response(
                f"Request timeout after {MCPProxyService.AUTO_FETCH_TIMEOUT}s"
            )
    
    @staticmethod
    async def _fetch_http_auto_impl(url: str, req: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP 자동 감지 구현부 (내부 메서드)"""
        async with aiohttp.ClientSession() as session:
            # 1️⃣ POST (JSON-RPC)
            try:
                logger.info(f"[HTTP Auto] Attempting POST to {url}")
                async with session.post(
                    url, 
                    json=req,
                    headers={"Accept": "application/json, text/event-stream, application/x-ndjson"},
                    timeout=aiohttp.ClientTimeout(total=MCPProxyService.HTTP_TIMEOUT)
                ) as resp:
                    ctype = resp.headers.get("Content-Type", "")
                    text = await resp.text()
                    logger.info(f"[HTTP Auto] POST response - Status: {resp.status}, Content-Type: {ctype}")
                    
                    if resp.status == 200:
                        if "application/json" in ctype:
                            logger.info("[HTTP Auto] Got JSON response")
                            data = json.loads(text)
                            tools = data.get("result", {}).get("tools", [])
                            logger.info(f"[HTTP Auto] Successfully parsed {len(tools)} tools")
                            return MCPProxyService._create_success_response(tools)
                        
                        if "text/event-stream" in ctype:
                            logger.info("[HTTP Auto] Got SSE stream response")
                            return await MCPProxyService._parse_stream(resp)
                    
                    # Invalid Content-Type 또는 403/405 → GET fallback
                    if "Invalid Content-Type" in text or resp.status in (403, 405):
                        logger.warning(f"[HTTP Auto] POST failed (status: {resp.status}), trying GET fallback")
                        return await MCPProxyService._try_http_get(session, url)
            except (aiohttp.ClientError, asyncio.TimeoutError, asyncio.CancelledError) as e:
                logger.warning(f"[HTTP Auto] POST failed: {type(e).__name__}: {e}, trying GET fallback")
                # CancelledError는 재발생시켜 상위로 전파
                if isinstance(e, asyncio.CancelledError):
                    raise
            
            # 2️⃣ GET-only fallback
            try:
                logger.info("[HTTP Auto] Attempting GET fallback")
                return await MCPProxyService._try_http_get(session, url)
            except asyncio.CancelledError:
                raise  # CancelledError는 그대로 전파
            except Exception as e:
                logger.warning(f"[HTTP Auto] GET fallback failed: {type(e).__name__}: {e}")
            
            # 3️⃣ Session-based (/mcp → /messages)
            try:
                logger.info("[HTTP Auto] Attempting session-based")
                return await MCPProxyService._handle_session_based(session, url)
            except asyncio.CancelledError:
                raise  # CancelledError는 그대로 전파
            except Exception as e:
                logger.error(f"[HTTP Auto] All methods failed: {type(e).__name__}: {e}")
                raise Exception("No valid response from server")
    
    @staticmethod
    async def _try_http_get(session: aiohttp.ClientSession, base_url: str) -> Dict[str, Any]:
        """GET-only MCP 서버 탐지: /, /tools, /tools/list, /list, /tool-list"""
        paths = ["", "/tools", "/tools/list", "/list", "/tool-list"]
        logger.info(f"[HTTP GET] Trying GET fallback with {len(paths)} paths")
        
        for path in paths:
            url = base_url.rstrip("/") + path
            logger.info(f"[HTTP GET] Trying: {url}")
            try:
                async with session.get(
                    url, 
                    headers={"Accept": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=MCPProxyService.HTTP_TIMEOUT)
                ) as r:
                    logger.info(f"[HTTP GET] Response - URL: {url}, Status: {r.status}")
                    if r.status != 200:
                        logger.info(f"[HTTP GET] Non-200 status, skipping")
                        continue
                    
                    txt = await r.text()
                    logger.info(f"[HTTP GET] Response text length: {len(txt)}")
                    
                    try:
                        data = json.loads(txt)
                    except json.JSONDecodeError as e:
                        logger.warning(f"[HTTP GET] JSON decode error: {e}")
                        continue
                    
                    logger.info(f"[HTTP GET] Parsed JSON - Type: {type(data)}")
                    
                    # 다양한 응답 패턴 자동 감지
                    if isinstance(data, list):
                        logger.info(f"[HTTP GET] Detected array response with {len(data)} items")
                        if data and isinstance(data[0], dict) and "name" in data[0]:
                            return MCPProxyService._create_success_response(data, f"Got tools array from {url}")
                    
                    if isinstance(data, dict):
                        if "result" in data and "tools" in data["result"]:
                            tools = data["result"]["tools"]
                            logger.info(f"[HTTP GET] Found tools in result: {len(tools)} items")
                            return MCPProxyService._create_success_response(tools, f"Got tools from {url}")
                        
                        if "tools" in data:
                            tools = data["tools"]
                            logger.info(f"[HTTP GET] Found tools key: {len(tools)} items")
                            return MCPProxyService._create_success_response(tools, f"Got tools from {url}")
                        
                        # tool-like 리스트 자동 추정
                        logger.info(f"[HTTP GET] Searching for tool-like arrays in dict")
                        for k, v in data.items():
                            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                                # name 필드가 있는지 확인
                                if "name" in v[0]:
                                    logger.info(f"[HTTP GET] Found tool-like array in key '{k}' with {len(v)} items")
                                    return MCPProxyService._create_success_response(v, f"Got tools from {k} at {url}")
            
            except aiohttp.ClientError as e:
                logger.warning(f"[HTTP GET] Client error for {url}: {e}")
                continue
        
        logger.error("[HTTP GET] All GET attempts failed")
        return MCPProxyService._create_error_response("GET-only MCP server did not return valid data")
    
    @staticmethod
    async def _handle_session_based(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """세션형 MCP 서버 (/mcp → /messages)"""
        logger.info(f"[Session] Handling session-based MCP - URL: {url}")
        
        if not url.endswith("/mcp"):
            logger.warning("[Session] URL does not end with /mcp")
            raise Exception("Session-based server expected /mcp endpoint")
        
        try:
            async with session.get(
                url,
                headers={"Accept": "text/event-stream"},
                timeout=aiohttp.ClientTimeout(total=MCPProxyService.STREAM_TIMEOUT)
            ) as resp:
                logger.info(f"[Session] Got SSE response - Status: {resp.status}")
                async for line in resp.content:
                    s = line.decode().strip()
                    logger.debug(f"[Session] SSE line: {s}")
                    if s.startswith("data:") and "/messages/" in s:
                        session_path = s[5:].strip()
                        logger.info(f"[Session] Found session path: {session_path}")
                        base = url.split("/mcp")[0]
                        session_url = session_path if session_path.startswith("http") else f"{base}{session_path}"
                        logger.info(f"[Session] Connecting to session URL: {session_url}")
                        return await MCPProxyService._listen_messages(session, session_url)
            
            raise Exception("Session ID not found from /mcp")
        except Exception as e:
            logger.error(f"[Session] Session handling failed: {e}")
            raise
    
    @staticmethod
    async def _listen_messages(session: aiohttp.ClientSession, session_url: str) -> Dict[str, Any]:
        """실제 /messages SSE 구독"""
        logger.info(f"[Messages] Listening to: {session_url}")
        try:
            async with session.get(
                session_url,
                headers={"Accept": "text/event-stream"},
                timeout=aiohttp.ClientTimeout(total=MCPProxyService.STREAM_TIMEOUT)
            ) as r:
                logger.info(f"[Messages] SSE stream connected")
                result = await MCPProxyService._parse_stream(r)
                logger.info(f"[Messages] Stream parsed successfully")
                return result
        except Exception as e:
            logger.error(f"[Messages] Failed to listen: {e}")
            return MCPProxyService._create_error_response(f"Failed to listen to messages stream: {str(e)}")
    
    @staticmethod
    async def _parse_stream(resp: aiohttp.ClientResponse) -> Dict[str, Any]:
        """SSE / NDJSON Stream 파싱"""
        logger.info("[Stream] Starting stream parsing")
        tools = []
        line_count = 0
        
        async for raw in resp.content:
            line_count += 1
            line = raw.decode().strip()
            logger.debug(f"[Stream] Line {line_count}: {line[:100]}")
            
            if not line or line.startswith(":"):
                continue
            
            if line.startswith("data:"):
                line = line[5:].strip()
                if line == "[DONE]":
                    logger.info("[Stream] Received [DONE] signal")
                    break
            
            try:
                obj = json.loads(line)
                logger.debug(f"[Stream] Parsed JSON object: {list(obj.keys())}")
                
                # JSON-RPC 표준
                if "result" in obj and "tools" in obj["result"]:
                    tools = obj["result"]["tools"]
                    logger.info(f"[Stream] Found standard JSON-RPC response with {len(tools)} tools")
                    break
                
                # tools 배열 직접 반환
                if "tools" in obj:
                    tools = obj["tools"]
                    logger.info(f"[Stream] Found tools key with {len(tools)} items")
                    break
                
                # payload가 문자열 JSON일 때
                if "payload" in obj:
                    payload = obj["payload"]
                    logger.info(f"[Stream] Found payload key")
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                        logger.info(f"[Stream] Parsed nested JSON payload")
                    if "tools" in payload:
                        tools = payload["tools"]
                        logger.info(f"[Stream] Found tools in nested payload: {len(tools)} items")
                        break
            
            except json.JSONDecodeError as e:
                logger.debug(f"[Stream] JSON decode error on line {line_count}: {e}")
                continue
        
        if tools:
            logger.info(f"[Stream] Successfully extracted {len(tools)} tools from stream")
            return MCPProxyService._create_success_response(tools, "Tools fetched successfully from stream")
        else:
            logger.warning("[Stream] No tools found in stream response")
            return MCPProxyService._create_error_response("No tools found in stream response")
    
    @staticmethod
    async def _fetch_http_stream(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP-stream (NDJSON or SSE) 프로토콜 지원"""
        logger.info(f"[HTTP Stream] Starting - URL: {url}")
        try:
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
                    logger.info(f"[HTTP Stream] Response - Status: {response.status}, Content-Type: {content_type}")
                    
                    if "application/json" in content_type and response.status == 200:
                        try:
                            data = await response.json()
                            tools = data.get("result", {}).get("tools", [])
                            logger.info(f"[HTTP Stream] Got JSON with {len(tools)} tools")
                            return MCPProxyService._create_success_response(tools)
                        except Exception as e:
                            logger.warning(f"[HTTP Stream] JSON parse failed: {e}")
                    
                    return await MCPProxyService._parse_stream(response)
        except Exception as e:
            logger.error(f"[HTTP Stream] Failed: {e}")
            return MCPProxyService._create_error_response(f"HTTP Stream failed: {str(e)}")
    
    @staticmethod
    async def _fetch_websocket(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 프로토콜로 tools 가져오기"""
        logger.info(f"[WebSocket] Starting - URL: {url}")
        try:
            # http:// -> ws:// 변환
            ws_url = url.replace('http://', 'ws://').replace('https://', 'wss://')
            logger.info(f"[WebSocket] Connecting to: {ws_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    ws_url,
                    timeout=MCPProxyService.WEBSOCKET_TIMEOUT
                ) as ws:
                    logger.info("[WebSocket] Connected")
                    await ws.send_json(payload)
                    logger.info("[WebSocket] Sent request")
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                logger.debug(f"[WebSocket] Received message: {list(data.keys())}")
                                
                                if data.get('id') == payload['id']:
                                    tools = data.get("result", {}).get("tools", [])
                                    logger.info(f"[WebSocket] Got {len(tools)} tools")
                                    return MCPProxyService._create_success_response(tools)
                            except json.JSONDecodeError as e:
                                logger.debug(f"[WebSocket] JSON decode error: {e}")
                                continue
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"[WebSocket] Error: {ws.exception()}")
                            return MCPProxyService._create_error_response(f"WebSocket error: {ws.exception() or 'Unknown error'}")
                        elif msg.type == aiohttp.WSMsgType.CLOSE:
                            logger.warning(f"[WebSocket] Closed: code={msg.data}, reason={msg.extra}")
                            return MCPProxyService._create_error_response(f"WebSocket closed")
                    
                    logger.warning("[WebSocket] No response from server")
                    return MCPProxyService._create_error_response("No response from WebSocket server")
        except aiohttp.ClientError as e:
            logger.error(f"[WebSocket] Connection error: {e}")
            return MCPProxyService._create_error_response(f"WebSocket connection error: {str(e)}")
        except Exception as e:
            logger.error(f"[WebSocket] Failed: {e}")
            return MCPProxyService._create_error_response(f"WebSocket connection failed: {str(e)}")
    
    @staticmethod
    async def _fetch_stdio(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """STDIO 기반 로컬 MCP 서버 실행"""
        logger.info(f"[STDIO] Starting - Command: {command}")
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            req = json.dumps(payload) + "\n"
            logger.info(f"[STDIO] Sending request: {req[:100]}")
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=req.encode()),
                timeout=MCPProxyService.STDIO_TIMEOUT
            )
            
            if stderr:
                logger.warning(f"[STDIO] stderr: {stderr.decode('utf-8')[:200]}")
            
            logger.info(f"[STDIO] Got response - stdout length: {len(stdout)}")
            
            for line in stdout.decode().splitlines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        logger.info(f"[STDIO] Parsed JSON")
                        if data.get('id') == payload['id']:
                            tools = data.get("result", {}).get("tools", [])
                            logger.info(f"[STDIO] Got {len(tools)} tools")
                            return MCPProxyService._create_success_response(tools)
                    except json.JSONDecodeError:
                        continue
            
            error_msg = "No valid JSON response from stdio process"
            if stderr:
                error_msg += f": {stderr.decode('utf-8')[:200]}"
            logger.error(f"[STDIO] {error_msg}")
            return MCPProxyService._create_error_response(error_msg)
            
        except asyncio.TimeoutError:
            logger.error(f"[STDIO] Timeout after {MCPProxyService.STDIO_TIMEOUT}s")
            return MCPProxyService._create_error_response(f"STDIO process timeout")
        except Exception as e:
            logger.error(f"[STDIO] Failed: {e}")
            return MCPProxyService._create_error_response(f"STDIO process failed: {str(e)}")