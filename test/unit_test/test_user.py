import pytest
from backend.database.model import User
from backend.service.user_service import UserService

class TestUser:
    """User CRUD 테스트 클래스"""
    
    def test_create_user(self, user_service):
        """사용자 생성 테스트"""
        # Arrange
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        
        # Act
        user = user_service.create_user(username, email, password)
        
        # Assert
        assert user is not None
        assert user.username == username
        assert user.email == email
        assert user.password_hash is not None
        assert user.is_admin == "user"
    
    def test_create_user_duplicate_username(self, user_service):
        """중복 사용자명으로 사용자 생성 시도 테스트"""
        # Arrange
        username = "testuser"
        email1 = "test1@example.com"
        email2 = "test2@example.com"
        password = "password123"
        
        # Act & Assert
        user_service.create_user(username, email1, password)
        
        with pytest.raises(ValueError, match="이미 존재하는 사용자명입니다."):
            user_service.create_user(username, email2, password)
    
    def test_create_user_duplicate_email(self, user_service):
        """중복 이메일로 사용자 생성 시도 테스트"""
        # Arrange
        username1 = "testuser1"
        username2 = "testuser2"
        email = "test@example.com"
        password = "password123"
        
        # Act & Assert
        user_service.create_user(username1, email, password)
        
        with pytest.raises(ValueError, match="이미 존재하는 이메일입니다."):
            user_service.create_user(username2, email, password)
    
    def test_authenticate_user_success(self, user_service):
        """사용자 인증 성공 테스트"""
        # Arrange
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        
        user_service.create_user(username, email, password)
        
        # Act
        authenticated_user = user_service.authenticate_user(username, password)
        
        # Assert
        assert authenticated_user is not None
        assert authenticated_user.username == username
    
    def test_authenticate_user_wrong_password(self, user_service):
        """잘못된 비밀번호로 인증 시도 테스트"""
        # Arrange
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        wrong_password = "wrongpassword"
        
        user_service.create_user(username, email, password)
        
        # Act
        authenticated_user = user_service.authenticate_user(username, wrong_password)
        
        # Assert
        assert authenticated_user is None
    
    def test_authenticate_user_nonexistent_user(self, user_service):
        """존재하지 않는 사용자로 인증 시도 테스트"""
        # Arrange
        username = "nonexistent"
        password = "password123"
        
        # Act
        authenticated_user = user_service.authenticate_user(username, password)
        
        # Assert
        assert authenticated_user is None
    
    def test_get_user_by_id(self, user_service):
        """ID로 사용자 조회 테스트"""
        # Arrange
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        
        created_user = user_service.create_user(username, email, password)
        
        # Act
        found_user = user_service.get_user_by_id(created_user.id)
        
        # Assert
        assert found_user is not None
        assert found_user.username == username
        assert found_user.email == email
    
    def test_get_user_by_username(self, user_service):
        """사용자명으로 사용자 조회 테스트"""
        # Arrange
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        
        user_service.create_user(username, email, password)
        
        # Act
        found_user = user_service.get_user_by_username(username)
        
        # Assert
        assert found_user is not None
        assert found_user.username == username
        assert found_user.email == email
    
    def test_get_user_by_nonexistent_id(self, user_service):
        """존재하지 않는 ID로 사용자 조회 테스트"""
        # Act
        found_user = user_service.get_user_by_id(999)
        
        # Assert
        assert found_user is None
    
    def test_get_user_by_nonexistent_username(self, user_service):
        """존재하지 않는 사용자명으로 사용자 조회 테스트"""
        # Act
        found_user = user_service.get_user_by_username("nonexistent")
        
        # Assert
        assert found_user is None
    
    def test_update_user_profile(self, user_service):
        """사용자 프로필 업데이트 테스트"""
        # Arrange
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        
        user = user_service.create_user(username, email, password)
        
        # Act
        updated_user = user_service.update_user_profile(
            user.id, 
            username="updateduser",
            email="updated@example.com",
            avatar_url="https://example.com/avatar.jpg"
        )
        
        # Assert
        assert updated_user is not None
        assert updated_user.username == "updateduser"
        assert updated_user.email == "updated@example.com"
        assert updated_user.avatar_url == "https://example.com/avatar.jpg"
    
    def test_is_admin(self, user_service):
        """관리자 권한 확인 테스트"""
        # Arrange
        admin_user = user_service.create_user("admin", "admin@example.com", "password", "admin")
        regular_user = user_service.create_user("user", "user@example.com", "password", "user")
        
        # Act & Assert
        assert user_service.is_admin(admin_user.id) is True
        assert user_service.is_admin(regular_user.id) is False
        assert user_service.is_admin(999) is False 