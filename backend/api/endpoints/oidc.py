from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import timedelta

from backend.database import get_db
from backend.service.oidc_service import OIDCService
from backend.service import UserService
from backend.api.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.api.schemas import UserResponse
from backend.config import settings

router = APIRouter(prefix="/oidc", tags=["OpenID Connect"])

oidc_service = OIDCService()

@router.get("/login")
async def oidc_login(request: Request):
    """OpenID Connect 로그인을 시작합니다."""
    try:
        # Azure AD 로그인 페이지로 리다이렉트
        login_url = oidc_service.get_login_url()
        return RedirectResponse(url=login_url)
    except Exception as e:
        logging.error(f"OIDC login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OIDC login"
        )

@router.get("/callback")
async def oidc_callback(request: Request, db: Session = Depends(get_db)):
    """OpenID Connect 콜백을 처리합니다."""
    try:
        # OIDC 콜백 처리
        result = await oidc_service.handle_callback(request)
        user_info = result['user_info']
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from OIDC"
            )
        
        # 사용자 이메일 또는 username 추출
        email = user_info.get('email') or user_info.get('preferred_username')
        name = user_info.get('name', '')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in OIDC user info"
            )
        
        # 기존 사용자 확인 또는 생성
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        
        if not user:
            # 새 사용자 생성 (OIDC 사용자)
            user = user_service.create_oidc_user(
                email=email,
                name=name,
                oidc_sub=user_info.get('sub')
            )
        
        # JWT 토큰 생성 (기존 시스템과 호환)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        # 프론트엔드로 리다이렉트 (토큰과 함께)
        frontend_url = f"http://localhost:3000/auth/success?token={access_token}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logging.error(f"OIDC callback error: {e}")
        # 에러 발생 시 프론트엔드 에러 페이지로 리다이렉트
        error_url = f"http://localhost:3000/auth/error?message={str(e)}"
        return RedirectResponse(url=error_url)

@router.get("/logout")
async def oidc_logout():
    """OpenID Connect 로그아웃을 수행합니다."""
    # Azure AD 로그아웃 URL로 리다이렉트
    logout_url = f"{settings.OIDC_DISCOVERY_URL.replace('/.well-known/openid_configuration', '')}/oauth2/v2.0/logout"
    return RedirectResponse(url=logout_url) 