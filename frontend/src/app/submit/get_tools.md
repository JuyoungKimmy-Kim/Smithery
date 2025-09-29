# Automatically Get Tools List - 세부 구현 계획

## 📋 전체 플로우
1. Deploy Server 과정에서 User가 Server Config 항목을 입력하였을 때, Tools Preview가 생긴다.
2. MCP Server가 띄워져 있고, type=streamable-http 라면, POST로 JSON-RPC 요청 (tools/list)를 보냄
3. 서버는 응답을 SSE 스트림으로 흘려줌
4. tools/list 요청을 통해 tools를 받아와서 Preview 표시가 가능하게 함

## 🔧 세부 구현 단계

### 1단계: Server Config 변경 감지 및 트리거 로직 ✅
- [x] `handleConfigChange` 함수 구현
- [x] JSON 파싱 및 유효성 검사
- [x] `type=streamable-http` 및 `url` 필드 확인
- [x] Server Config 필드에 onChange 이벤트 연결

### 2단계: MCP Server 상태 확인 ✅
- [x] `checkMCPServerStatus` 함수 구현
- [x] HTTP HEAD 요청으로 서버 응답 가능 여부 확인
- [x] 타임아웃 설정 (3초)
- [x] 에러 처리 및 사용자 피드백

### 3단계: JSON-RPC tools/list 요청 ✅
- [x] `requestToolsList` 함수 구현
- [x] JSON-RPC 2.0 형식으로 요청 구성
- [x] POST 요청 헤더 설정 (Content-Type, Accept)
- [x] SSE 스트림 응답 처리 준비

### 4단계: SSE 스트림 처리 ✅
- [x] `handleSSEStream` 함수 구현
- [x] ReadableStream 처리
- [x] TextDecoder로 스트림 데이터 디코딩
- [x] `data: ` 라인 파싱 및 JSON 응답 처리
- [x] `[DONE]` 시그널 감지

### 5단계: Tools 데이터 처리 및 UI 업데이트 ✅
- [x] 받아온 tools 데이터 구조 분석
- [x] `setPreviewTools`로 상태 업데이트
- [x] Tools Preview UI 개선
- [x] Parameters 정보 표시
- [x] 에러 상태 UI 추가

### 6단계: 통합 및 최적화 ✅
- [x] 기존 GitHub 링크 기반 로직 제거 (MCP Server 전용으로 변경)
- [x] 로딩 상태 관리 개선
- [x] 에러 핸들링 강화
- [x] 사용자 경험 최적화 완료

## 📝 구현 예시 코드

### Server Config 변경 감지
```typescript
const handleConfigChange = async (configValue: string) => {
  if (!configValue.trim()) {
    setPreviewTools([]);
    return;
  }
  
  try {
    const config = JSON.parse(configValue);
    if (config.type === 'streamable-http' && config.url) {
      await detectAndPreviewTools(config);
    }
  } catch (error) {
    console.error('Config 파싱 실패:', error);
  }
};
```

### MCP Server 상태 확인
```typescript
const checkMCPServerStatus = async (url: string) => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    
    const response = await fetch(url, {
      method: 'HEAD',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return { isRunning: response.ok };
  } catch (error) {
    return { isRunning: false };
  }
};
```

### JSON-RPC 요청
```typescript
const requestToolsList = async (config: any) => {
  const jsonRpcRequest = {
    jsonrpc: "2.0",
    method: "tools/list",
    id: Date.now(),
    params: {}
  };

  const response = await fetch(config.url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream'
    },
    body: JSON.stringify(jsonRpcRequest)
  });

  if (response.ok) {
    await handleSSEStream(response);
  }
};
```

### SSE 스트림 처리
```typescript
const handleSSEStream = async (response: Response) => {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') break;
        
        try {
          const parsed = JSON.parse(data);
          if (parsed.result?.tools) {
            setPreviewTools(parsed.result.tools);
          }
        } catch (e) {
          console.error('SSE 데이터 파싱 실패:', e);
        }
      }
    }
  }
};
```

## ✅ 구현 완료 상태

### 🎉 주요 구현 완료 사항
1. **Server Config 기반 Tools 미리보기**: Server Config 입력 시 실시간 MCP Server 연결
2. **실시간 MCP Server 감지**: `type=streamable-http` 설정 시 자동으로 서버 상태 확인
3. **JSON-RPC 통신**: 표준 JSON-RPC 2.0 프로토콜로 `tools/list` 요청
4. **SSE 스트림 처리**: Server-Sent Events로 실시간 tools 데이터 수신
5. **데이터 형식 변환**: MCP 서버의 `inputSchema`를 `MCPServerTool` 형식으로 변환
6. **향상된 UI**: Parameters 정보, 타입, 필수 여부 등을 상세히 표시
7. **에러 처리**: 연결 실패, 타임아웃, 파싱 오류 등 다양한 상황 대응
8. **GitHub 링크 로직 제거**: MCP Server 전용으로 단순화

### 🔧 구현된 주요 함수들
- `handleConfigChange()`: Server Config 변경 감지 및 트리거
- `checkMCPServerStatus()`: MCP Server 상태 확인 (3초 타임아웃)
- `requestToolsList()`: JSON-RPC tools/list 요청
- `handleSSEStream()`: SSE 스트림 데이터 처리
- `detectAndPreviewTools()`: 전체 플로우 조율

### 📋 사용 방법
1. Server Config 필드에 다음과 같은 JSON 입력:
```json
{
  "type": "streamable-http",
  "url": "http://localhost:3000"
}
```
2. 자동으로 MCP Server 연결 시도
3. 연결 성공 시 tools 목록 미리보기 표시
4. "모두 추가" 버튼으로 tools를 폼에 추가

## 🎯 테스트 및 최적화
실제 MCP Server와의 연동 테스트가 필요합니다.