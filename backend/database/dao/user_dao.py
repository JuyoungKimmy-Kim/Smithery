from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from backend.database.model import User, MCPServer, UserFavorite
from passlib.context import CryptContext

# bcrypt 버전 문제 해결을 위한 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__default_rounds=12)

class UserDAO:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, username: str, email: str, password: str, is_admin: str = "user") -> User:
        """새 사용자를 생성합니다."""
        hashed_password = pwd_context.hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            is_admin=is_admin
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자를 조회합니다."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 사용자를 조회합니다."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자를 조회합니다."""
        return self.db.query(User).filter(User.email == email).first()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호를 검증합니다."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # bcrypt 검증 실패 시 평문 비교 (개발용)
            return hashed_password == plain_password
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """사용자 정보를 업데이트합니다."""
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def get_user_mcp_servers(self, user_id: int) -> List[MCPServer]:
        """사용자가 등록한 MCP 서버 목록을 조회합니다."""
        return self.db.query(MCPServer).filter(MCPServer.owner_id == user_id).all()
    
    def get_user_favorites(self, user_id: int) -> List[MCPServer]:
        """사용자가 즐겨찾기한 MCP 서버 목록을 조회합니다."""
        return self.db.query(MCPServer).join(UserFavorite).filter(UserFavorite.user_id == user_id).all()
    
    def add_favorite(self, user_id: int, mcp_server_id: int) -> bool:
        """즐겨찾기를 추가합니다."""
        existing = self.db.query(UserFavorite).filter(
            and_(UserFavorite.user_id == user_id, UserFavorite.mcp_server_id == mcp_server_id)
        ).first()
        
        if existing:
            return False
        
        favorite = UserFavorite(user_id=user_id, mcp_server_id=mcp_server_id)
        self.db.add(favorite)
        self.db.commit()
        return True
    
    def remove_favorite(self, user_id: int, mcp_server_id: int) -> bool:
        """즐겨찾기를 제거합니다."""
        favorite = self.db.query(UserFavorite).filter(
            and_(UserFavorite.user_id == user_id, UserFavorite.mcp_server_id == mcp_server_id)
        ).first()
        
        if favorite:
            self.db.delete(favorite)
            self.db.commit()
            return True
        return False
    
    def is_favorite(self, user_id: int, mcp_server_id: int) -> bool:
        """즐겨찾기 여부를 확인합니다."""
        favorite = self.db.query(UserFavorite).filter(
            and_(UserFavorite.user_id == user_id, UserFavorite.mcp_server_id == mcp_server_id)
        ).first()
        return favorite is not None 