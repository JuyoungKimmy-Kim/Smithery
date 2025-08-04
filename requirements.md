## 요구 사항

- 사용자
1. 사용자는 일반 사용자와 관리자로 구분된다.
2. 모든 사용자는 MCP List를 보고, 검색하고, 상세 정보를 열람할 수 있다.
3. 일반 사용자는 MCP Server를 등록할 수 있지만 관리자의 승인이 있어야지만 MCP List에 노출이 된다.
4. 자신이 등록한 MCP Server List를 관리할 수 있다.
5. 사용자의 Avatar를 클릭하면, 해당 사용자가 등록한 MCP Server List를 확인할 수 있다.
6. 등록된 MCP Server의 삭제, 비공개 처리는 관리자만이 가능하다.
7. 일반 사용자는 MCP Server를 즐겨 찾기할 수 있다.

- MCP Server
1. 관리자의 승인이 있는 모든 MCP Server는 메인 화면에 노출된다.
2. MCP 서버의 상세 정보에는 사용 가능한 Tools, Resource, Server Config 등의 정보를 나타난다.
3. Tools 항목에는 Tools의 name, description, parameter, 각 parameter에 대한 설명 등이 나타난다.

- Search 기능
1. 키워드를 통해 MCP Server를 검색할 수 있다.
2. MCP Server의 이름, 설명, tag, category 에서 해당 키워드와 유사하거나 동일한 키워드를 포함하는 MCP List를 표시한다.

## 작업 단계계

### 1단계: 데이터베이스 설계 및 구현 ✅ 우선순위 1
현재 SQLite를 사용하고 있지만, 요구사항에 맞는 완전한 스키마가 필요합니다:
필요한 테이블:
users - 사용자 관리 (일반 사용자/관리자 구분)
mcp_servers - MCP 서버 정보 (승인 상태 포함)
mcp_tools - MCP 서버의 도구들
mcp_resources - MCP 서버의 리소스들
user_favorites - 사용자 즐겨찾기
user_mcp_servers - 사용자가 등록한 MCP 서버 관계

### 2단계: 사용자 인증 시스템 구현 ✅ 우선순위 2
필요한 기능:
JWT 기반 인증
사용자 등록/로그인
관리자 권한 관리
사용자 프로필 관리

### 3단계: 백엔드 API 확장 ✅ 우선순위 3
현재 부족한 API:
사용자 관리 API (회원가입, 로그인, 프로필)
MCP 서버 승인/거부 API (관리자용)
즐겨찾기 API
검색 API (키워드 기반)
사용자별 MCP 서버 관리 API

### 4단계: 프론트엔드 구현 ✅ 우선순위 4
필요한 페이지:
메인 페이지 (승인된 MCP 서버 목록)
MCP 서버 상세 페이지
사용자 프로필 페이지
관리자 대시보드
검색 페이지
로그인/회원가입 페이지

### 5단계: 검색 기능 구현 ✅ 우선순위 5
검색 대상:
MCP 서버 이름
설명
태그
카테고리

### 6단계: 관리자 기능 구현 ✅ 우선순위 6
관리자 전용 기능:
MCP 서버 승인/거부
MCP 서버 삭제
비공개 처리
사용자 관리