# DS Smithery

데이터 사이언스 프로젝트를 위한 풀스택 웹 애플리케이션입니다.

## 프로젝트 구조

```
ds-smithery/
├── backend/          # 백엔드 로직 (DAO, 모델, 서비스)
├── frontend/         # Next.js + Tailwind CSS 프론트엔드
├── tools/            # 개발 도구 및 스크립트
├── test/             # 테스트 파일들
├── main.py           # FastAPI 백엔드 서버
└── requirements.txt  # Python 의존성
```

## 아키텍처 설명

### 백엔드 (main.py + backend/)
- **FastAPI 서버**: 포트 8080에서 실행
- **DAO (Data Access Object)**: 데이터베이스 접근 로직
- **모델**: 데이터 구조 정의 (Pydantic)
- **API 엔드포인트**: RESTful API 제공

### 프론트엔드 (frontend/)
- **Next.js 서버**: 포트 3000에서 실행
- **API Routes**: 백엔드 API를 호출하는 프록시
- **UI 컴포넌트**: React + Tailwind CSS
- **타입 정의**: 백엔드 모델을 TypeScript로 변환

## 서버 실행 방법

### 1. 백엔드 서버 실행

1. **가상환경 활성화**
   ```bash
   source .venv/bin/activate
   ```

2. **Python 의존성 설치** (처음 실행 시)
   ```bash
   pip install -r requirements.txt
   ```

3. **백엔드 서버 실행**
   ```bash
   python main.py
   ```

4. **백엔드 API 확인**
   - **API 문서**: http://localhost:8080/docs
   - **API 엔드포인트**: http://localhost:8080/api/mcps

### 2. 프론트엔드 서버 실행

1. **프론트엔드 디렉토리로 이동**
   ```bash
   cd frontend
   ```

2. **Node.js 버전 설정**
   ```bash
   export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
   nvm use 18
   ```

3. **의존성 설치** (처음 실행 시)
   ```bash
   npm install
   ```

4. **개발 서버 실행**
   ```bash
   npm run dev
   ```

5. **프론트엔드 접속**
   - **메인 페이지**: http://localhost:3000
   - **API 프록시**: http://localhost:3000/api/mcps

## 현재 실행 상태

✅ **백엔드 서버**: http://localhost:8080 (FastAPI)
✅ **프론트엔드 서버**: http://localhost:3000 (Next.js)

## API 엔드포인트

### 백엔드 API (포트 8080)
- **GET /api/mcps**: MCP 서버 목록 조회
- **POST /api/mcps**: 새로운 MCP 서버 생성
- **GET /api/mcps/{id}**: 특정 MCP 서버 조회
- **PUT /api/mcps/{id}**: MCP 서버 정보 수정
- **DELETE /api/mcps/{id}**: MCP 서버 삭제
- **GET /api/posts**: 블로그 포스트 목록 (UI용)

### 프론트엔드 API 프록시 (포트 3000)
- **GET /api/mcps**: 백엔드 API 호출
- **POST /api/mcps**: 백엔드 API 호출
- **GET /api/mcps/{id}**: 백엔드 API 호출
- **PUT /api/mcps/{id}**: 백엔드 API 호출
- **DELETE /api/mcps/{id}**: 백엔드 API 호출
- **GET /api/posts**: 백엔드 API 호출

## 기술 스택

### 백엔드
- **Framework**: FastAPI
- **Language**: Python
- **Database**: SQLite
- **Architecture**: DAO 패턴
- **Models**: Pydantic BaseModel
- **Port**: 8080

### 프론트엔드
- **Framework**: Next.js 13.4.0
- **UI Library**: React 18
- **Styling**: Tailwind CSS 3
- **Icons**: Heroicons React
- **Language**: TypeScript
- **Port**: 3000

## 개발 환경

- **OS**: Linux (WSL2)
- **Shell**: Bash
- **Node.js**: NVM을 통한 관리
- **Python**: 가상환경 사용
- **Database**: SQLite

## 사용 가능한 스크립트

### 백엔드
- `python main.py` - FastAPI 서버 실행

### 프론트엔드
- `npm run dev` - 개발 서버 실행 (핫 리로드 포함)
- `npm run build` - 프로덕션 빌드
- `npm run start` - 프로덕션 서버 실행
- `npm run lint` - ESLint로 코드 검사

## 문제 해결

### 포트 충돌
포트가 이미 사용 중인 경우:
```bash
# 실행 중인 서버 확인
ss -tlnp | grep :8080
ss -tlnp | grep :3000

# 서버 종료
pkill -f "python main.py"
pkill -f "npm run dev"
```

### 의존성 문제
Node.js 모듈에 문제가 있는 경우:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 캐시 문제
Next.js 캐시 관련 문제:
```bash
cd frontend
rm -rf .next/cache
npm run dev
```

### 데이터베이스 문제
SQLite 데이터베이스 파일이 없는 경우:
```bash
# 데이터베이스 파일 확인
ls -la mcp_market.db

# 백엔드에서 테이블 생성
cd backend
python -c "from database.dao.mcp_server_dao import MCPServerDAO; dao = MCPServerDAO('../mcp_market.db'); dao.connect(); dao.create_table(); dao.close()"
```

## 데이터베이스

### 개발용 더미 데이터 생성

개발 및 테스트를 위해 더미 데이터를 생성할 수 있습니다:

```bash
# 가상환경 활성화
source .venv/bin/activate

# 더미 데이터 삽입 스크립트 실행
PYTHONPATH=. python tools/test_insert_dummy.py
```

이 스크립트는 다음과 같은 더미 데이터를 생성합니다:
- 5개의 MCP 서버 정보
- 각 서버마다 2-3개의 도구(tools)
- 다양한 카테고리와 태그 정보

### 데이터베이스 스키마
```sql
CREATE TABLE mcp_server (
    id TEXT PRIMARY KEY,
    github_link TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    transport TEXT NOT NULL,
    category TEXT,
    tags TEXT,
    status TEXT,
    tools TEXT,
    resources TEXT,
    created_at TEXT,
    updated_at TEXT
);
```

## 접속 테스트

### 백엔드 API 테스트
```bash
# MCP 서버 목록 조회
curl http://localhost:8080/api/mcps

# API 문서 확인
curl http://localhost:8080/docs
```

### 프론트엔드 테스트
```bash
# 메인 페이지 접속
curl http://localhost:3000

# 프론트엔드 API 프록시 테스트
curl http://localhost:3000/api/mcps
``` 