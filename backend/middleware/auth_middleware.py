from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.service.auth_service import AuthService
from backend.database.dao.user_dao import UserDAO
from backend.database.model.user import User
import os
from dotenv import load_dotenv

load_dotenv()

# JWT 시크릿 키
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")

# HTTP Bearer 스키마
security = HTTPBearer()

# 인증 서비스 인스턴스
def get_auth_service():
    user_dao = UserDAO("mcp_market.db")
    user_dao.connect()
    user_dao.create_table()
    return AuthService(JWT_SECRET_KEY, user_dao)

# 현재 사용자 의존성
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """현재 인증된 사용자 반환"""
    token = credentials.credentials
    user = auth_service.get_current_user(token)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# 관리자 권한 의존성
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """현재 인증된 관리자 사용자 반환"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user

# 선택적 인증 (로그인하지 않아도 접근 가능)
async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """선택적 현재 사용자 반환 (인증되지 않아도 None 반환)"""
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(token)
        return user
    except:
        return None 