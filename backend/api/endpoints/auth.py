from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
import logging
import requests
import os

from backend.database import get_db
from backend.service import UserService
from backend.api.schemas import UserCreate, UserLogin, UserResponse, ADLoginRequest
from backend.api.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

# AD 설정
AD_CLIENT_ID = os.getenv("AD_CLIENT_ID", "your-ad-client-id")
AD_CLIENT_SECRET = os.getenv("AD_CLIENT_SECRET", "your-ad-client-secret")
AD_TOKEN_ENDPOINT = os.getenv("AD_TOKEN_ENDPOINT", "https://adfs.company.com/adfs/oauth2/token")

@router.post("/ad-login")
async def ad_login(request: Request, db: Session = Depends(get_db)):
    """AD 로그인을 처리합니다."""
    try:
        # form 데이터 파싱
        form_data = await request.form()
        code = form_data.get("code")
        state = form_data.get("state")
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required"
            )
        
        print(f"AD login received - code: {code[:10]}..., state: {state}")
        
        # ADFS 토큰 엔드포인트에 토큰 교환 요청
        token_response = requests.post(
            AD_TOKEN_ENDPOINT,
            data={
                "client_id": AD_CLIENT_ID,
                "client_secret": AD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "https://your-backend.com/api/v1/auth/ad-login"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if not token_response.ok:
            print(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange token with ADFS"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        id_token = token_data.get("id_token")
        
        print(f"Token exchange successful - access_token: {access_token[:20]}...")
        
        # TODO: id_token 검증 (JWT 서명, 만료시간 등)
        # 여기서는 간단하게 처리
        
        # 사용자 정보 추출 (실제로는 id_token에서 추출)
        # 더미 데이터로 대체
        import secrets
        username = f"ad_user_{secrets.token_urlsafe(8)}"
        email = f"{username}@company.com"
        
        # 사용자 조회 또는 생성
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        
        if not user:
            print(f"Creating new AD user: {username}")
            user = user_service.create_user(
                username=username,
                email=email,
                password="ad_user_temp_password_123"
            )
        else:
            print(f"Existing AD user found: {user.username}")
        
        # JWT 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
        
    except Exception as e:
        print(f"AD login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AD 로그인 처리 실패: {str(e)}"
        )

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """새 사용자를 등록합니다."""
    user_service = UserService(db)
    
    try:
        user = user_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """사용자 로그인을 수행합니다."""
    print(f"Login attempt for username: {user_data.username}")  # 디버깅 로그
    
    user_service = UserService(db)
    
    # 사용자 조회 시도
    user = user_service.get_user_by_username(user_data.username)
    if user:
        print(f"User found: {user.username}, stored password: {user.password_hash}")  # 디버깅 로그
        print(f"Attempting to verify password: {user_data.password}")  # 디버깅 로그
    else:
        print(f"User not found: {user_data.username}")  # 디버깅 로그
    
    user = user_service.authenticate_user(user_data.username, user_data.password)
    
    if not user:
        print("Authentication failed")  # 디버깅 로그
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"Authentication successful for user: {user.username}")  # 디버깅 로그
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(get_current_user)):
    """현재 로그인한 사용자 정보를 조회합니다."""
    return current_user 