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

    DEFAULT_TIMEOUT = 30  # 30 seconds timeout

    async def check_server_health(self, server_url: str, transport_type: str) -> Dict[str, Any]:
        """
        Check MCP server health by attempting to connect and initialize.

        Args:
            server_url: The MCP server URL
            transport_type: "sse" or "http"

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

        # Only SSE and HTTP are supported for remote health checks
        if transport_type in ("sse", "http-stream", "streamable-http", "http"):
            return await self._check_sse_server(server_url)
        else:
            return {
                "healthy": False,
                "error": f"Unsupported transport type for health check: {transport_type}"
            }

    async def _check_sse_server(self, url: str) -> Dict[str, Any]:
        """
        Check SSE/HTTP MCP server health.
        Based on Inspector's connect() method.
        """
        logger.info(f"[Health Check] Checking SSE server: {url}")

        try:
            # Create SSE client connection (like Inspector's SSEClientTransport)
            async with sse_client(url) as (read, write):
                # Create MCP client session (like Inspector's Client.connect())
                async with ClientSession(read, write) as session:
                    logger.info("[Health Check] Initializing session...")

                    # Initialize session with timeout
                    await asyncio.wait_for(
                        session.initialize(),
                        timeout=self.DEFAULT_TIMEOUT
                    )

                    logger.info("[Health Check] Session initialized successfully")

                    # Get server capabilities (like Inspector's getServerCapabilities())
                    capabilities = session.get_server_capabilities()

                    # Server is healthy if we got here
                    return {
                        "healthy": True,
                        "capabilities": str(capabilities) if capabilities else None
                    }

        except asyncio.TimeoutError:
            error_msg = f"Timeout after {self.DEFAULT_TIMEOUT}s"
            logger.error(f"[Health Check] {error_msg}")
            return {
                "healthy": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"[Health Check] Failed: {error_msg}")
            return {
                "healthy": False,
                "error": error_msg
            }
