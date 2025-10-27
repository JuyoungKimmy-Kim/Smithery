"""
MCP 프록시 서비스
Frontend에서 MCP 서버의 tools를 미리보기할 때 사용하는 프록시 서비스
Python MCP SDK를 사용하여 Inspector 패턴을 따름
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
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
    Python MCP SDK를 사용하여 표준화된 방식으로 통신
    """

    # 타임아웃 설정
    DEFAULT_TIMEOUT = 30

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
        if not MCP_SDK_AVAILABLE:
            logger.error("MCP SDK is not installed. Please install with: pip install mcp[cli]")
            return MCPProxyService._create_error_response(
                "MCP SDK is not installed. Please contact administrator."
            )

        logger.info(f"[MCP Proxy] Fetching tools - URL: {url}, Protocol: {protocol}")

        try:
            # 프로토콜 정규화
            normalized_protocol = MCPProxyService._normalize_protocol(protocol)

            if normalized_protocol == "stdio":
                return await MCPProxyService._fetch_stdio(url)
            elif normalized_protocol in ("http", "streamable-http"):
                return await MCPProxyService._fetch_http(url)
            else:
                logger.warning(f"[MCP Proxy] Unsupported protocol: {protocol}, trying HTTP fallback")
                # 알 수 없는 프로토콜은 HTTP로 시도
                return await MCPProxyService._fetch_http(url)

        except Exception as e:
            logger.error(f"[MCP Proxy] Failed to fetch tools: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"Failed to fetch tools: {str(e)}")

    @staticmethod
    def _normalize_protocol(protocol: str) -> str:
        """프로토콜 이름 정규화"""
        protocol = protocol.lower().strip()

        # HTTP 관련 프로토콜들은 모두 streamable-http로 통합
        if protocol in ("http", "http-stream", "sse", "streamable-http", "websocket"):
            return "streamable-http"

        return protocol

    @staticmethod
    async def _fetch_stdio(command: str) -> Dict[str, Any]:
        """
        STDIO transport를 사용하여 로컬 MCP 서버에서 tools 가져오기

        Args:
            command: 실행할 명령어 (예: "node server.js" 또는 "python server.py")
        """
        logger.info(f"[STDIO] Starting STDIO transport with command: {command}")

        try:
            # 명령어를 파싱 (첫 번째가 command, 나머지가 args)
            parts = command.split()
            if not parts:
                return MCPProxyService._create_error_response("Empty command")

            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            # StdioServerParameters 생성
            server_params = StdioServerParameters(
                command=cmd,
                args=args,
                env=None  # 필요시 환경 변수 추가 가능
            )

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

                    # result.tools는 Tool 객체들의 리스트
                    tools = []
                    for tool in result.tools:
                        tool_dict = {
                            "name": tool.name,
                            "description": tool.description,
                        }
                        # inputSchema가 있으면 추가
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
    async def _fetch_http(url: str) -> Dict[str, Any]:
        """
        Streamable HTTP transport를 사용하여 HTTP 기반 MCP 서버에서 tools 가져오기

        Args:
            url: MCP 서버 URL (예: "http://localhost:8000/mcp")
        """
        logger.info(f"[HTTP] Starting Streamable HTTP transport with URL: {url}")

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

                    logger.info("[HTTP] Session initialized, listing tools")

                    # tools 목록 가져오기
                    result = await asyncio.wait_for(
                        session.list_tools(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    # result.tools는 Tool 객체들의 리스트
                    tools = []
                    for tool in result.tools:
                        tool_dict = {
                            "name": tool.name,
                            "description": tool.description,
                        }
                        # inputSchema가 있으면 추가
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            tool_dict["inputSchema"] = tool.inputSchema
                        tools.append(tool_dict)

                    logger.info(f"[HTTP] Successfully fetched {len(tools)} tools")
                    return MCPProxyService._create_success_response(
                        tools,
                        f"Successfully fetched {len(tools)} tools via HTTP"
                    )

        except asyncio.TimeoutError:
            logger.error(f"[HTTP] Timeout after {MCPProxyService.DEFAULT_TIMEOUT}s")
            return MCPProxyService._create_error_response(
                f"HTTP connection timeout after {MCPProxyService.DEFAULT_TIMEOUT}s"
            )
        except Exception as e:
            logger.error(f"[HTTP] Failed: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"HTTP failed: {str(e)}")
