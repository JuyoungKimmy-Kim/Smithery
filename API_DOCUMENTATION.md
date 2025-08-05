# DS Smithery API 문서

## 🔐 인증 API

### 사용자 등록
```http
POST /api/auth/register
```

**요청 본문:**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "testpassword123"
}
```

**응답:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user"
  }
}
```

### 사용자 로그인
```http
POST /api/auth/login
```

**요청 본문:**
```json
{
  "username": "testuser",
  "password": "testpassword123"
}
```

**응답:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user"
  }
}
```

### 현재 사용자 정보 조회
```http
GET /api/auth/me
Authorization: Bearer {token}
```

**응답:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "role": "user",
  "avatar_url": null,
  "created_at": "2024-01-01T00:00:00"
}
```

## 🔧 MCP 서버 API

### 승인된 MCP 서버 목록 조회 (공개)
```http
GET /api/mcps/approved
```

**응답:**
```json
[
  {
    "id": 1,
    "github_link": "https://github.com/example/mcp-server",
    "name": "Example MCP Server",
    "description": "An example MCP server",
    "transport": "stdio",
    "category": "example",
    "tags": ["example", "test"],
    "status": "approved",
    "tools": [...],
    "resources": [...],
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 승인 대기 중인 MCP 서버 목록 조회 (관리자용)
```http
GET /api/mcps/pending
Authorization: Bearer {admin_token}
```

### 내가 등록한 MCP 서버 목록 조회
```http
GET /api/mcps/my
Authorization: Bearer {token}
```

### 특정 MCP 서버 조회
```http
GET /api/mcps/{mcp_id}
```

### 새로운 MCP 서버 생성
```http
POST /api/mcps
Authorization: Bearer {token}
```

**요청 본문:**
```json
{
  "github_link": "https://github.com/example/mcp-server",
  "name": "Example MCP Server",
  "description": "An example MCP server",
  "transport": "stdio",
  "category": "example",
  "tags": ["example", "test"]
}
```

**응답:**
```json
{
  "message": "MCP server created successfully",
  "mcp_id": 1
}
```

### MCP 서버 승인 (관리자용)
```http
POST /api/mcps/{mcp_id}/approve
Authorization: Bearer {admin_token}
```

### MCP 서버 거부 (관리자용)
```http
POST /api/mcps/{mcp_id}/reject
Authorization: Bearer {admin_token}
```

### MCP 서버 삭제 (관리자용)
```http
DELETE /api/mcps/{mcp_id}
Authorization: Bearer {admin_token}
```

## ⭐ 즐겨찾기 API

### 즐겨찾기 추가
```http
POST /api/favorites/{mcp_id}
Authorization: Bearer {token}
```

### 즐겨찾기 제거
```http
DELETE /api/favorites/{mcp_id}
Authorization: Bearer {token}
```

### 즐겨찾기 목록 조회
```http
GET /api/favorites
Authorization: Bearer {token}
```

## 🔍 검색 API

### 키워드 검색
```http
GET /api/search?q={keyword}
```

**응답:**
```json
[
  {
    "id": 1,
    "name": "Python MCP Server",
    "description": "A Python MCP server",
    "category": "python",
    "tags": ["python", "mcp"]
  }
]
```

## 👑 관리자 API

### 모든 사용자 목록 조회 (관리자용)
```http
GET /api/admin/users
Authorization: Bearer {admin_token}
```

## 📋 상태 코드

- `200` - 성공
- `201` - 생성 성공
- `400` - 잘못된 요청
- `401` - 인증 실패
- `403` - 권한 부족
- `404` - 리소스 없음
- `500` - 서버 오류

## 🔑 인증

대부분의 API는 JWT 토큰을 필요로 합니다. 토큰은 다음과 같이 전달하세요:

```
Authorization: Bearer {your_jwt_token}
```

## 📝 사용 예시

### 1. 사용자 등록 및 로그인
```bash
# 사용자 등록
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# 로그인
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

### 2. MCP 서버 생성
```bash
curl -X POST "http://localhost:8000/api/mcps" \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "github_link": "https://github.com/example/mcp-server",
    "name": "Example Server",
    "description": "An example MCP server",
    "transport": "stdio",
    "category": "example",
    "tags": ["example"]
  }'
```

### 3. 검색
```bash
curl "http://localhost:8000/api/search?q=python"
```

## 🚀 서버 실행

```bash
# 환경 변수 설정
cp env.example .env
# .env 파일을 편집하여 필요한 설정을 추가

# 서버 실행
python main.py
```

## 📚 API 문서 확인

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 