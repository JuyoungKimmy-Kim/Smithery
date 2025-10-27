"""
MCP 프록시 서비스
Inspector의 구현을 최대한 그대로 따라서 구현
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client
    try:
        # streamablehttp_client가 없을 수도 있음
        from mcp.client.streamable_http import streamablehttp_client
        HAS_STREAMABLE_HTTP = True
    except ImportError:
        HAS_STREAMABLE_HTTP = False
        # SSE로 대체
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False
    HAS_STREAMABLE_HTTP = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPProxyService:
    """
    MCP 서버와 통신하는 프록시 서비스
    Inspector처럼 SDK를 직접 사용
    """

    # 타임아웃 설정
    DEFAULT_TIMEOUT = 60
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
        Inspector의 createTransport와 동일한 패턴

        Args:
            url: MCP 서버 URL 또는 명령어
            protocol: 프로토콜 타입 (stdio, sse, streamable-http)

        Returns:
            Dict containing tools list and status
        """
        logger.info(f"[MCP Proxy] Fetching tools - URL: {url}, Protocol: {protocol}")

        if not MCP_SDK_AVAILABLE:
            logger.error("MCP SDK is not installed")
            return MCPProxyService._create_error_response(
                "MCP SDK is not installed. Please install with: pip install mcp[cli]"
            )

        try:
            # 프로토콜 정규화
            normalized_protocol = MCPProxyService._normalize_protocol(protocol)

            # Inspector의 createTransport처럼 프로토콜에 따라 분기
            if normalized_protocol == "stdio":
                return await MCPProxyService._fetch_stdio(url)
            elif normalized_protocol == "sse":
                return await MCPProxyService._fetch_sse(url)
            else:
                # streamable-http (기본값)
                return await MCPProxyService._fetch_streamable_http(url)

        except Exception as e:
            logger.error(f"[MCP Proxy] Failed to fetch tools: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"Failed to fetch tools: {str(e)}")

    @staticmethod
    def _normalize_protocol(protocol: str) -> str:
        """프로토콜 이름 정규화 - Inspector와 동일"""
        protocol = protocol.lower().strip()

        # Inspector는 stdio, sse, streamable-http 3가지만 지원
        if protocol in ("stdio",):
            return "stdio"
        elif protocol in ("sse",):
            return "sse"
        else:
            # 나머지는 모두 streamable-http
            return "streamable-http"

    @staticmethod
    async def _fetch_stdio(command: str) -> Dict[str, Any]:
        """
        STDIO transport - Inspector의 StdioClientTransport와 동일
        """
        logger.info(f"[STDIO] Starting with command: {command}")

        try:
            parts = command.split()
            if not parts:
                return MCPProxyService._create_error_response("Empty command")

            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            server_params = StdioServerParameters(
                command=cmd,
                args=args,
                env=None
            )

            logger.info(f"[STDIO] Command={cmd}, Args={args}")

            # Inspector: await transport.start()
            # Python: async with stdio_client
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    logger.info("[STDIO] Initializing session...")

                    await asyncio.wait_for(
                        session.initialize(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    logger.info("[STDIO] Listing tools...")

                    result = await asyncio.wait_for(
                        session.list_tools(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    tools = MCPProxyService._convert_tools(result.tools)

                    logger.info(f"[STDIO] Success: {len(tools)} tools")
                    return MCPProxyService._create_success_response(
                        tools,
                        f"Fetched {len(tools)} tools via STDIO"
                    )

        except asyncio.TimeoutError:
            logger.error(f"[STDIO] Timeout after {MCPProxyService.DEFAULT_TIMEOUT}s")
            return MCPProxyService._create_error_response(
                f"STDIO timeout after {MCPProxyService.DEFAULT_TIMEOUT}s"
            )
        except Exception as e:
            logger.error(f"[STDIO] Failed: {type(e).__name__}: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"STDIO failed: {str(e)}")

    @staticmethod
    async def _fetch_sse(url: str) -> Dict[str, Any]:
        """
        SSE transport - Inspector의 SSEClientTransport와 동일
        """
        logger.info(f"[SSE] Connecting to: {url}")

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                return MCPProxyService._create_error_response(f"Invalid URL: {url}")

            logger.info(f"[SSE] Creating SSE client for {url}")

            # Inspector: new SSEClientTransport(new URL(url), {headers...})
            # Python: sse_client(url)
            async with sse_client(url) as (read, write):
                async with ClientSession(read, write) as session:
                    logger.info("[SSE] Session created, initializing...")

                    await asyncio.wait_for(
                        session.initialize(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    logger.info(f"[SSE] Session initialized")
                    logger.info("[SSE] Listing tools...")

                    result = await asyncio.wait_for(
                        session.list_tools(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    tools = MCPProxyService._convert_tools(result.tools)

                    logger.info(f"[SSE] Success: {len(tools)} tools")
                    return MCPProxyService._create_success_response(
                        tools,
                        f"Fetched {len(tools)} tools via SSE"
                    )

        except asyncio.TimeoutError:
            error_msg = f"SSE timeout after {MCPProxyService.DEFAULT_TIMEOUT}s"
            logger.error(f"[SSE] {error_msg}")
            return MCPProxyService._create_error_response(error_msg)
        except Exception as e:
            error_msg = f"SSE failed: {type(e).__name__}: {str(e)}"
            logger.error(f"[SSE] {error_msg}", exc_info=True)
            return MCPProxyService._create_error_response(error_msg)

    @staticmethod
    async def _fetch_streamable_http(url: str) -> Dict[str, Any]:
        """
        Streamable HTTP transport - Inspector의 StreamableHTTPClientTransport와 동일
        """
        logger.info(f"[Streamable HTTP] Connecting to: {url}")

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                return MCPProxyService._create_error_response(f"Invalid URL: {url}")

            if not HAS_STREAMABLE_HTTP:
                # Streamable HTTP가 없으면 SSE로 시도
                logger.warning("[Streamable HTTP] Not available, trying SSE")
                return await MCPProxyService._fetch_sse(url)

            logger.info(f"[Streamable HTTP] Creating client for {url}")

            # Inspector: new StreamableHTTPClientTransport(new URL(url), {fetch...})
            # Python: streamablehttp_client(url)
            async with streamablehttp_client(url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    logger.info("[Streamable HTTP] Session created, initializing...")

                    init_result = await asyncio.wait_for(
                        session.initialize(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    logger.info(f"[Streamable HTTP] Session initialized")
                    logger.info(f"[Streamable HTTP] Server info: {init_result}")
                    logger.info("[Streamable HTTP] Listing tools...")

                    result = await asyncio.wait_for(
                        session.list_tools(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    logger.info(f"[Streamable HTTP] Received tools response")

                    tools = MCPProxyService._convert_tools(result.tools)

                    logger.info(f"[Streamable HTTP] Success: {len(tools)} tools")
                    return MCPProxyService._create_success_response(
                        tools,
                        f"Fetched {len(tools)} tools via Streamable HTTP"
                    )

        except asyncio.TimeoutError:
            error_msg = f"Streamable HTTP timeout after {MCPProxyService.DEFAULT_TIMEOUT}s"
            logger.error(f"[Streamable HTTP] {error_msg}")

            # Fallback to manual methods
            logger.info("[Streamable HTTP] Trying manual fallback")
            return await MCPProxyService._fetch_http_manual(url)

        except Exception as e:
            error_msg = f"Streamable HTTP failed: {type(e).__name__}: {str(e)}"
            logger.error(f"[Streamable HTTP] {error_msg}", exc_info=True)

            # Fallback to manual methods
            logger.info("[Streamable HTTP] Trying manual fallback")
            return await MCPProxyService._fetch_http_manual(url)

    @staticmethod
    def _convert_tools(tools_list) -> List[Dict[str, Any]]:
        """Tool 객체를 딕셔너리로 변환"""
        tools = []
        for tool in tools_list:
            tool_dict = {
                "name": tool.name,
                "description": tool.description,
            }
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                tool_dict["inputSchema"] = tool.inputSchema
            tools.append(tool_dict)
        return tools

    @staticmethod
    async def _fetch_http_manual(url: str) -> Dict[str, Any]:
        """
        수동 HTTP fallback - SDK 실패 시
        """
        logger.info(f"[HTTP Manual] Starting with URL: {url}")

        json_rpc_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "params": {}
        }

        async with aiohttp.ClientSession() as session:
            # 1. POST 시도
            try:
                logger.info("[HTTP Manual] Trying POST")
                async with session.post(
                    url,
                    json=json_rpc_request,
                    headers={"Accept": "application/json, text/event-stream"},
                    timeout=aiohttp.ClientTimeout(total=MCPProxyService.HTTP_TIMEOUT)
                ) as resp:
                    logger.info(f"[HTTP Manual] POST Status: {resp.status}")

                    if resp.status == 200:
                        content_type = resp.headers.get("Content-Type", "")
                        if "application/json" in content_type:
                            data = await resp.json()
                            tools = data.get("result", {}).get("tools", [])
                            if tools:
                                logger.info(f"[HTTP Manual] POST success: {len(tools)} tools")
                                return MCPProxyService._create_success_response(
                                    tools,
                                    f"Fetched {len(tools)} tools via POST"
                                )
            except Exception as e:
                logger.warning(f"[HTTP Manual] POST failed: {e}")

            # 2. GET 시도
            get_paths = ["", "/tools", "/tools/list"]
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

                        tools = None
                        if isinstance(data, list) and data and isinstance(data[0], dict) and "name" in data[0]:
                            tools = data
                        elif isinstance(data, dict):
                            if "result" in data and "tools" in data["result"]:
                                tools = data["result"]["tools"]
                            elif "tools" in data:
                                tools = data["tools"]

                        if tools:
                            logger.info(f"[HTTP Manual] GET success: {len(tools)} tools")
                            return MCPProxyService._create_success_response(
                                tools,
                                f"Fetched {len(tools)} tools via GET"
                            )
                except Exception as e:
                    logger.debug(f"[HTTP Manual] GET {path} failed: {e}")
                    continue

            logger.error("[HTTP Manual] All attempts failed")
            return MCPProxyService._create_error_response(
                "Could not fetch tools: all methods failed"
            )
