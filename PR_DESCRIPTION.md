# 🎮 Playground 기능 추가

## 개요

MCP 서버를 브라우저에서 직접 테스트할 수 있는 **Playground** 기능을 추가했습니다. 로그인한 사용자가 LLM과 대화하며 MCP 서버의 Tools를 실제로 사용해볼 수 있습니다.

## 주요 기능

### 1. 🤖 LLM + MCP 통합
- OpenAI GPT 모델과 MCP 서버 연동
- LLM이 필요 시 MCP Tools를 자동으로 호출
- Tool 실행 결과를 기반으로 최종 답변 생성

### 2. 💬 실시간 채팅 인터페이스
- MCP 서버 상세 페이지에 Playground 섹션 추가
- 사용자 메시지 입력 및 AI 응답 표시
- Tool 호출 내역 시각화 (어떤 tool을 사용했는지 표시)
- 대화 히스토리 유지 및 Clear 기능

### 3. 🔒 사용량 제한 (Rate Limiting)
- 로그인한 사용자만 접근 가능
- **일일 10회** 쿼리 제한 (사용자별, MCP 서버별)
- KST(한국 시간) 자정에 자동 리셋
- UI에서 실시간 사용량 표시 (예: 7/10 queries today)

### 4. 🌐 다양한 LLM API 지원
- OpenAI GPT-4/GPT-3.5 지원
- DeepSeek API 지원
- 사내 LLM API 연동 가능 (base_url 설정)
- 환경변수로 간편하게 전환

### 5. 🔧 MCP Transport 지원
- STDIO, SSE, HTTP 모든 프로토콜 지원
- MCP Tool 호출 기능 구현 (call_tool 메서드 추가)
- Tool 결과 파싱 및 LLM 전달

## 기술 스택

### Backend
- **FastAPI**: Playground API 엔드포인트
- **OpenAI SDK**: LLM 통합 및 Function Calling
- **SQLAlchemy**: 사용량 추적 DB
- **MCP SDK**: MCP 서버 통신
- **pytz**: KST 타임존 지원

### Frontend
- **React/Next.js**: Playground UI 컴포넌트
- **Tailwind CSS**: 스타일링
- **TypeScript**: 타입 안전성

## 파일 변경 사항

### 새로 추가된 파일
- `backend/service/playground_service.py` - LLM + MCP 통합 로직
- `backend/api/endpoints/playground.py` - Playground API 엔드포인트
- `backend/database/model/playground_usage.py` - 사용량 추적 모델
- `frontend/src/components/playground-chat.tsx` - 채팅 UI 컴포넌트
- `frontend/src/app/api/mcps/[id]/playground/` - Next.js API 라우트
- `PLAYGROUND_SETUP.md` - 상세 설정 가이드
- `.env.example` - 환경변수 템플릿

### 주요 수정된 파일
- `backend/service/mcp_proxy_service.py` - call_tool 메서드 추가
- `backend/api/schemas.py` - Playground 스키마 추가
- `frontend/src/app/mcp/[id]/page.tsx` - Playground 섹션 추가
- `backend/main.py` - .env 파일 자동 로딩
- `requirements.txt` - 새 의존성 추가

## API 엔드포인트

### 1. Rate Limit 확인
```
GET /api/v1/mcp-servers/{server_id}/playground/rate-limit
Authorization: Bearer {token}

Response:
{
  "allowed": true,
  "remaining": 8,
  "used": 2
}
```

### 2. 채팅
```
POST /api/v1/mcp-servers/{server_id}/playground/chat
Authorization: Bearer {token}

Request:
{
  "message": "GitHub에서 최근 이슈 가져와줘",
  "conversation_history": []
}

Response:
{
  "success": true,
  "response": "최근 이슈 3개를 가져왔습니다...",
  "tool_calls": [
    {
      "name": "fetch_github_issues",
      "arguments": {"repo": "example/repo"},
      "result": {...}
    }
  ],
  "tokens_used": 450
}
```

## 환경 변수 설정

`.env` 파일에 추가 필요:

