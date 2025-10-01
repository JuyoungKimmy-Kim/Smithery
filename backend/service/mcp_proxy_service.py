"""
MCP 프록시 서비스
Frontend에서 MCP 서버의 tools를 미리보기할 때 사용하는 프록시 서비스
HTTPS → HTTP Mixed Content 문제와 CORS 문제를 해결
"""

import asyncio
import aiohttp
import json
import subprocess
from typing import Dict, Any, List, Optional


class MCPProxyService:
    """MCP 서버와 통신하는 프록시 서비스"""
    
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
                return {
                    "success": False,
                    "tools": [],
                    "message": f"Unsupported protocol: {protocol}"
                }
        except Exception as e:
            return {
                "success": False,
                "tools": [],
                "message": f"Failed to fetch tools: {str(e)}"
            }
    
    @staticmethod
    async def _fetch_http(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP 프로토콜로 tools 가져오기"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tools = data.get("result", {}).get("tools", [])
                    return {
                        "success": True,
                        "tools": tools,
                        "message": "Tools fetched successfully"
                    }
                else:
                    return {
                        "success": False,
                        "tools": [],
                        "message": f"HTTP request failed with status {response.status}"
                    }
    
    @staticmethod
    async def _fetch_http_stream(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP-Stream (SSE) 프로토콜로 tools 가져오기"""
        post_error = None
        get_error = None
        
        async with aiohttp.ClientSession() as session:
            # 먼저 POST로 직접 시도 (단일 요청/응답 패턴)
            try:
                print(f"[HTTP-Stream] Trying POST to {url}")
                async with session.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    print(f"[HTTP-Stream] POST response: status={response.status}, content-type={response.headers.get('Content-Type')}")
                    
                    # 405 Method Not Allowed가 아니면 처리
                    if response.status != 405:
                        result = await MCPProxyService._handle_http_response(response)
                        print(f"[HTTP-Stream] POST result: success={result.get('success')}, tools_count={len(result.get('tools', []))}")
                        return result
                    
                    # 405면 두 단계 구조 시도
                    post_error = f"POST returned 405 Method Not Allowed"
                    print(f"[HTTP-Stream] {post_error}, trying two-step stream pattern")
            except asyncio.TimeoutError:
                post_error = "POST request timed out after 30 seconds"
                print(f"[HTTP-Stream] {post_error}")
            except Exception as e:
                post_error = f"POST failed: {type(e).__name__}: {str(e)}"
                print(f"[HTTP-Stream] {post_error}")
            
            # 두 단계 구조 시도: GET으로 스트림 열고 → POST로 요청
            try:
                print(f"[HTTP-Stream] Trying two-step pattern: GET stream + POST request")
                return await MCPProxyService._fetch_two_step_stream(session, url, payload)
            except asyncio.TimeoutError:
                get_error = "Two-step stream request timed out"
                print(f"[HTTP-Stream] {get_error}")
            except Exception as e:
                get_error = f"Two-step stream failed: {type(e).__name__}: {str(e)}"
                print(f"[HTTP-Stream] {get_error}")
            
            # 모든 방법 실패
            return {
                "success": False,
                "tools": [],
                "message": f"All methods failed - POST: {post_error}, Two-step: {get_error}"
            }
    
    @staticmethod
    async def _fetch_two_step_stream(session: aiohttp.ClientSession, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        두 단계 HTTP-Stream 처리:
        1. GET으로 SSE 스트림 열기 (연결 유지)
        2. 스트림에서 endpoint와 session_id 받기
        3. POST로 JSON-RPC 요청 (session_id 포함)
        4. 스트림에서 응답 받기
        """
        print(f"[Two-Step] Opening SSE stream with GET to {url}")
        
        # 1단계: GET으로 스트림 열기
        async with session.get(
            url,
            headers={"Accept": "text/event-stream"},
            timeout=aiohttp.ClientTimeout(total=60)
        ) as stream_response:
            if stream_response.status != 200:
                raise Exception(f"Failed to open stream: status={stream_response.status}")
            
            print(f"[Two-Step] Stream opened, waiting for endpoint and session_id")
            
            endpoint = None
            session_id = None
            
            # 스트림에서 endpoint와 session_id 읽기
            async for line in stream_response.content:
                line_str = line.decode('utf-8').strip()
                print(f"[Two-Step] Stream line: {line_str}")
                
                if line_str.startswith('data:'):
                    data_str = line_str[5:].strip()
                    try:
                        data = json.loads(data_str)
                        
                        # endpoint와 session_id 추출
                        if 'endpoint' in data:
                            endpoint = data.get('endpoint')
                            session_id = data.get('session_id')
                            print(f"[Two-Step] Received endpoint={endpoint}, session_id={session_id}")
                            break
                    except json.JSONDecodeError:
                        continue
            
            if not endpoint:
                raise Exception("No endpoint received from stream")
            
            # 2단계: POST로 JSON-RPC 요청 (session_id 포함)
            print(f"[Two-Step] Sending POST to {endpoint} with session_id={session_id}")
            
            # payload에 session_id 추가
            payload_with_session = {**payload}
            if session_id:
                payload_with_session['session_id'] = session_id
            
            # 별도 요청으로 POST 전송
            async with session.post(
                endpoint,
                json=payload_with_session,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as post_response:
                print(f"[Two-Step] POST response: status={post_response.status}")
                
                # POST는 202나 200을 반환할 수 있음 (결과는 스트림으로)
                if post_response.status not in [200, 202]:
                    raise Exception(f"POST request failed: status={post_response.status}")
            
            # 3단계: 스트림에서 응답 받기
            print(f"[Two-Step] Waiting for response in stream")
            
            tools = []
            async for line in stream_response.content:
                line_str = line.decode('utf-8').strip()
                print(f"[Two-Step] Response line: {line_str}")
                
                if line_str.startswith('data:'):
                    data_str = line_str[5:].strip()
                    if data_str and data_str != '[DONE]':
                        try:
                            data = json.loads(data_str)
                            
                            # tools/list 응답 확인
                            if 'result' in data and 'tools' in data['result']:
                                tools = data['result']['tools']
                                print(f"[Two-Step] Received {len(tools)} tools")
                                break
                            elif 'tools' in data:
                                tools = data['tools']
                                print(f"[Two-Step] Received {len(tools)} tools")
                                break
                        except json.JSONDecodeError:
                            continue
            
            return {
                "success": True,
                "tools": tools,
                "message": "Tools fetched successfully via two-step stream"
            }
    
    @staticmethod
    async def _handle_http_response(response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """HTTP 응답 처리 (POST/GET 공통)"""
        content_type = response.headers.get('Content-Type', '').lower()
        
        # 1. Content-Type으로 먼저 판단
        if 'application/json' in content_type:
            # JSON 응답인 경우 - 즉시 처리
            data = await response.json()
            
            # 정상 응답 (200, 201 등)
            if response.status in [200, 201]:
                tools = data.get("result", {}).get("tools", [])
                return {
                    "success": True,
                    "tools": tools,
                    "message": "Tools fetched successfully"
                }
            
            # 202 Accepted - 처리 진행 중이지만 결과를 기다림
            elif response.status == 202:
                # 응답 본문에 이미 결과가 있으면 사용
                if "result" in data and "tools" in data["result"]:
                    tools = data["result"]["tools"]
                    return {
                        "success": True,
                        "tools": tools,
                        "message": "Tools fetched successfully"
                    }
                # 결과가 없으면 에러 처리
                return {
                    "success": False,
                    "tools": [],
                    "message": f"Request accepted but no result available: {data}"
                }
            
            # 기타 에러
            else:
                return {
                    "success": False,
                    "tools": [],
                    "message": f"HTTP request failed with status {response.status}: {data}"
                }
        
        # 2. SSE 스트림 응답인 경우
        elif 'text/event-stream' in content_type:
            return await MCPProxyService._process_sse_stream(response)
        
        # 3. Content-Type이 명확하지 않은 경우 - 본문을 읽어서 판단
        else:
            text = await response.text()
            
            # JSON 파싱 시도
            try:
                data = json.loads(text)
                tools = data.get("result", {}).get("tools", [])
                return {
                    "success": True,
                    "tools": tools,
                    "message": "Tools fetched successfully"
                }
            except json.JSONDecodeError:
                # SSE 형식인지 확인
                if text.strip().startswith('data:'):
                    # SSE를 텍스트로 파싱
                    return MCPProxyService._parse_sse_text(text)
                
                return {
                    "success": False,
                    "tools": [],
                    "message": f"Unknown response format. Status: {response.status}, Content-Type: {content_type}"
                }
    
    @staticmethod
    async def _process_sse_stream(response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """SSE 스트림 데이터 처리"""
        tools = []
        async for line in response.content:
            line_str = line.decode('utf-8').strip()
            if line_str.startswith('data:'):
                try:
                    data_str = line_str[5:].strip()
                    if data_str and data_str != '[DONE]':
                        data = json.loads(data_str)
                        
                        # 다양한 응답 형식 처리
                        if 'result' in data and 'tools' in data['result']:
                            tools = data['result']['tools']
                            break
                        elif isinstance(data, list) and len(data) > 0:
                            tools = data
                            break
                        elif 'tools' in data:
                            tools = data['tools']
                            break
                except json.JSONDecodeError:
                    continue
        
        return {
            "success": True,
            "tools": tools,
            "message": "Tools fetched successfully from SSE stream"
        }
    
    @staticmethod
    def _parse_sse_text(text: str) -> Dict[str, Any]:
        """SSE 텍스트를 파싱"""
        tools = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('data:'):
                try:
                    data_str = line[5:].strip()
                    if data_str and data_str != '[DONE]':
                        data = json.loads(data_str)
                        
                        # 다양한 응답 형식 처리
                        if 'result' in data and 'tools' in data['result']:
                            tools = data['result']['tools']
                            break
                        elif isinstance(data, list) and len(data) > 0:
                            tools = data
                            break
                        elif 'tools' in data:
                            tools = data['tools']
                            break
                except json.JSONDecodeError:
                    continue
        
        return {
            "success": True,
            "tools": tools,
            "message": "Tools fetched successfully from SSE text"
        }
    
    @staticmethod
    async def _fetch_websocket(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 프로토콜로 tools 가져오기"""
        try:
            # http:// -> ws:// 변환
            ws_url = url.replace('http://', 'ws://').replace('https://', 'wss://')
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(ws_url, timeout=10) as ws:
                    # JSON-RPC 요청 전송
                    await ws.send_json(payload)
                    
                    # 응답 대기
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            # ID가 일치하는 응답만 처리
                            if data.get('id') == payload['id']:
                                tools = data.get("result", {}).get("tools", [])
                                return {
                                    "success": True,
                                    "tools": tools,
                                    "message": "Tools fetched successfully"
                                }
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                    
                    return {
                        "success": False,
                        "tools": [],
                        "message": "No response from WebSocket server"
                    }
        except Exception as e:
            return {
                "success": False,
                "tools": [],
                "message": f"WebSocket connection failed: {str(e)}"
            }
    
    @staticmethod
    async def _fetch_stdio(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """STDIO 프로토콜로 tools 가져오기"""
        try:
            # 명령어를 공백으로 분리
            cmd_parts = command.split()
            if not cmd_parts:
                return {
                    "success": False,
                    "tools": [],
                    "message": "Invalid command"
                }
            
            # 프로세스 실행
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # JSON-RPC 요청 전송
            request_str = json.dumps(payload) + "\n"
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=request_str.encode('utf-8')),
                timeout=10
            )
            
            # 응답 파싱
            if stdout:
                try:
                    data = json.loads(stdout.decode('utf-8'))
                    if data.get('id') == payload['id']:
                        tools = data.get("result", {}).get("tools", [])
                        return {
                            "success": True,
                            "tools": tools,
                            "message": "Tools fetched successfully"
                        }
                except json.JSONDecodeError:
                    pass
            
            return {
                "success": False,
                "tools": [],
                "message": f"STDIO process error: {stderr.decode('utf-8') if stderr else 'Unknown error'}"
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "tools": [],
                "message": "STDIO process timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "tools": [],
                "message": f"STDIO process failed: {str(e)}"
            }

