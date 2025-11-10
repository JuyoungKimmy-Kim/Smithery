"""
MCP 프록시 서비스
Inspector의 구현을 최대한 그대로 따라서 구현
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional

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

    # 타임아웃 설정 - Inspector처럼 충분한 시간 확보
    DEFAULT_TIMEOUT = 120

    @staticmethod
    def _create_success_response(data: List[Dict[str, Any]], message: str = "Success", data_key: str = "tools") -> Dict[str, Any]:
        """성공 응답 생성 - tools, prompts, resources 모두 지원"""
        return {
            "success": True,
            data_key: data,
            "message": message
        }

    @staticmethod
    def _create_error_response(message: str, data_key: str = "tools") -> Dict[str, Any]:
        """에러 응답 생성 - tools, prompts, resources 모두 지원"""
        return {
            "success": False,
            data_key: [],
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

        # Inspector의 정확한 매핑
        if protocol in ("stdio",):
            return "stdio"
        elif protocol in ("sse", "server-sent-events"):
            return "sse"
        elif protocol in ("streamable-http", "http", "https", "http-stream", "websocket"):
            return "streamable-http"
        else:
            # 기본값
            return "streamable-http"

    @staticmethod
    async def _fetch_stdio(command: str) -> Dict[str, Any]:
        """
        STDIO transport - Inspector의 StdioClientTransport와 동일
        Improved error handling and resource cleanup
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
        except asyncio.CancelledError:
            logger.warning("[STDIO] Request was cancelled by client")
            raise  # Re-raise to propagate cancellation properly
        except Exception as e:
            logger.error(f"[STDIO] Failed: {type(e).__name__}: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"STDIO failed: {str(e)}")
        finally:
            logger.debug("[STDIO] Resource cleanup completed")

    @staticmethod
    async def _fetch_sse(url: str) -> Dict[str, Any]:
        """
        SSE transport - Inspector의 SSEClientTransport와 동일
        Improved error handling and resource cleanup
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
        except asyncio.CancelledError:
            logger.warning("[SSE] Request was cancelled by client")
            raise  # Re-raise to propagate cancellation properly
        except Exception as e:
            error_msg = f"SSE failed: {type(e).__name__}: {str(e)}"
            logger.error(f"[SSE] {error_msg}", exc_info=True)
            return MCPProxyService._create_error_response(error_msg)
        finally:
            logger.debug("[SSE] Resource cleanup completed")

    @staticmethod
    async def _fetch_streamable_http(url: str) -> Dict[str, Any]:
        """
        Streamable HTTP transport - Inspector의 StreamableHTTPClientTransport와 동일
        Improved error handling and resource cleanup
        """
        logger.info(f"[Streamable HTTP] Connecting to: {url}")
        logger.info(f"[Streamable HTTP] HAS_STREAMABLE_HTTP = {HAS_STREAMABLE_HTTP}")

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                return MCPProxyService._create_error_response(f"Invalid URL: {url}")

            if not HAS_STREAMABLE_HTTP:
                # Streamable HTTP가 없으면 SSE로 시도
                logger.warning("[Streamable HTTP] Not available, trying SSE")
                return await MCPProxyService._fetch_sse(url)

            logger.info(f"[Streamable HTTP] Creating client for {url}")
            logger.info(f"[Streamable HTTP] streamablehttp_client function: {streamablehttp_client}")

            # Inspector: new StreamableHTTPClientTransport(new URL(url), {fetch...})
            # Python: streamablehttp_client(url)
            logger.info(f"[Streamable HTTP] About to call streamablehttp_client({url})")
            async with streamablehttp_client(url) as transport_tuple:
                logger.info(f"[Streamable HTTP] streamablehttp_client returned, unpacking...")
                logger.info(f"[Streamable HTTP] transport_tuple type: {type(transport_tuple)}")
                read, write, _ = transport_tuple
                logger.info(f"[Streamable HTTP] Successfully unpacked: read={type(read)}, write={type(write)}")

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
            return MCPProxyService._create_error_response(error_msg)
        except asyncio.CancelledError:
            logger.warning("[Streamable HTTP] Request was cancelled by client")
            raise  # Re-raise to propagate cancellation properly
        except Exception as e:
            error_msg = f"Streamable HTTP failed: {type(e).__name__}: {str(e)}"
            logger.error(f"[Streamable HTTP] {error_msg}", exc_info=True)
            return MCPProxyService._create_error_response(error_msg)
        finally:
            logger.debug("[Streamable HTTP] Resource cleanup completed")

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
    def _convert_prompts(prompts_list) -> List[Dict[str, Any]]:
        """Prompt 객체를 딕셔너리로 변환"""
        prompts = []
        for prompt in prompts_list:
            prompt_dict = {
                "name": prompt.name,
                "description": getattr(prompt, 'description', None),
            }
            if hasattr(prompt, 'arguments') and prompt.arguments:
                prompt_dict["arguments"] = prompt.arguments
            prompts.append(prompt_dict)
        return prompts

    @staticmethod
    def _convert_resources(resources_list) -> List[Dict[str, Any]]:
        """Resource 객체를 딕셔너리로 변환"""
        resources = []
        for resource in resources_list:
            resource_dict = {
                "uri": resource.uri,
                "name": resource.name,
                "description": getattr(resource, 'description', None),
            }
            if hasattr(resource, 'mimeType') and resource.mimeType:
                resource_dict["mimeType"] = resource.mimeType
            resources.append(resource_dict)
        return resources

    @staticmethod
    def _convert_resource_templates(templates_list) -> List[Dict[str, Any]]:
        """Resource Template 객체를 딕셔너리로 변환"""
        templates = []
        for template in templates_list:
            template_dict = {
                "uriTemplate": template.uriTemplate,
                "name": template.name,
                "description": getattr(template, 'description', None),
            }
            if hasattr(template, 'mimeType') and template.mimeType:
                template_dict["mimeType"] = template.mimeType
            templates.append(template_dict)
        return templates

    # ==================== PROMPTS METHODS ====================

    @staticmethod
    async def fetch_prompts(url: str, protocol: str) -> Dict[str, Any]:
        """
        MCP 서버에서 prompts 목록을 가져옵니다
        Inspector의 listPrompts()와 동일한 패턴

        Args:
            url: MCP 서버 URL 또는 명령어
            protocol: 프로토콜 타입 (stdio, sse, streamable-http)

        Returns:
            Dict containing prompts list and status
        """
        logger.info(f"[MCP Proxy] Fetching prompts - URL: {url}, Protocol: {protocol}")

        if not MCP_SDK_AVAILABLE:
            logger.error("MCP SDK is not installed")
            return MCPProxyService._create_error_response(
                "MCP SDK is not installed. Please install with: pip install mcp[cli]",
                data_key="prompts"
            )

        try:
            normalized_protocol = MCPProxyService._normalize_protocol(protocol)

            if normalized_protocol == "stdio":
                return await MCPProxyService._fetch_prompts_stdio(url)
            elif normalized_protocol == "sse":
                return await MCPProxyService._fetch_prompts_sse(url)
            else:
                return await MCPProxyService._fetch_prompts_streamable_http(url)

        except Exception as e:
            logger.error(f"[MCP Proxy] Failed to fetch prompts: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"Failed to fetch prompts: {str(e)}", data_key="prompts")

    @staticmethod
    async def _fetch_prompts_stdio(command: str) -> Dict[str, Any]:
        """STDIO를 통해 prompts 가져오기"""
        logger.info(f"[STDIO] Fetching prompts with command: {command}")

        try:
            parts = command.split()
            if not parts:
                return MCPProxyService._create_error_response("Empty command", data_key="prompts")

            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            server_params = StdioServerParameters(command=cmd, args=args, env=None)

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=MCPProxyService.DEFAULT_TIMEOUT)

                    result = await asyncio.wait_for(
                        session.list_prompts(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    prompts = MCPProxyService._convert_prompts(result.prompts)
                    logger.info(f"[STDIO] Success: {len(prompts)} prompts")

                    return MCPProxyService._create_success_response(
                        prompts,
                        f"Fetched {len(prompts)} prompts via STDIO",
                        data_key="prompts"
                    )

        except asyncio.TimeoutError:
            return MCPProxyService._create_error_response(
                f"STDIO timeout after {MCPProxyService.DEFAULT_TIMEOUT}s",
                data_key="prompts"
            )
        except Exception as e:
            logger.error(f"[STDIO] Failed: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"STDIO failed: {str(e)}", data_key="prompts")

    @staticmethod
    async def _fetch_prompts_sse(url: str) -> Dict[str, Any]:
        """SSE를 통해 prompts 가져오기"""
        logger.info(f"[SSE] Fetching prompts from: {url}")

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                return MCPProxyService._create_error_response(f"Invalid URL: {url}", data_key="prompts")

            async with sse_client(url) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=MCPProxyService.DEFAULT_TIMEOUT)

                    result = await asyncio.wait_for(
                        session.list_prompts(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    prompts = MCPProxyService._convert_prompts(result.prompts)
                    logger.info(f"[SSE] Success: {len(prompts)} prompts")

                    return MCPProxyService._create_success_response(
                        prompts,
                        f"Fetched {len(prompts)} prompts via SSE",
                        data_key="prompts"
                    )

        except asyncio.TimeoutError:
            return MCPProxyService._create_error_response(
                f"SSE timeout after {MCPProxyService.DEFAULT_TIMEOUT}s",
                data_key="prompts"
            )
        except Exception as e:
            logger.error(f"[SSE] Failed: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"SSE failed: {str(e)}", data_key="prompts")

    @staticmethod
    async def _fetch_prompts_streamable_http(url: str) -> Dict[str, Any]:
        """Streamable HTTP를 통해 prompts 가져오기"""
        logger.info(f"[Streamable HTTP] Fetching prompts from: {url}")

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                return MCPProxyService._create_error_response(f"Invalid URL: {url}", data_key="prompts")

            if not HAS_STREAMABLE_HTTP:
                logger.warning("[Streamable HTTP] Not available, trying SSE")
                return await MCPProxyService._fetch_prompts_sse(url)

            async with streamablehttp_client(url) as transport_tuple:
                read, write, _ = transport_tuple

                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=MCPProxyService.DEFAULT_TIMEOUT)

                    result = await asyncio.wait_for(
                        session.list_prompts(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    prompts = MCPProxyService._convert_prompts(result.prompts)
                    logger.info(f"[Streamable HTTP] Success: {len(prompts)} prompts")

                    return MCPProxyService._create_success_response(
                        prompts,
                        f"Fetched {len(prompts)} prompts via Streamable HTTP",
                        data_key="prompts"
                    )

        except asyncio.TimeoutError:
            return MCPProxyService._create_error_response(
                f"Streamable HTTP timeout after {MCPProxyService.DEFAULT_TIMEOUT}s",
                data_key="prompts"
            )
        except Exception as e:
            logger.error(f"[Streamable HTTP] Failed: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"Streamable HTTP failed: {str(e)}", data_key="prompts")

    # ==================== RESOURCES METHODS ====================

    @staticmethod
    async def fetch_resources(url: str, protocol: str) -> Dict[str, Any]:
        """
        MCP 서버에서 resources 목록을 가져옵니다
        Inspector의 listResources()와 동일한 패턴

        Args:
            url: MCP 서버 URL 또는 명령어
            protocol: 프로토콜 타입 (stdio, sse, streamable-http)

        Returns:
            Dict containing resources list and status
        """
        logger.info(f"[MCP Proxy] Fetching resources - URL: {url}, Protocol: {protocol}")

        if not MCP_SDK_AVAILABLE:
            logger.error("MCP SDK is not installed")
            return MCPProxyService._create_error_response(
                "MCP SDK is not installed. Please install with: pip install mcp[cli]",
                data_key="resources"
            )

        try:
            normalized_protocol = MCPProxyService._normalize_protocol(protocol)

            if normalized_protocol == "stdio":
                return await MCPProxyService._fetch_resources_stdio(url)
            elif normalized_protocol == "sse":
                return await MCPProxyService._fetch_resources_sse(url)
            else:
                return await MCPProxyService._fetch_resources_streamable_http(url)

        except Exception as e:
            logger.error(f"[MCP Proxy] Failed to fetch resources: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"Failed to fetch resources: {str(e)}", data_key="resources")

    @staticmethod
    async def _fetch_resources_stdio(command: str) -> Dict[str, Any]:
        """STDIO를 통해 resources 가져오기"""
        logger.info(f"[STDIO] Fetching resources with command: {command}")

        try:
            parts = command.split()
            if not parts:
                return MCPProxyService._create_error_response("Empty command", data_key="resources")

            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            server_params = StdioServerParameters(command=cmd, args=args, env=None)

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=MCPProxyService.DEFAULT_TIMEOUT)

                    result = await asyncio.wait_for(
                        session.list_resources(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    resources = MCPProxyService._convert_resources(result.resources)
                    logger.info(f"[STDIO] Success: {len(resources)} resources")

                    return MCPProxyService._create_success_response(
                        resources,
                        f"Fetched {len(resources)} resources via STDIO",
                        data_key="resources"
                    )

        except asyncio.TimeoutError:
            return MCPProxyService._create_error_response(
                f"STDIO timeout after {MCPProxyService.DEFAULT_TIMEOUT}s",
                data_key="resources"
            )
        except Exception as e:
            logger.error(f"[STDIO] Failed: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"STDIO failed: {str(e)}", data_key="resources")

    @staticmethod
    async def _fetch_resources_sse(url: str) -> Dict[str, Any]:
        """SSE를 통해 resources 가져오기"""
        logger.info(f"[SSE] Fetching resources from: {url}")

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                return MCPProxyService._create_error_response(f"Invalid URL: {url}", data_key="resources")

            async with sse_client(url) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=MCPProxyService.DEFAULT_TIMEOUT)

                    result = await asyncio.wait_for(
                        session.list_resources(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    resources = MCPProxyService._convert_resources(result.resources)
                    logger.info(f"[SSE] Success: {len(resources)} resources")

                    return MCPProxyService._create_success_response(
                        resources,
                        f"Fetched {len(resources)} resources via SSE",
                        data_key="resources"
                    )

        except asyncio.TimeoutError:
            return MCPProxyService._create_error_response(
                f"SSE timeout after {MCPProxyService.DEFAULT_TIMEOUT}s",
                data_key="resources"
            )
        except Exception as e:
            logger.error(f"[SSE] Failed: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"SSE failed: {str(e)}", data_key="resources")

    @staticmethod
    async def _fetch_resources_streamable_http(url: str) -> Dict[str, Any]:
        """Streamable HTTP를 통해 resources 가져오기"""
        logger.info(f"[Streamable HTTP] Fetching resources from: {url}")

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                return MCPProxyService._create_error_response(f"Invalid URL: {url}", data_key="resources")

            if not HAS_STREAMABLE_HTTP:
                logger.warning("[Streamable HTTP] Not available, trying SSE")
                return await MCPProxyService._fetch_resources_sse(url)

            async with streamablehttp_client(url) as transport_tuple:
                read, write, _ = transport_tuple

                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=MCPProxyService.DEFAULT_TIMEOUT)

                    result = await asyncio.wait_for(
                        session.list_resources(),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    resources = MCPProxyService._convert_resources(result.resources)
                    logger.info(f"[Streamable HTTP] Success: {len(resources)} resources")

                    return MCPProxyService._create_success_response(
                        resources,
                        f"Fetched {len(resources)} resources via Streamable HTTP",
                        data_key="resources"
                    )

        except asyncio.TimeoutError:
            return MCPProxyService._create_error_response(
                f"Streamable HTTP timeout after {MCPProxyService.DEFAULT_TIMEOUT}s",
                data_key="resources"
            )
        except Exception as e:
            logger.error(f"[Streamable HTTP] Failed: {str(e)}", exc_info=True)
            return MCPProxyService._create_error_response(f"Streamable HTTP failed: {str(e)}", data_key="resources")

    # ==================== TOOL CALLING METHODS ====================

    @staticmethod
    async def call_tool(url: str, protocol: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a specific tool on the MCP server

        Args:
            url: MCP 서버 URL 또는 명령어
            protocol: 프로토콜 타입 (stdio, sse, streamable-http)
            tool_name: Tool name to call
            arguments: Tool arguments

        Returns:
            Dict containing tool execution result
        """
        logger.info(f"[MCP Proxy] Calling tool {tool_name} - URL: {url}, Protocol: {protocol}")

        if not MCP_SDK_AVAILABLE:
            logger.error("MCP SDK is not installed")
            return {
                "success": False,
                "error": "MCP SDK is not installed"
            }

        try:
            normalized_protocol = MCPProxyService._normalize_protocol(protocol)

            if normalized_protocol == "stdio":
                return await MCPProxyService._call_tool_stdio(url, tool_name, arguments)
            elif normalized_protocol == "sse":
                return await MCPProxyService._call_tool_sse(url, tool_name, arguments)
            else:
                return await MCPProxyService._call_tool_streamable_http(url, tool_name, arguments)

        except Exception as e:
            logger.error(f"[MCP Proxy] Failed to call tool: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    async def _call_tool_stdio(command: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """STDIO를 통해 tool 호출 - Improved error handling"""
        logger.info(f"[STDIO] Calling tool {tool_name} with command: {command}")

        try:
            parts = command.split()
            if not parts:
                return {"success": False, "error": "Empty command"}

            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            server_params = StdioServerParameters(command=cmd, args=args, env=None)

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=MCPProxyService.DEFAULT_TIMEOUT)

                    result = await asyncio.wait_for(
                        session.call_tool(tool_name, arguments),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    logger.info(f"[STDIO] Tool {tool_name} executed successfully")
                    return {
                        "success": True,
                        "result": result.content if hasattr(result, 'content') else result
                    }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"STDIO timeout after {MCPProxyService.DEFAULT_TIMEOUT}s"
            }
        except asyncio.CancelledError:
            logger.warning(f"[STDIO] Tool call {tool_name} was cancelled by client")
            raise
        except Exception as e:
            logger.error(f"[STDIO] Failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            logger.debug(f"[STDIO] Tool {tool_name} cleanup completed")

    @staticmethod
    async def _call_tool_sse(url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """SSE를 통해 tool 호출 - Improved error handling"""
        logger.info(f"[SSE] Calling tool {tool_name} from: {url}")

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                return {"success": False, "error": f"Invalid URL: {url}"}

            async with sse_client(url) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=MCPProxyService.DEFAULT_TIMEOUT)

                    result = await asyncio.wait_for(
                        session.call_tool(tool_name, arguments),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    logger.info(f"[SSE] Tool {tool_name} executed successfully")
                    return {
                        "success": True,
                        "result": result.content if hasattr(result, 'content') else result
                    }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"SSE timeout after {MCPProxyService.DEFAULT_TIMEOUT}s"
            }
        except asyncio.CancelledError:
            logger.warning(f"[SSE] Tool call {tool_name} was cancelled by client")
            raise
        except Exception as e:
            logger.error(f"[SSE] Failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            logger.debug(f"[SSE] Tool {tool_name} cleanup completed")

    @staticmethod
    async def _call_tool_streamable_http(url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Streamable HTTP를 통해 tool 호출 - Improved error handling"""
        logger.info(f"[Streamable HTTP] Calling tool {tool_name} from: {url}")

        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                return {"success": False, "error": f"Invalid URL: {url}"}

            if not HAS_STREAMABLE_HTTP:
                logger.warning("[Streamable HTTP] Not available, trying SSE")
                return await MCPProxyService._call_tool_sse(url, tool_name, arguments)

            async with streamablehttp_client(url) as transport_tuple:
                read, write, _ = transport_tuple

                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=MCPProxyService.DEFAULT_TIMEOUT)

                    result = await asyncio.wait_for(
                        session.call_tool(tool_name, arguments),
                        timeout=MCPProxyService.DEFAULT_TIMEOUT
                    )

                    logger.info(f"[Streamable HTTP] Tool {tool_name} executed successfully")
                    return {
                        "success": True,
                        "result": result.content if hasattr(result, 'content') else result
                    }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Streamable HTTP timeout after {MCPProxyService.DEFAULT_TIMEOUT}s"
            }
        except asyncio.CancelledError:
            logger.warning(f"[Streamable HTTP] Tool call {tool_name} was cancelled by client")
            raise
        except Exception as e:
            logger.error(f"[Streamable HTTP] Failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            logger.debug(f"[Streamable HTTP] Tool {tool_name} cleanup completed")