```bash
# OpenAI API 사용 시
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
LLM_BASE_URL=https://api.openai.com/v1

# DeepSeek 사용 시
OPENAI_API_KEY=sk-...
OPENAI_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com

# 사내 LLM 사용 시
OPENAI_API_KEY=your-internal-key
OPENAI_MODEL=your-model-name
LLM_BASE_URL=https://your-internal-api.company.com/v1
```

## 설치 및 실행

### 1. 의존성 설치
```bash
cd backend
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 수정하여 API 키 입력
```

### 3. 서버 실행
```bash
python main.py
```

### 4. 프론트엔드 실행
```bash
cd frontend
npm run dev
```

## 사용 방법

1. MCP 서버 상세 페이지 접속 (`/mcp/{id}`)
2. 페이지 하단 "🎮 Try it out!" 섹션 확인
3. 로그인 (필수)
4. 질문 입력 후 Send 버튼 클릭
5. AI가 MCP Tools를 사용하여 답변 생성

## 보안 및 제한

### 인증
- JWT 토큰 기반 인증
- 로그인하지 않은 사용자는 접근 불가

### Rate Limiting
- 사용자별 일일 10회 제한
- MCP 서버별로 독립적으로 카운트
- KST 자정(00:00)에 자동 리셋
- 실패한 요청은 카운트하지 않음

### API 키 보안
- 서버 측에서만 API 키 관리
- 프론트엔드에 노출되지 않음
- 환경 변수로 관리

## 비용 관리

### OpenAI GPT-4 Turbo 기준
- 평균 쿼리당 약 $0.04
- 100명 × 10회/일 = $40/일 = **$1,200/월**

### 비용 절감 방안
- GPT-3.5-turbo 사용 (70% 절감)
- DeepSeek 사용 (더 저렴)
- 사내 LLM 사용 (무료)
- 일일 쿼리 제한 조정

## 향후 개선 사항

- [ ] WebSocket 실시간 스트리밍 응답
- [ ] 대화 히스토리 DB 저장
- [ ] Playground 공유 기능
- [ ] 다양한 LLM 모델 선택 UI
- [ ] 예제 프롬프트 제공
- [ ] 사용량 통계 대시보드
- [ ] 토큰 사용량 추적 및 분석

## 테스트

### 단위 테스트
```bash
pytest backend/tests/test_playground_service.py
```

### 통합 테스트
1. MCP 서버 등록 (예: GitHub MCP)
2. Playground에서 질문: "최근 커밋 가져와줘"
3. Tool 호출 확인
4. 응답 확인

## 문서

- **상세 설정 가이드**: [PLAYGROUND_SETUP.md](./PLAYGROUND_SETUP.md)
- **프로젝트 문서**: [CLAUDE.md](./CLAUDE.md) - Playground 섹션 추가됨

## 스크린샷

### Playground UI
```
┌─────────────────────────────────────────┐
│  🎮 Playground (Beta)                   │
│  Usage: 3/10 queries today              │
├─────────────────────────────────────────┤
│  User: GitHub에서 이슈 가져와줘          │
│  AI: fetch_github_issues 호출 중...     │
│  Tool: ✓ fetch_github_issues            │
│  AI: 최근 이슈 5개를 가져왔습니다...     │
├─────────────────────────────────────────┤
│  [Type your message...]      [Send] 📤  │
└─────────────────────────────────────────┘
```

## 관련 이슈

- Closes #XXX (MCP 서버 테스트 기능 요청)

## 체크리스트

- [x] 기능 구현 완료
- [x] 백엔드 API 테스트
- [x] 프론트엔드 UI 테스트
- [x] 문서 작성 (PLAYGROUND_SETUP.md)
- [x] Rate limiting 동작 확인
- [x] 환경 변수 설정 가이드 작성
- [x] 보안 검토 (API 키 노출 방지)
- [x] 에러 핸들링
- [x] 로깅 추가

## 리뷰어께

- MCP tool 호출 및 결과 파싱 로직 검토 부탁드립니다
- Rate limiting 정책 (10회/일) 적절한지 의견 주세요
- LLM API 비용 관리 방안 제안 부탁드립니다

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
