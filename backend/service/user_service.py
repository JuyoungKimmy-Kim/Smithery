from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from backend.database.dao.user_dao import UserDAO
from backend.database.model import User, MCPServer

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_dao = UserDAO(db)
    
    def create_user(self, username: str, email: str, password: str, is_admin: str = "user") -> User:
        """새 사용자를 생성합니다."""
        # 중복 검사
        if self.user_dao.get_user_by_username(username):
            raise ValueError("이미 존재하는 사용자명입니다.")
        
        if self.user_dao.get_user_by_email(email):
            raise ValueError("이미 존재하는 이메일입니다.")
        
        return self.user_dao.create_user(username, email, password, is_admin)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """사용자 인증을 수행합니다."""
        print(f"UserService.authenticate_user called with username: {username}")  # 디버깅 로그
        
        user = self.user_dao.get_user_by_username(username)
        print(f"User found in DAO: {user is not None}")  # 디버깅 로그
        
        if user:
            print(f"Stored password hash: {user.password_hash}")  # 디버깅 로그
            print(f"Input password: {password}")  # 디버깅 로그
            
            is_valid = self.user_dao.verify_password(password, user.password_hash)
            print(f"Password verification result: {is_valid}")  # 디버깅 로그
            
            if is_valid:
                return user
        
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자를 조회합니다."""
        return self.user_dao.get_user_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 사용자를 조회합니다."""
        return self.user_dao.get_user_by_username(username)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자를 조회합니다."""
        return self.user_dao.get_user_by_email(email)
    
    def get_user_mcp_servers(self, user_id: int) -> List[MCPServer]:
        """사용자가 등록한 MCP 서버 목록을 조회합니다."""
        return self.user_dao.get_user_mcp_servers(user_id)
    
    def get_user_all_mcp_servers(self, user_id: int) -> List[MCPServer]:
        """사용자가 등록한 모든 MCP 서버 목록을 조회합니다. (pending 포함)"""
        return self.user_dao.get_user_all_mcp_servers(user_id)
    
    def get_user_mcp_servers_by_username(self, username: str) -> List[MCPServer]:
        """사용자명으로 사용자가 등록한 MCP 서버 목록을 조회합니다."""
        user = self.user_dao.get_user_by_username(username)
        if not user:
            return []
        return self.user_dao.get_user_mcp_servers(user.id)
    
    def get_user_favorites(self, user_id: int) -> List[MCPServer]:
        """사용자가 즐겨찾기한 MCP 서버 목록을 조회합니다."""
        return self.user_dao.get_user_favorites(user_id)
    
    def add_favorite(self, user_id: int, mcp_server_id: int) -> bool:
        """즐겨찾기를 추가합니다."""
        # 사용자와 MCP 서버가 존재하는지 확인
        user = self.user_dao.get_user_by_id(user_id)
        if not user:
            return False
        
        # MCP 서버 존재 여부 확인 (간단한 방법으로)
        from backend.database.model import MCPServer
        mcp_server = self.db.query(MCPServer).filter(MCPServer.id == mcp_server_id).first()
        if not mcp_server:
            return False
        
        return self.user_dao.add_favorite(user_id, mcp_server_id)
    
    def remove_favorite(self, user_id: int, mcp_server_id: int) -> bool:
        """즐겨찾기를 제거합니다."""
        return self.user_dao.remove_favorite(user_id, mcp_server_id)
    
    def is_favorite(self, user_id: int, mcp_server_id: int) -> bool:
        """즐겨찾기 여부를 확인합니다."""
        return self.user_dao.is_favorite(user_id, mcp_server_id)
    
    def update_user_profile(self, user_id: int, **kwargs) -> Optional[User]:
        """사용자 프로필을 업데이트합니다."""
        return self.user_dao.update_user(user_id, **kwargs)
    
    def is_admin(self, user_id: int) -> bool:
        """사용자가 관리자인지 확인합니다."""
        user = self.user_dao.get_user_by_id(user_id)
        return user is not None and user.is_admin == "admin" 