import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from backend.database.dao.user_dao import UserDAO
from backend.database.model.user import User, UserCreate, UserLogin


class AuthService:
    def __init__(self, secret_key: str, user_dao: UserDAO):
        self.secret_key = secret_key
        self.user_dao = user_dao
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None

    def register_user(self, user_create: UserCreate) -> Optional[User]:
        """사용자 등록"""
        # 사용자명 중복 확인
        if self.user_dao.get_user_by_username(user_create.username):
            return None
        
        # 이메일 중복 확인
        if self.user_dao.get_user_by_email(user_create.email):
            return None
        
        # 비밀번호 해시화
        hashed_password = self.hash_password(user_create.password)
        
        # 사용자 생성
        return self.user_dao.create_user(user_create, hashed_password)

    def authenticate_user(self, user_login: UserLogin) -> Optional[User]:
        """사용자 인증"""
        user = self.user_dao.get_user_by_username(user_login.username)
        if not user:
            return None
        
        if not self.verify_password(user_login.password, user.password_hash):
            return None
        
        return user

    def login_user(self, user_login: UserLogin) -> Optional[dict]:
        """사용자 로그인"""
        user = self.authenticate_user(user_login)
        if not user:
            return None
        
        # 액세스 토큰 생성
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }

    def get_current_user(self, token: str) -> Optional[User]:
        """현재 사용자 조회"""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        return self.user_dao.get_user_by_id(int(user_id))

    def is_admin(self, token: str) -> bool:
        """관리자 권한 확인"""
        user = self.get_current_user(token)
        return user and user.role == "admin" 