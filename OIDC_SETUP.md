# OpenID Connect (OIDC) 설정 가이드

이 문서는 Smithery 프로젝트에 Azure Active Directory (AD) SSO를 설정하는 방법을 설명합니다.

## 1. Azure AD 앱 등록

### 1.1 Azure Portal에서 앱 등록
1. [Azure Portal](https://portal.azure.com)에 로그인
2. "Azure Active Directory" → "앱 등록" → "새 등록"
3. 앱 이름: `Smithery MCP Marketplace`
4. 지원되는 계정 유형: `이 조직 디렉터리의 계정만`
5. 리디렉션 URI: `http://localhost:3000/auth/callback` (개발용)

### 1.2 클라이언트 ID와 시크릿 생성
1. 앱 등록 후 "개요"에서 `애플리케이션(클라이언트) ID` 복사
2. "인증서 및 비밀번호" → "새 클라이언트 비밀번호" → 비밀번호 생성 후 복사

### 1.3 API 권한 설정
1. "API 권한" → "권한 추가" → "Microsoft Graph"
2. 위임된 권한 선택:
   - `User.Read` (사용자 프로필 읽기)
   - `email` (이메일 주소 읽기)
   - `profile` (프로필 읽기)

## 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# OpenID Connect 설정
OIDC_CLIENT_ID=your_client_id_here
OIDC_CLIENT_SECRET=your_client_secret_here
OIDC_DISCOVERY_URL=https://login.microsoftonline.com/your-tenant-id/v2.0/.well-known/openid_configuration
OIDC_REDIRECT_URI=http://localhost:3000/auth/callback
OIDC_SCOPE=openid profile email

# 기존 JWT 설정
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 데이터베이스 설정
DATABASE_URL=postgresql://user:password@localhost/dbname
```

### 2.1 테넌트 ID 찾기
- Azure Portal → "Azure Active Directory" → "개요" → "테넌트 ID"

## 3. 데이터베이스 마이그레이션

새로운 OIDC 필드가 추가되었으므로 데이터베이스를 마이그레이션해야 합니다:

```sql
-- users 테이블에 OIDC 필드 추가
ALTER TABLE users 
ADD COLUMN display_name VARCHAR(255),
ADD COLUMN oidc_sub VARCHAR(255) UNIQUE;

-- password_hash를 nullable로 변경
ALTER TABLE users 
ALTER COLUMN password_hash DROP NOT NULL;
```

## 4. 테스트

### 4.1 백엔드 실행
```bash
cd backend
python -m uvicorn main:app --reload
```

### 4.2 프론트엔드 실행
```bash
cd frontend
npm run dev
```

### 4.3 SSO 로그인 테스트
1. `http://localhost:3000/login` 접속
2. "회사 계정으로 로그인 (SSO)" 버튼 클릭
3. Azure AD 로그인 페이지로 리다이렉트
4. 회사 계정으로 로그인
5. 성공 시 메인 페이지로 리다이렉트

## 5. 프로덕션 배포 시 고려사항

### 5.1 HTTPS 설정
- 프로덕션에서는 반드시 HTTPS 사용
- 리디렉션 URI를 HTTPS로 변경

### 5.2 도메인 설정
- 실제 도메인에 맞게 리디렉션 URI 수정
- CORS 설정 업데이트

### 5.3 보안 강화
- 환경 변수는 안전한 방법으로 관리
- 클라이언트 시크릿 정기적 갱신

## 6. 문제 해결

### 6.1 일반적인 오류
- **AADSTS50011**: 리디렉션 URI 불일치 → Azure AD 앱 등록에서 URI 확인
- **AADSTS70001**: 클라이언트 ID 오류 → 환경 변수 확인
- **AADSTS70002**: 클라이언트 시크릿 오류 → 시크릿 재생성

### 6.2 로그 확인
- 백엔드 로그에서 OIDC 관련 오류 메시지 확인
- 브라우저 개발자 도구에서 네트워크 요청 확인

## 7. 추가 기능

### 7.1 로그아웃
- `/api/v1/oidc/logout` 엔드포인트로 Azure AD 로그아웃

### 7.2 사용자 정보 동기화
- Azure AD에서 사용자 정보 변경 시 자동 동기화
- 그룹 멤버십 기반 권한 관리

## 8. 지원

문제가 발생하면 다음을 확인하세요:
1. 환경 변수 설정
2. Azure AD 앱 등록 설정
3. 데이터베이스 스키마
4. 네트워크 연결 및 방화벽 설정 