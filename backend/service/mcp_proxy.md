```python
import aiohttp
import asyncio
import websockets
import json
import sys
from typing import Dict, Any, Optional


class MCPProxyService:
    """
    범용 MCP 클라이언트 서비스.
    Transport Type과 Server URL만으로 tools 목록을 자동으로 가져옴.
    HTTP, HTTP-stream, WebSocket, stdio 모두 지원하며, HTTP 계열은 fallback 내장.
    """

    # ----------------------------------------------------------------------
    @staticmethod
    async def fetch_tools(url: str, protocol: str) -> Dict[str, Any]:
        """Fetches tool list from MCP server using given transport type."""
        json_rpc_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "params": {}
        }

        try:
            if protocol == "http":
                return await MCPProxyService._fetch_http_with_fallback(url, json_rpc_request)
            elif protocol == "http-stream":
                return await MCPProxyService._fetch_http_stream(url, json_rpc_request)
            elif protocol == "websocket":
                return await MCPProxyService._fetch_websocket(url, json_rpc_request)
            elif protocol == "stdio":
                return await MCPProxyService._fetch_stdio(url, json_rpc_request)
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")
        except Exception as e:
            return {"error": f"Failed to fetch tools: {e}"}

    # ----------------------------------------------------------------------
    # ✅ HTTP with Fallback Logic
    # ----------------------------------------------------------------------
    @staticmethod
    async def _fetch_http_with_fallback(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        HTTP 요청에 대해 다음 순서로 fallback 시도:
        1. POST → 2. GET → 3. HTTP-stream (NDJSON or SSE)
        """
        try:
            # 1️⃣ 기본 POST 요청
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 405:  # Method Not Allowed
                        # 2️⃣ GET fallback
                        async with session.get(url) as get_resp:
                            if get_resp.status == 200:
                                try:
                                    return await get_resp.json()
                                except aiohttp.ContentTypeError:
                                    text = await get_resp.text()
                                    return {"raw": text, "message": "Non-JSON response received"}
                    else:
                        # 3️⃣ HTTP-stream fallback (chunked NDJSON)
                        try:
                            return await MCPProxyService._fetch_http_stream(url, payload)
                        except Exception as se:
                            raise Exception(f"HTTP fallback (stream) failed: {se}")
            raise Exception("No valid HTTP response")
        except Exception as e:
            raise Exception(f"HTTP request failed: {e}")

    # ----------------------------------------------------------------------
    # ✅ HTTP-stream (NDJSON + SSE 자동 감지)
    # ----------------------------------------------------------------------
    @staticmethod
    async def _fetch_http_stream(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        HTTP-stream (NDJSON or SSE) 프로토콜 지원.
        서버가 'application/x-ndjson' 또는 'text/event-stream'으로 응답하는 경우 모두 커버.
        """
        tools = []
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={
                    "Accept": "application/json, application/x-ndjson, text/event-stream"
                },
                timeout=aiohttp.ClientTimeout(total=20)
            ) as response:
                content_type = response.headers.get("Content-Type", "")

                # 💡 1️⃣ 일반 JSON 응답
                if "application/json" in content_type:
                    data = await response.json()
                    return data

                # 💡 2️⃣ 스트림 응답 (NDJSON / SSE)
                async for line in response.content:
                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue

                    # SSE 형식 (data: prefix)
                    if line_str.startswith("data:"):
                        line_str = line_str[5:].strip()
                        if line_str == "[DONE]":
                            break

                    try:
                        data = json.loads(line_str)
                        # 다양한 서버 응답 형태 호환
                        if "result" in data and "tools" in data["result"]:
                            tools = data["result"]["tools"]
                            break
                        elif "tools" in data:
                            tools = data["tools"]
                            break
                    except json.JSONDecodeError:
                        continue

        if not tools:
            raise Exception("No tools found in stream response.")
        return {"jsonrpc": "2.0", "result": {"tools": tools}}

    # ----------------------------------------------------------------------
    # ✅ WebSocket
    # ----------------------------------------------------------------------
    @staticmethod
    async def _fetch_websocket(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request over WebSocket transport."""
        try:
            async with websockets.connect(url, ping_interval=None) as ws:
                await ws.send(json.dumps(payload))
                async for message in ws:
                    try:
                        data = json.loads(message)
                        if data.get("id") == payload["id"]:
                            return data
                    except json.JSONDecodeError:
                        continue
            raise Exception("No matching WebSocket response received.")
        except Exception as e:
            raise Exception(f"WebSocket connection failed: {e}")

    # ----------------------------------------------------------------------
    # ✅ stdio (local process execution)
    # ----------------------------------------------------------------------
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
            stdout, stderr = await proc.communicate(input=req.encode())

            if stderr:
                sys.stderr.write(stderr.decode())

            for line in stdout.decode().splitlines():
                if line.strip():
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            raise Exception("No valid JSON response from stdio process.")
        except Exception as e:
            raise Exception(f"Stdio execution failed: {e}")

```
