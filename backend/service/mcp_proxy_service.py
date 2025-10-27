"""
MCP 프록시 서비스
하이브리드 접근: Python MCP SDK 우선 + 수동 HTTP fallback
표준 서버는 SDK로, 비표준 서버는 fallback으로 최대 호환성 보장
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, Any, List
from urllib.parse import urlparse

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamablehttp_client
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPProxyService:
    """
    MCP 서버와 통신하는 프록시 서비스
    하이브리드: SDK 우선 시도 → 실패 시 수동 fallback
    """

    # 타임아웃 설정
    DEFAULT_TIMEOUT = 30
    HTTP_TIMEOUT = 10

    @staticmethod
    def _create_success_response(tools: List[Dict[str, Any]], message: str = "Tools fetched successfully") -> Dict[str, Any]:
        """성공 응답 생성"""
        return {
            "success": True,
            "tools": tools,
            "message": message
        }

    @staticmethod
    def _create_error_response(message: str) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "success": False,
            "tools": [],
            "message": message
        }

    @staticmethod
    async def fetch_tools(url: str, protocol: str) -> Dict[str, Any]:
        """
        MCP 서버에서 tools 목록을 가져옵니다

        Args:
            url: MCP 서버 URL 또는 명령어
            protocol: 프로토콜 타입 (stdio, sse, http, streamable-http, http-stream, websocket)

        Returns:
            Dict containing tools list and status
        """
        logger.info(f"[MCP Proxy] Fetching tools - URL: {url}, Protocol: {protocol}")

        try:
            # 프로토콜 정규화
            normalized_protocol = MCPProxyService._normalize_protocol(protocol)

            if normalized_protocol == "stdio":
                return await MCPProxyService._fetch_stdio(url)
            else:
                # HTTP는 하이브리드 접근
                return await MCPProxyService._fetch_http_hybrid(url)

        except Exception as e:
            logger.error(f"[MCP Proxy] Failed to fetch tools: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"Failed to fetch tools: {str(e)}")

    @staticmethod
    def _normalize_protocol(protocol: str) -> str:
        """프로토콜 이름 정규화"""
        protocol = protocol.lower().strip()

        # HTTP 관련 프로토콜들은 모두 http로 통합
        if protocol in ("http", "http-stream", "sse", "streamable-http", "websocket"):
            return "http"

        return protocol

    @staticmethod
    async def _fetch_stdio(command: str) -> Dict[str, Any]:
        """
        STDIO transport를 사용하여 로컬 MCP 서버에서 tools 가져오기

        Args:
            command: 실행할 명령어 (예: "node server.js" 또는 "python server.py")
        """
        logger.info(f"[STDIO] Starting STDIO transport with command: {command}")

        if not MCP_SDK_AVAILABLE:
            logger.error("[STDIO] MCP SDK is not installed")
            return MCPProxyService._create_error_response(
                "MCP SDK is required for STDIO transport"
            )

        try:
            # 명령어를 파싱
            parts = command.split()
            if not parts:
                return MCPProxyService._create_error_response("Empty command")

            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            # StdioServerParameters 생성
            server_params = StdioServerParameters(
                command=cmd,
                args=args,
                env=None
            )

            logger.info(f"[STDIO] Command: {cmd}, Args: {args}")

            # stdio_client context manager 사용
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # 세션 초기화
                    await asyncio.wait_for(
                        session.initialize(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    logger.info("[STDIO] Session initialized, listing tools")

                    # tools 목록 가져오기
                    result = await asyncio.wait_for(
                        session.list_tools(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    # Tool 객체를 dict로 변환
                    tools = []
                    for tool in result.tools:
                        tool_dict = {
                            "name": tool.name,
                            "description": tool.description,
                        }
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            tool_dict["inputSchema"] = tool.inputSchema
                        tools.append(tool_dict)

                    logger.info(f"[STDIO] Successfully fetched {len(tools)} tools")
                    return MCPProxyService._create_success_response(
                        tools,
                        f"Successfully fetched {len(tools)} tools via STDIO"
                    )

        except asyncio.TimeoutError:
            logger.error(f"[STDIO] Timeout after {MCPProxyService.DEFAULT_TIMEOUT}s")
            return MCPProxyService._create_error_response(
                f"STDIO connection timeout after {MCPProxyService.DEFAULT_TIMEOUT}s"
            )
        except Exception as e:
            logger.error(f"[STDIO] Failed: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"STDIO failed: {str(e)}")

    @staticmethod
    async def _fetch_http_hybrid(url: str) -> Dict[str, Any]:
        """
        하이브리드 HTTP 접근:
        1. MCP SDK 시도 (표준 MCP 서버용)
        2. 실패 시 수동 HTTP fallback (비표준 서버용)
        """
        # 1단계: SDK 시도 (표준 서버)
        if MCP_SDK_AVAILABLE:
            logger.info("[HTTP] Trying MCP SDK (standard servers)")
            result = await MCPProxyService._fetch_http_sdk(url)
            if result.get("success"):
                logger.info("[HTTP] SDK succeeded")
                return result

            logger.warning(f"[HTTP] SDK failed: {result.get('message')}")
            logger.info("[HTTP] Trying manual fallback (non-standard servers)")
        else:
            logger.info("[HTTP] MCP SDK not available, using manual fallback only")

        # 2단계: 수동 HTTP fallback (비표준 서버)
        return await MCPProxyService._fetch_http_manual(url)

    @staticmethod
    async def _fetch_http_sdk(url: str) -> Dict[str, Any]:
        """
        MCP SDK를 사용한 표준 HTTP transport
        """
        logger.info(f"[HTTP SDK] Starting with URL: {url}")

        try:
            # URL 검증
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return MCPProxyService._create_error_response(f"Invalid URL: {url}")

            # streamablehttp_client context manager 사용
            async with streamablehttp_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    # 세션 초기화
                    await asyncio.wait_for(
                        session.initialize(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    logger.info("[HTTP SDK] Session initialized, listing tools")

                    # tools 목록 가져오기
                    result = await asyncio.wait_for(
                        session.list_tools(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    # Tool 객체를 dict로 변환
                    tools = []
                    for tool in result.tools:
                        tool_dict = {
                            "name": tool.name,
                            "description": tool.description,
                        }
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            tool_dict["inputSchema"] = tool.inputSchema
                        tools.append(tool_dict)

                    logger.info(f"[HTTP SDK] Successfully fetched {len(tools)} tools")
                    return MCPProxyService._create_success_response(
                        tools,
                        f"Fetched {len(tools)} tools via SDK (standard MCP)"
                    )

        except asyncio.TimeoutError:
            logger.error(f"[HTTP SDK] Timeout after {MCPProxyService.DEFAULT_TIMEOUT}s")
            return MCPProxyService._create_error_response(
                f"SDK timeout after {MCPProxyService.DEFAULT_TIMEOUT}s"
            )
        except Exception as e:
            logger.error(f"[HTTP SDK] Failed: {str(e)}")
            return MCPProxyService._create_error_response(f"SDK failed: {str(e)}")

    @staticmethod
    async def _fetch_http_manual(url: str) -> Dict[str, Any]:
        """
        수동 HTTP 요청 fallback - 다양한 비표준 MCP 서버 구현 지원
        POST → GET → Stream 순으로 시도
        """
        logger.info(f"[HTTP Manual] Starting with URL: {url}")

        json_rpc_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "params": {}
        }

        async with aiohttp.ClientSession() as session:
            # 1. POST 시도 (표준 JSON-RPC)
            try:
                logger.info("[HTTP Manual] Trying POST request")
                async with session.post(
                    url,
                    json=json_rpc_request,
                    headers={"Accept": "application/json, text/event-stream, application/x-ndjson"},
                    timeout=aiohttp.ClientTimeout(total=MCPProxyService.HTTP_TIMEOUT)
                ) as resp:
                    content_type = resp.headers.get("Content-Type", "")
                    logger.info(f"[HTTP Manual] POST response - Status: {resp.status}, Content-Type: {content_type}")

                    if resp.status == 200:
                        if "application/json" in content_type:
                            data = await resp.json()
                            tools = data.get("result", {}).get("tools", [])
                            if tools:
                                logger.info(f"[HTTP Manual] POST success: {len(tools)} tools")
                                return MCPProxyService._create_success_response(
                                    tools,
                                    f"Fetched {len(tools)} tools via POST (non-standard)"
                                )

                        elif "text/event-stream" in content_type or "application/x-ndjson" in content_type:
                            logger.info("[HTTP Manual] POST returned stream, parsing...")
                            result = await MCPProxyService._parse_stream(resp)
                            if result.get("success"):
                                return result

            except Exception as e:
                logger.warning(f"[HTTP Manual] POST failed: {e}")

            # 2. GET 시도 (REST API 스타일)
            get_paths = ["", "/tools", "/tools/list", "/list"]
            for path in get_paths:
                try:
                    get_url = url.rstrip("/") + path
                    logger.info(f"[HTTP Manual] Trying GET: {get_url}")

                    async with session.get(
                        get_url,
                        headers={"Accept": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=MCPProxyService.HTTP_TIMEOUT)
                    ) as resp:
                        if resp.status != 200:
                            continue

                        data = await resp.json()

                        # 다양한 응답 패턴 감지
                        tools = None
                        if isinstance(data, list) and data and isinstance(data[0], dict) and "name" in data[0]:
                            tools = data
                        elif isinstance(data, dict):
                            if "result" in data and "tools" in data["result"]:
                                tools = data["result"]["tools"]
                            elif "tools" in data:
                                tools = data["tools"]

                        if tools:
                            logger.info(f"[HTTP Manual] GET success: {len(tools)} tools from {get_url}")
                            return MCPProxyService._create_success_response(
                                tools,
                                f"Fetched {len(tools)} tools via GET (non-standard)"
                            )

                except Exception as e:
                    logger.debug(f"[HTTP Manual] GET {path} failed: {e}")
                    continue

            # 3. 모든 시도 실패
            logger.error("[HTTP Manual] All fallback attempts failed")
            return MCPProxyService._create_error_response(
                "Could not fetch tools: tried SDK, POST, and GET methods"
            )

    @staticmethod
    async def _parse_stream(resp: aiohttp.ClientResponse) -> Dict[str, Any]:
        """SSE/NDJSON 스트림 파싱"""
        logger.info("[Stream] Parsing stream response")
        tools = []

        try:
            async for raw in resp.content:
                line = raw.decode().strip()

                if not line or line.startswith(":"):
                    continue

                if line.startswith("data:"):
                    line = line[5:].strip()
                    if line == "[DONE]":
                        break

                try:
                    obj = json.loads(line)

                    # JSON-RPC 표준
                    if "result" in obj and "tools" in obj["result"]:
                        tools = obj["result"]["tools"]
                        break

                    # tools 배열 직접 반환
                    if "tools" in obj:
                        tools = obj["tools"]
                        break

                    # payload 처리
                    if "payload" in obj:
                        payload = obj["payload"]
                        if isinstance(payload, str):
                            payload = json.loads(payload)
                        if "tools" in payload:
                            tools = payload["tools"]
                            break

                except json.JSONDecodeError:
                    continue

            if tools:
                logger.info(f"[Stream] Successfully parsed {len(tools)} tools")
                return MCPProxyService._create_success_response(
                    tools,
                    f"Fetched {len(tools)} tools via stream (non-standard)"
                )
            else:
                return MCPProxyService._create_error_response("No tools found in stream")

        except Exception as e:
            logger.error(f"[Stream] Parsing failed: {e}")
            return MCPProxyService._create_error_response(f"Stream parsing failed: {str(e)}")
