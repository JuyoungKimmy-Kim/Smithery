from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from backend.database import get_db
from backend.service import UserService
from backend.api.schemas import UserCreate, UserLogin, UserResponse
from backend.api.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

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