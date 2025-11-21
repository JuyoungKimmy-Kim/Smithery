# MCP Auth Token Storage - Database Setup (Optional)

이 가이드는 **옵션 2: DB에 토큰 저장** 방식을 사용하려는 경우에만 필요합니다.

## 현재 구현 vs DB 저장 방식

### 현재 구현 (권장) ✅
- 토큰을 메모리(React state)에만 저장
- 사용자가 매번 토큰 입력 필요
- 보안상 더 안전
- **DB 변경 불필요**

### DB 저장 방식 (이 가이드)
- 토큰을 암호화하여 DB에 저장
- 사용자가 한 번만 토큰 입력
- 편리하지만 추가 보안 조치 필요

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd /home/kimmy/code/Smithery
pip install -r requirements.txt
```

이 명령어는 `cryptography` 패키지를 설치합니다 (토큰 암호화에 필요).

### 2. Set Environment Variable

**IMPORTANT**: 프로덕션 환경에서는 반드시 강력한 암호화 키를 설정하세요.

```bash
# .env 파일 또는 환경변수에 추가
export TOKEN_ENCRYPTION_SECRET="your-very-strong-secret-key-here-min-32-chars"
```

**개발 환경**에서는 설정하지 않으면 기본값이 사용됩니다 (경고 로그 출력).

### 3. Run Migration

데이터베이스에 새 테이블을 생성합니다:

```bash
cd /home/kimmy/code/Smithery
python backend/run_migration.py
```

예상 출력:
```
INFO:__main__:Running migration: add_mcp_auth_tokens_table.sql
INFO:__main__:✅ Migration completed successfully!
INFO:__main__:Created table: mcp_auth_tokens
```

### 4. Verify Table Creation

```bash
sqlite3 mcp_market.db
```

```sql
-- 테이블 확인
.tables

-- 스키마 확인
.schema mcp_auth_tokens

-- 종료
.quit
```

---

## Database Schema

```sql
CREATE TABLE mcp_auth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mcp_server_id INTEGER NOT NULL,
    token_encrypted TEXT NOT NULL,  -- 암호화된 토큰
    token_hint TEXT,                -- 마지막 4글자 (예: "...a1b2")
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (mcp_server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE,
    UNIQUE(user_id, mcp_server_id)
);
```

**특징:**
- 사용자당 MCP 서버당 하나의 토큰만 저장
- 토큰은 Fernet (대칭키 암호화)로 암호화됨
- 사용자나 서버 삭제 시 자동으로 토큰도 삭제 (CASCADE)

---

## API Usage Examples

### Save Token (새 API 엔드포인트 필요)

현재 구현에는 토큰 저장 API가 없습니다. 추가하려면:

```python
# backend/api/endpoints/auth_tokens.py (새 파일)
from fastapi import APIRouter, Depends
from backend.database.dao.mcp_auth_token_dao import MCPAuthTokenDAO
from backend.api.auth import get_current_user

router = APIRouter()

@router.post("/mcp-servers/{server_id}/auth-token")
async def save_auth_token(
    server_id: int,
    token: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dao = MCPAuthTokenDAO(db)
    dao.save_token(current_user.id, server_id, token)
    return {"success": True, "message": "Token saved"}

@router.get("/mcp-servers/{server_id}/auth-token")
async def get_auth_token(
    server_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dao = MCPAuthTokenDAO(db)
    token = dao.get_token(current_user.id, server_id)
    if token:
        hint = TokenEncryption.get_token_hint(token)
        return {"has_token": True, "hint": hint}
    return {"has_token": False}
```

### Modify Playground Endpoint

`backend/api/endpoints/playground.py` 수정:

```python
# 토큰이 요청에 없으면 DB에서 가져오기
if not chat_request.mcp_auth_token:
    token_dao = MCPAuthTokenDAO(db)
    saved_token = token_dao.get_token(user_id, server_id)
    if saved_token:
        logger.info(f"Using saved auth token for user {user_id}, server {server_id}")
        user_token = saved_token
    else:
        user_token = None
else:
    user_token = chat_request.mcp_auth_token
```

---

## Security Considerations

### ✅ Implemented Security Measures

1. **Encryption**: Tokens encrypted with Fernet (AES-128-CBC)
2. **Key Derivation**: PBKDF2 with 100,000 iterations
3. **Cascade Delete**: Tokens deleted when user/server is deleted
4. **Token Hints**: Only last 4 characters visible

### ⚠️ Additional Recommendations

1. **Use Strong Secret**:
   ```bash
   # Generate strong secret
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Rotate Encryption Key**:
   - Implement key rotation policy
   - Re-encrypt tokens periodically

3. **Audit Logging**:
   - Log token access and modifications
   - Monitor for suspicious activity

4. **HTTPS Only**:
   - Never transmit tokens over HTTP
   - Use HTTPS in production

5. **Token Expiration**:
   - Consider implementing token expiration
   - Prompt users to refresh expired tokens

---

## Rollback (테이블 삭제)

테이블을 삭제하려면:

```sql
DROP TABLE IF EXISTS mcp_auth_tokens;
DROP INDEX IF EXISTS idx_mcp_auth_tokens_user_server;
DROP INDEX IF EXISTS idx_mcp_auth_tokens_user;
DROP TRIGGER IF EXISTS update_mcp_auth_tokens_timestamp;
```

또는:

```bash
sqlite3 mcp_market.db "DROP TABLE IF EXISTS mcp_auth_tokens;"
```

---

## Files Created

이 기능을 위해 생성된 파일들:

1. `backend/database/migrations/add_mcp_auth_tokens_table.sql` - SQL 마이그레이션
2. `backend/database/model/mcp_auth_token.py` - SQLAlchemy 모델
3. `backend/database/dao/mcp_auth_token_dao.py` - Data Access Object
4. `backend/utils/token_encryption.py` - 암호화 유틸리티
5. `backend/run_migration.py` - 마이그레이션 실행 스크립트
6. `requirements.txt` - `cryptography` 추가
7. `DB_TOKEN_STORAGE_SETUP.md` - 이 문서

---

## Summary

**현재 구현 (옵션 1)**: 토큰을 DB에 저장하지 않음 → DB 변경 불필요 ✅

**옵션 2 (이 가이드)**: 토큰을 DB에 저장 → 위 단계 실행 필요

대부분의 경우 **옵션 1 (현재 구현)**을 권장합니다. 보안상 더 안전하고 간단합니다.
