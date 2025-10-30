"""
MCP Health Checker using official MCP SDK
Inspired by Inspector's useConnection.ts connect() method
"""

import asyncio
import logging
from typing import Dict, Any

try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamablehttp_client
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPHealthChecker:
    """
    Health checker for MCP servers using official MCP SDK.
    Supports SSE and HTTP transports (STDIO not applicable for remote health checks).
    """

    # Timeout settings matching MCPProxyService (which works for tools preview)
    CONNECTION_TIMEOUT = 120  # Connection timeout - same as MCPProxyService.DEFAULT_TIMEOUT
    INITIALIZE_TIMEOUT = 120  # Session initialization timeout

    async def check_server_health(self, server_url: str, transport_type: str) -> Dict[str, Any]:
        """
        Check MCP server health by attempting to connect and initialize.

        Args:
            server_url: The MCP server URL
            transport_type: "sse", "http", "http-stream", "streamable-http"

        Returns:
            Dict with 'healthy' (bool) and optional 'error' (str)
        """
        if not MCP_SDK_AVAILABLE:
            return {
                "healthy": False,
                "error": "MCP SDK not available. Install with: pip install mcp"
            }

        if not server_url:
            return {
                "healthy": False,
                "error": "No server URL provided"
            }

        transport_type = transport_type.lower()
        logger.info(f"[Health Check] Transport type: {transport_type}, Server URL: {server_url}")

        # Map transport types to appropriate check method (matching Inspector's logic)
        if transport_type == "sse":
            # SSE transport
            logger.info(f"[Health Check] Using SSEClientTransport")
            return await self._check_sse_server(server_url)
        elif transport_type in ("http-stream", "streamable-http", "http"):
            # Streamable HTTP transport (like Inspector's StreamableHTTPClientTransport)
            logger.info(f"[Health Check] Using StreamableHTTPClientTransport")
            return await self._check_streamable_http_server(server_url)
        else:
            return {
                "healthy": False,
                "error": f"Unsupported transport type for health check: {transport_type}"
            }

    async def _check_sse_server(self, url: str) -> Dict[str, Any]:
        """
        Check SSE MCP server health using SSEClientTransport.
        Based on Inspector's connect() method for SSE.
        """
        logger.info(f"[Health Check] Checking SSE server: {url}")

        try:
            # Create SSE client connection (like Inspector's SSEClientTransport)
            logger.info(f"[Health Check] Creating SSE client connection to {url}")
            async with sse_client(url, timeout=self.CONNECTION_TIMEOUT) as (read, write):
                logger.info("[Health Check] SSE client connected, creating session...")

                # Create MCP client session (like Inspector's Client.connect())
                async with ClientSession(read, write) as session:
                    logger.info("[Health Check] Session created, initializing...")

                    # Initialize session with timeout
                    init_result = await asyncio.wait_for(
                        session.initialize(),
                        timeout=self.INITIALIZE_TIMEOUT
                    )

                    logger.info(f"[Health Check] Session initialized successfully")
                    logger.info(f"[Health Check] Server info: {init_result.serverInfo}")
                    logger.info(f"[Health Check] Capabilities: {init_result.capabilities}")

                    # Server is healthy if we can initialize (matching Inspector's connect logic)
                    # Inspector doesn't list tools for health check, just connects and gets capabilities
                    return {
                        "healthy": True,
                        "server_info": str(init_result.serverInfo) if init_result.serverInfo else None,
                        "capabilities": str(init_result.capabilities) if init_result.capabilities else None,
                        "protocol_version": init_result.protocolVersion
                    }

        except asyncio.TimeoutError:
            error_msg = f"Timeout after {self.INITIALIZE_TIMEOUT}s - server did not respond"
            logger.error(f"[Health Check] {error_msg}")
            return {
                "healthy": False,
                "error": error_msg
            }
        except ConnectionError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error(f"[Health Check] {error_msg}")
            return {
                "healthy": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"[Health Check] Failed with exception: {error_msg}", exc_info=True)
            return {
                "healthy": False,
                "error": error_msg
            }

    async def _check_streamable_http_server(self, url: str) -> Dict[str, Any]:
        """
        Check Streamable HTTP MCP server health using StreamableHTTPClientTransport.
        Based on Inspector's connect() method for streamable-http.
        """
        logger.info(f"[Health Check] Checking Streamable HTTP server: {url}")

        try:
            # Create Streamable HTTP client connection (like Inspector's StreamableHTTPClientTransport)
            logger.info(f"[Health Check] Creating Streamable HTTP client connection to {url}")
            # streamablehttp_client returns (read, write, get_session_id)
            async with streamablehttp_client(url, timeout=self.CONNECTION_TIMEOUT) as (read, write, _get_session_id):
                logger.info("[Health Check] Streamable HTTP client connected, creating session...")

                # Create MCP client session
                async with ClientSession(read, write) as session:
                    logger.info("[Health Check] Session created, initializing...")

                    # Initialize session with timeout
                    init_result = await asyncio.wait_for(
                        session.initialize(),
                        timeout=self.INITIALIZE_TIMEOUT
                    )

                    logger.info(f"[Health Check] Session initialized successfully")
                    logger.info(f"[Health Check] Server info: {init_result.serverInfo}")
                    logger.info(f"[Health Check] Capabilities: {init_result.capabilities}")

                    # Server is healthy if we can initialize (matching Inspector's connect logic)
                    # Inspector doesn't list tools for health check, just connects and gets capabilities
                    return {
                        "healthy": True,
                        "server_info": str(init_result.serverInfo) if init_result.serverInfo else None,
                        "capabilities": str(init_result.capabilities) if init_result.capabilities else None,
                        "protocol_version": init_result.protocolVersion
                    }

        except asyncio.TimeoutError:
            error_msg = f"Timeout after {self.INITIALIZE_TIMEOUT}s - server did not respond"
            logger.error(f"[Health Check] {error_msg}")
            return {
                "healthy": False,
                "error": error_msg
            }
        except ConnectionError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error(f"[Health Check] {error_msg}")
            return {
                "healthy": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"[Health Check] Failed with exception: {error_msg}", exc_info=True)
            return {
                "healthy": False,
                "error": error_msg
            }
