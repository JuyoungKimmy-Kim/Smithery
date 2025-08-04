# DS Smithery 개발 계획서

## ✅ 완료된 작업 (1단계: 데이터베이스 설계 및 구현)

### 1. 데이터베이스 스키마 설계 ✅
- **파일**: `database_schema.sql`
- **내용**: 
  - 사용자 테이블 (`users`)
  - MCP 서버 테이블 (`mcp_servers`)
  - MCP 도구 테이블 (`mcp_tools`)
  - MCP 리소스 테이블 (`mcp_resources`)
  - 사용자 즐겨찾기 테이블 (`user_favorites`)
  - 인덱스 및 제약조건

### 2. 데이터 모델 업데이트 ✅
- **파일**: `backend/database/model/user.py`
- **내용**: 사용자 관리 모델 (User, UserCreate, UserLogin, UserResponse)

- **파일**: `backend/database/model/mcp_server.py`
- **내용**: MCP 서버 모델 업데이트 (승인 상태, 사용자 관계 등)

### 3. DAO 구현 ✅
- **파일**: `backend/database/dao/user_dao.py`
- **내용**: 사용자 CRUD 작업

- **파일**: `backend/database/dao/mcp_server_dao.py`
- **내용**: MCP 서버 CRUD 작업 (승인, 검색, 즐겨찾기 등)

### 4. 인증 서비스 구현 ✅
- **파일**: `backend/service/auth_service.py`
- **내용**: JWT 기반 인증, 비밀번호 해시화, 사용자 등록/로그인

### 5. 데이터베이스 초기화 ✅
- **파일**: `init_database.py`
- **내용**: 스키마 생성 및 기본 관리자 계정 설정

### 6. 의존성 업데이트 ✅
- **파일**: `requirements.txt`
- **추가**: PyJWT, bcrypt, email-validator, python-dotenv

---

## 🔄 다음 단계 작업

### 2단계: 백엔드 API 확장 (우선순위 2)

#### 필요한 API 엔드포인트:
1. **사용자 관리 API**
   - `POST /api/auth/register` - 사용자 등록
   - `POST /api/auth/login` - 사용자 로그인
   - `GET /api/auth/me` - 현재 사용자 정보
   - `PUT /api/auth/profile` - 프로필 업데이트

2. **MCP 서버 관리 API**
   - `GET /api/mcps/approved` - 승인된 MCP 서버 목록
   - `GET /api/mcps/pending` - 승인 대기 중인 MCP 서버 목록 (관리자용)
   - `POST /api/mcps/approve/{id}` - MCP 서버 승인 (관리자용)
   - `POST /api/mcps/reject/{id}` - MCP 서버 거부 (관리자용)
   - `DELETE /api/mcps/{id}` - MCP 서버 삭제 (관리자용)

3. **즐겨찾기 API**
   - `POST /api/favorites/{mcp_id}` - 즐겨찾기 추가
   - `DELETE /api/favorites/{mcp_id}` - 즐겨찾기 제거
   - `GET /api/favorites` - 사용자 즐겨찾기 목록

4. **검색 API**
   - `GET /api/search?q={keyword}` - 키워드 검색

### 3단계: 프론트엔드 구현 (우선순위 3)

#### 필요한 페이지:
1. **인증 페이지**
   - 로그인 페이지
   - 회원가입 페이지

2. **메인 페이지**
   - 승인된 MCP 서버 목록
   - 검색 기능
   - 카테고리 필터

3. **MCP 서버 상세 페이지**
   - 서버 정보
   - 도구 및 리소스 목록
   - 즐겨찾기 버튼

4. **사용자 프로필 페이지**
   - 사용자 정보
   - 등록한 MCP 서버 목록
   - 즐겨찾기 목록

5. **관리자 대시보드**
   - 승인 대기 중인 MCP 서버 목록
   - 승인/거부 기능
   - 사용자 관리

### 4단계: 검색 기능 구현 (우선순위 4)

#### 검색 대상:
- MCP 서버 이름
- 설명
- 태그
- 카테고리

#### 검색 기능:
- 실시간 검색
- 필터링 (카테고리, 태그)
- 정렬 (최신순, 인기순)

### 5단계: 관리자 기능 구현 (우선순위 5)

#### 관리자 전용 기능:
- MCP 서버 승인/거부
- MCP 서버 삭제
- 비공개 처리
- 사용자 관리

---

## 🚀 즉시 시작할 작업

### 다음 단계: 백엔드 API 확장

1. **main.py 업데이트**
   - 인증 미들웨어 추가
   - 새로운 API 엔드포인트 추가
   - 권한 검증 로직 추가

2. **환경 변수 설정**
   - JWT 시크릿 키
   - 데이터베이스 설정
   - GitHub 토큰

3. **API 테스트**
   - 사용자 등록/로그인 테스트
   - MCP 서버 승인 프로세스 테스트
   - 검색 기능 테스트

---

## 📋 체크리스트

### 데이터베이스 설계 ✅
- [x] 스키마 설계
- [x] 모델 정의
- [x] DAO 구현
- [x] 데이터베이스 초기화

### 인증 시스템 ✅
- [x] JWT 토큰 구현
- [x] 비밀번호 해시화
- [x] 사용자 등록/로그인
- [x] 권한 관리

### 백엔드 API (진행 예정)
- [ ] 인증 API
- [ ] MCP 서버 관리 API
- [ ] 즐겨찾기 API
- [ ] 검색 API

### 프론트엔드 (진행 예정)
- [ ] 인증 페이지
- [ ] 메인 페이지
- [ ] 상세 페이지
- [ ] 관리자 대시보드

### 테스트 (진행 예정)
- [ ] 단위 테스트
- [ ] 통합 테스트
- [ ] API 테스트 