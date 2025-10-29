"""
MCP Health Checker using official MCP SDK
Inspired by MCP Inspector's connection pattern
"""
import asyncio
from typing import Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import httpx


class MCPHealthChecker:
    """Health checker for MCP servers using official MCP SDK"""

    CLIENT_INFO = {
        "name": "smithery-health-checker",
        "version": "1.0.0"
    }

    TIMEOUT = 10  # seconds

    async def check_stdio_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of STDIO-based MCP server"""
        try:
            command = config.get("command")
            args = config.get("args", [])
            env = config.get("env", {})

            if not command:
                return {
                    "healthy": False,
                    "error": "No command specified for STDIO server"
                }

            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args if isinstance(args, list) else args.split(),
                env=env
            )

            # Connect using MCP SDK
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize connection
                    await asyncio.wait_for(
                        session.initialize(),
                        timeout=self.TIMEOUT
                    )

                    # Check if tools capability exists
                    capabilities = session.get_server_capabilities()

                    # Try to list tools if supported
                    if capabilities and hasattr(capabilities, 'tools'):
                        tools = await asyncio.wait_for(
                            session.list_tools(),
                            timeout=self.TIMEOUT
                        )
                        return {
                            "healthy": True,
                            "capabilities": str(capabilities),
                            "tools_count": len(tools.tools) if hasattr(tools, 'tools') else 0
                        }
                    else:
                        # Server connected but doesn't support tools
                        return {
                            "healthy": True,
                            "capabilities": str(capabilities),
                            "note": "Server does not expose tools capability"
                        }

        except asyncio.TimeoutError:
            return {
                "healthy": False,
                "error": "Connection timeout"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": f"STDIO connection failed: {str(e)}"
            }

    async def check_sse_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of SSE-based MCP server"""
        try:
            url = config.get("url")
            headers = config.get("headers", {})

            if not url:
                return {
                    "healthy": False,
                    "error": "No URL specified for SSE server"
                }

            # Connect using MCP SDK SSE client
            async with httpx.AsyncClient() as http_client:
                async with sse_client(url, headers=headers) as (read, write):
                    async with ClientSession(read, write) as session:
                        # Initialize connection
                        await asyncio.wait_for(
                            session.initialize(),
                            timeout=self.TIMEOUT
                        )

                        # Check capabilities
                        capabilities = session.get_server_capabilities()

                        # Try to list tools if supported
                        if capabilities and hasattr(capabilities, 'tools'):
                            tools = await asyncio.wait_for(
                                session.list_tools(),
                                timeout=self.TIMEOUT
                            )
                            return {
                                "healthy": True,
                                "capabilities": str(capabilities),
                                "tools_count": len(tools.tools) if hasattr(tools, 'tools') else 0
                            }
                        else:
                            return {
                                "healthy": True,
                                "capabilities": str(capabilities),
                                "note": "Server does not expose tools capability"
                            }

        except asyncio.TimeoutError:
            return {
                "healthy": False,
                "error": "Connection timeout"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": f"SSE connection failed: {str(e)}"
            }

    async def check_http_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of HTTP-based MCP server"""
        try:
            url = config.get("url")
            headers = config.get("headers", {})

            if not url:
                return {
                    "healthy": False,
                    "error": "No URL specified for HTTP server"
                }

            # Simple HTTP health check - try to call tools/list via JSON-RPC
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(
                    url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list",
                        "params": {}
                    },
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        return {
                            "healthy": True,
                            "tools_count": len(data.get("result", {}).get("tools", []))
                        }
                    else:
                        return {
                            "healthy": False,
                            "error": f"Invalid JSON-RPC response: {data}"
                        }
                else:
                    return {
                        "healthy": False,
                        "error": f"HTTP error {response.status_code}"
                    }

        except asyncio.TimeoutError:
            return {
                "healthy": False,
                "error": "Connection timeout"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": f"HTTP connection failed: {str(e)}"
            }

    async def check_server_health(
        self,
        transport_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check health of MCP server based on transport type

        Args:
            transport_type: Type of transport (stdio, sse, http)
            config: Server configuration

        Returns:
            Dict with health status and details
        """
        transport_type = transport_type.lower()

        if transport_type == "stdio":
            result = await self.check_stdio_server(config)
        elif transport_type in ("sse", "http-stream"):
            result = await self.check_sse_server(config)
        elif transport_type == "http":
            result = await self.check_http_server(config)
        else:
            result = {
                "healthy": False,
                "error": f"Unsupported transport type: {transport_type}"
            }

        return result
