"""
Transport 인터페이스와 구현체들
MCP 서버와의 통신을 위한 다양한 프로토콜 지원
"""

import asyncio
import aiohttp
import json
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator
import sys


class Transport(ABC):
    """Transport 인터페이스"""
    
    @abstractmethod
    async def write(self, message: str) -> None:
        """메시지 전송"""
        pass
    
    @abstractmethod
    async def read(self) -> str:
        """메시지 수신"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """연결 종료"""
        pass


class JsonRpcClient:
    """JSON-RPC 클라이언트"""
    
    def __init__(self, transport: Transport):
        self.transport = transport
        self._id = 0
    
    def _next_id(self) -> int:
        self._id += 1
        return self._id
    
    async def request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """JSON-RPC 요청 전송"""
        req_id = self._next_id()
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }
        
        await self.transport.write(json.dumps(payload))
        response = await self.transport.read()
        return json.loads(response)


class HttpTransport(Transport):
    """HTTP 프로토콜 Transport"""
    
    def __init__(self, url: str):
        self.url = url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def write(self, message: str) -> None:
        """HTTP POST 요청으로 메시지 전송"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        payload = json.loads(message)
        async with self.session.post(
            self.url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status == 200:
                data = await response.json()
                self._last_response = json.dumps(data)
            else:
                error_data = {
                    "error": {
                        "code": response.status,
                        "message": f"HTTP request failed with status {response.status}"
                    }
                }
                self._last_response = json.dumps(error_data)
    
    async def read(self) -> str:
        """마지막 응답 반환"""
        return getattr(self, '_last_response', '{"error": {"message": "No response"}}')
    
    async def close(self) -> None:
        """세션 종료"""
        if self.session:
            await self.session.close()
            self.session = None


class HttpStreamTransport(Transport):
    """HTTP-Stream (SSE) 프로토콜 Transport"""
    
    def __init__(self, url: str):
        self.url = url
        self.session: Optional[aiohttp.ClientSession] = None
        self.session_id: Optional[str] = None
        self._last_response: str = ""
        print(f"[HttpStreamTransport] 초기화: URL={url}")
    
    async def write(self, message: str) -> None:
        """HTTP-Stream 요청 전송"""
        print(f"[HttpStreamTransport] write 호출: message={message[:100]}...")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            print(f"[HttpStreamTransport] 새 세션 생성")
        
        payload = json.loads(message)
        print(f"[HttpStreamTransport] 파싱된 payload: {payload}")
        
        # 먼저 세션 기반 스트림 시도
        if not self.session_id:
            print(f"[HttpStreamTransport] 세션 ID 없음, 세션 모드 시도")
            await self._try_session_mode()
        
        if self.session_id:
            # 세션 기반 모드
            print(f"[HttpStreamTransport] 세션 기반 모드 사용: session_id={self.session_id}")
            payload["session_id"] = self.session_id
            rpc_url = f"{self.url.rstrip('/')}/rpc"
            print(f"[HttpStreamTransport] RPC 요청 URL: {rpc_url}")
            
            try:
                async with self.session.post(
                    rpc_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    print(f"[HttpStreamTransport] 세션 요청 응답: status={response.status}")
                    print(f"[HttpStreamTransport] 응답 헤더: {dict(response.headers)}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"[HttpStreamTransport] 세션 응답 성공: {data}")
                        self._last_response = json.dumps(data)
                    else:
                        response_text = await response.text()
                        print(f"[HttpStreamTransport] 세션 요청 실패: status={response.status}, body={response_text}")
                        error_data = {
                            "error": {
                                "code": response.status,
                                "message": f"Session request failed with status {response.status}",
                                "details": response_text
                            }
                        }
                        self._last_response = json.dumps(error_data)
            except Exception as e:
                print(f"[HttpStreamTransport] 세션 요청 예외: {e}")
                error_data = {
                    "error": {
                        "message": f"Session request exception: {str(e)}"
                    }
                }
                self._last_response = json.dumps(error_data)
        else:
            # POST + SSE 기반 모드
            print(f"[HttpStreamTransport] POST + SSE 기반 모드 사용")
            await self._post_stream_mode(payload)
    
    async def _try_session_mode(self) -> None:
        """세션 기반 스트림 모드 시도"""
        stream_url = f"{self.url.rstrip('/')}/stream"
        print(f"[HttpStreamTransport] 세션 모드 시도: URL={stream_url}")
        
        try:
            async with self.session.get(
                stream_url,
                headers={"Accept": "text/event-stream"},
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                print(f"[HttpStreamTransport] 스트림 요청 응답: status={response.status}")
                print(f"[HttpStreamTransport] 스트림 응답 헤더: {dict(response.headers)}")
                
                if response.status == 200:
                    print(f"[HttpStreamTransport] 스트림 연결 성공, 세션 ID 대기 중...")
                    line_count = 0
                    async for line in response.content:
                        line_count += 1
                        line_str = line.decode('utf-8').strip()
                        print(f"[HttpStreamTransport] 스트림 라인 {line_count}: {line_str}")
                        
                        if line_str.startswith('data:'):
                            try:
                                data_str = line_str[5:].strip()
                                if data_str and data_str != '[DONE]':
                                    data = json.loads(data_str)
                                    print(f"[HttpStreamTransport] 파싱된 스트림 데이터: {data}")
                                    if data.get("event") == "session":
                                        self.session_id = data.get("session_id")
                                        print(f"[HttpStreamTransport] 세션 ID 획득: {self.session_id}")
                                        break
                            except json.JSONDecodeError as e:
                                print(f"[HttpStreamTransport] JSON 파싱 실패: {e}, data={data_str}")
                                continue
                    
                    if not self.session_id:
                        print(f"[HttpStreamTransport] 세션 ID를 찾을 수 없음 (처리된 라인: {line_count})")
                else:
                    response_text = await response.text()
                    print(f"[HttpStreamTransport] 스트림 요청 실패: status={response.status}, body={response_text}")
        except Exception as e:
            print(f"[HttpStreamTransport] 세션 모드 예외: {e}")
            # 세션 모드 실패 시 POST 모드로 fallback
    
    async def _post_stream_mode(self, payload: Dict[str, Any]) -> None:
        """POST + SSE 기반 모드"""
        print(f"[HttpStreamTransport] POST 스트림 모드 시작: URL={self.url}")
        print(f"[HttpStreamTransport] POST payload: {payload}")
        
        try:
            async with self.session.post(
                self.url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                content_type = response.headers.get('Content-Type', '')
                print(f"[HttpStreamTransport] POST 응답: status={response.status}, content_type={content_type}")
                print(f"[HttpStreamTransport] POST 응답 헤더: {dict(response.headers)}")
                
                # 200 OK + JSON 응답인 경우 (즉시 응답)
                if response.status == 200 and 'application/json' in content_type:
                    print(f"[HttpStreamTransport] 즉시 JSON 응답 처리")
                    data = await response.json()
                    print(f"[HttpStreamTransport] JSON 응답 데이터: {data}")
                    self._last_response = json.dumps(data)
                    return
                
                # 202 Accepted 응답인 경우 (SSE 스트림으로 전환)
                if response.status == 202:
                    print(f"[HttpStreamTransport] 202 Accepted, 스트림 URL 획득 시도")
                    response_data = await response.json()
                    print(f"[HttpStreamTransport] 202 응답 데이터: {response_data}")
                    stream_url = response_data.get('stream_url') or response_data.get('endpoint') or self.url
                    print(f"[HttpStreamTransport] 스트림 URL: {stream_url}")
                    await self._fetch_sse_stream(stream_url)
                    return
                
                # 200 OK + SSE 스트림인 경우 (바로 스트림 응답)
                if response.status == 200:
                    print(f"[HttpStreamTransport] 200 OK + SSE 스트림 처리")
                    await self._process_sse_stream(response)
                    return
                
                # 기타 오류
                response_text = await response.text()
                print(f"[HttpStreamTransport] POST 요청 실패: status={response.status}, body={response_text}")
                error_data = {
                    "error": {
                        "code": response.status,
                        "message": f"HTTP-Stream request failed with status {response.status}",
                        "details": response_text
                    }
                }
                self._last_response = json.dumps(error_data)
        except Exception as e:
            print(f"[HttpStreamTransport] POST 스트림 모드 예외: {e}")
            error_data = {
                "error": {
                    "message": f"HTTP-Stream request failed: {str(e)}"
                }
            }
            self._last_response = json.dumps(error_data)
    
    async def _fetch_sse_stream(self, stream_url: str) -> None:
        """GET 요청으로 SSE 스트림 구독"""
        print(f"[HttpStreamTransport] SSE 스트림 구독: URL={stream_url}")
        
        try:
            async with self.session.get(
                stream_url,
                headers={"Accept": "text/event-stream"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"[HttpStreamTransport] SSE 스트림 응답: status={response.status}")
                print(f"[HttpStreamTransport] SSE 응답 헤더: {dict(response.headers)}")
                
                if response.status == 200:
                    print(f"[HttpStreamTransport] SSE 스트림 연결 성공, 데이터 처리 시작")
                    await self._process_sse_stream(response)
                else:
                    response_text = await response.text()
                    print(f"[HttpStreamTransport] SSE 스트림 요청 실패: status={response.status}, body={response_text}")
                    error_data = {
                        "error": {
                            "code": response.status,
                            "message": f"SSE stream request failed with status {response.status}",
                            "details": response_text
                        }
                    }
                    self._last_response = json.dumps(error_data)
        except Exception as e:
            print(f"[HttpStreamTransport] SSE 스트림 연결 예외: {e}")
            error_data = {
                "error": {
                    "message": f"Failed to connect to SSE stream: {str(e)}"
                }
            }
            self._last_response = json.dumps(error_data)
    
    async def _process_sse_stream(self, response: aiohttp.ClientResponse) -> None:
        """SSE 스트림 데이터 처리"""
        print(f"[HttpStreamTransport] SSE 스트림 데이터 처리 시작")
        tools = []
        line_count = 0
        
        async for line in response.content:
            line_count += 1
            line_str = line.decode('utf-8').strip()
            print(f"[HttpStreamTransport] SSE 라인 {line_count}: {line_str}")
            
            if line_str.startswith('data:'):
                try:
                    data_str = line_str[5:].strip()
                    print(f"[HttpStreamTransport] SSE 데이터: {data_str}")
                    
                    if data_str and data_str != '[DONE]':
                        data = json.loads(data_str)
                        print(f"[HttpStreamTransport] 파싱된 SSE 데이터: {data}")
                        
                        # 다양한 응답 형식 처리
                        if 'result' in data and 'tools' in data['result']:
                            tools = data['result']['tools']
                            print(f"[HttpStreamTransport] result.tools 형식으로 tools 발견: {len(tools)}개")
                            break
                        elif isinstance(data, list) and len(data) > 0:
                            tools = data
                            print(f"[HttpStreamTransport] 리스트 형식으로 tools 발견: {len(tools)}개")
                            break
                        elif 'tools' in data:
                            tools = data['tools']
                            print(f"[HttpStreamTransport] 직접 tools 형식으로 tools 발견: {len(tools)}개")
                            break
                        else:
                            print(f"[HttpStreamTransport] tools를 찾을 수 없는 데이터 형식")
                    elif data_str == '[DONE]':
                        print(f"[HttpStreamTransport] 스트림 종료 신호 [DONE] 수신")
                        break
                except json.JSONDecodeError as e:
                    print(f"[HttpStreamTransport] SSE JSON 파싱 실패: {e}, data={data_str}")
                    continue
        
        print(f"[HttpStreamTransport] SSE 처리 완료: 총 {line_count}라인, {len(tools)}개 tools")
        result_data = {
            "result": {
                "tools": tools
            }
        }
        self._last_response = json.dumps(result_data)
    
    async def read(self) -> str:
        """마지막 응답 반환"""
        return self._last_response
    
    async def close(self) -> None:
        """세션 종료"""
        if self.session:
            await self.session.close()
            self.session = None


class WebSocketTransport(Transport):
    """WebSocket 프로토콜 Transport"""
    
    def __init__(self, url: str):
        # http:// -> ws:// 변환
        self.url = url.replace('http://', 'ws://').replace('https://', 'wss://')
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._last_response: str = ""
    
    async def write(self, message: str) -> None:
        """WebSocket으로 메시지 전송"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        if not self.ws:
            self.ws = await self.session.ws_connect(self.url, timeout=10)
        
        payload = json.loads(message)
        await self.ws.send_json(payload)
        
        # 응답 대기
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                
                # ID가 일치하는 응답만 처리
                if data.get('id') == payload['id']:
                    self._last_response = json.dumps(data)
                    break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                error_data = {
                    "error": {
                        "message": "WebSocket connection error"
                    }
                }
                self._last_response = json.dumps(error_data)
                break
    
    async def read(self) -> str:
        """마지막 응답 반환"""
        return self._last_response
    
    async def close(self) -> None:
        """WebSocket 연결 종료"""
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self.session:
            await self.session.close()
            self.session = None


class StdioTransport(Transport):
    """STDIO 프로토콜 Transport"""
    
    def __init__(self, command: str):
        self.command = command.split()
        self.process: Optional[asyncio.subprocess.Process] = None
        self._last_response: str = ""
    
    async def write(self, message: str) -> None:
        """STDIO로 메시지 전송"""
        if not self.command:
            error_data = {
                "error": {
                    "message": "Invalid command"
                }
            }
            self._last_response = json.dumps(error_data)
            return
        
        try:
            # 프로세스 실행
            if not self.process:
                self.process = await asyncio.create_subprocess_exec(
                    *self.command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            # JSON-RPC 요청 전송
            request_str = message + "\n"
            stdout, stderr = await asyncio.wait_for(
                self.process.communicate(input=request_str.encode('utf-8')),
                timeout=10
            )
            
            # 응답 파싱
            if stdout:
                try:
                    data = json.loads(stdout.decode('utf-8'))
                    self._last_response = json.dumps(data)
                except json.JSONDecodeError:
                    error_data = {
                        "error": {
                            "message": f"STDIO process error: {stderr.decode('utf-8') if stderr else 'Unknown error'}"
                        }
                    }
                    self._last_response = json.dumps(error_data)
            else:
                error_data = {
                    "error": {
                        "message": f"STDIO process error: {stderr.decode('utf-8') if stderr else 'Unknown error'}"
                    }
                }
                self._last_response = json.dumps(error_data)
                
        except asyncio.TimeoutError:
            error_data = {
                "error": {
                    "message": "STDIO process timeout"
                }
            }
            self._last_response = json.dumps(error_data)
        except Exception as e:
            error_data = {
                "error": {
                    "message": f"STDIO process failed: {str(e)}"
                }
            }
            self._last_response = json.dumps(error_data)
    
    async def read(self) -> str:
        """마지막 응답 반환"""
        return self._last_response
    
    async def close(self) -> None:
        """프로세스 종료"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None


def create_transport(protocol: str, url_or_command: str) -> Transport:
    """프로토콜에 따라 적절한 Transport 생성"""
    if protocol == "http":
        return HttpTransport(url_or_command)
    elif protocol == "http-stream":
        return HttpStreamTransport(url_or_command)
    elif protocol == "websocket":
        return WebSocketTransport(url_or_command)
    elif protocol == "stdio":
        return StdioTransport(url_or_command)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")
