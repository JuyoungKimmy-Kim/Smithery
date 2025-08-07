import pytest
from backend.database.model import User, MCPServer, UserFavorite
from backend.service.user_service import UserService
from backend.service.mcp_server_service import MCPServerService

class TestFavorite:
    """Favorite CRUD 테스트 클래스"""
    
    def test_add_favorite(self, user_service, mcp_server_service):
        """즐겨찾기 추가 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Act
        result = user_service.add_favorite(user.id, mcp_server.id)
        
        # Assert
        assert result is True
        
        # 즐겨찾기 목록 확인
        favorites = user_service.get_user_favorites(user.id)
        assert len(favorites) == 1
        assert favorites[0].id == mcp_server.id
    
    def test_add_favorite_duplicate(self, user_service, mcp_server_service):
        """중복 즐겨찾기 추가 시도 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Act
        user_service.add_favorite(user.id, mcp_server.id)
        result = user_service.add_favorite(user.id, mcp_server.id)  # 중복 추가 시도
        
        # Assert
        assert result is False  # 중복 추가는 실패해야 함
        
        # 즐겨찾기 목록은 여전히 1개여야 함
        favorites = user_service.get_user_favorites(user.id)
        assert len(favorites) == 1
    
    def test_remove_favorite(self, user_service, mcp_server_service):
        """즐겨찾기 제거 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        user_service.add_favorite(user.id, mcp_server.id)
        
        # Act
        result = user_service.remove_favorite(user.id, mcp_server.id)
        
        # Assert
        assert result is True
        
        # 즐겨찾기 목록 확인
        favorites = user_service.get_user_favorites(user.id)
        assert len(favorites) == 0
    
    def test_remove_favorite_nonexistent(self, user_service, mcp_server_service):
        """존재하지 않는 즐겨찾기 제거 시도 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Act
        result = user_service.remove_favorite(user.id, mcp_server.id)
        
        # Assert
        assert result is False  # 존재하지 않는 즐겨찾기 제거는 실패해야 함
    
    def test_is_favorite_true(self, user_service, mcp_server_service):
        """즐겨찾기 여부 확인 테스트 (즐겨찾기된 경우)"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        user_service.add_favorite(user.id, mcp_server.id)
        
        # Act
        is_favorite = user_service.is_favorite(user.id, mcp_server.id)
        
        # Assert
        assert is_favorite is True
    
    def test_is_favorite_false(self, user_service, mcp_server_service):
        """즐겨찾기 여부 확인 테스트 (즐겨찾기되지 않은 경우)"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Act
        is_favorite = user_service.is_favorite(user.id, mcp_server.id)
        
        # Assert
        assert is_favorite is False
    
    def test_get_user_favorites(self, user_service, mcp_server_service):
        """사용자 즐겨찾기 목록 조회 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data1 = {
            "name": "Test MCP Server 1",
            "github_link": "https://github.com/test/mcp-server-1",
            "description": "Test MCP server 1 description",
            "category": "test"
        }
        mcp_server_data2 = {
            "name": "Test MCP Server 2",
            "github_link": "https://github.com/test/mcp-server-2",
            "description": "Test MCP server 2 description",
            "category": "test"
        }
        mcp_server_data3 = {
            "name": "Test MCP Server 3",
            "github_link": "https://github.com/test/mcp-server-3",
            "description": "Test MCP server 3 description",
            "category": "test"
        }
        
        mcp1 = mcp_server_service.create_mcp_server(mcp_server_data1, user.id)
        mcp2 = mcp_server_service.create_mcp_server(mcp_server_data2, user.id)
        mcp3 = mcp_server_service.create_mcp_server(mcp_server_data3, user.id)
        
        user_service.add_favorite(user.id, mcp1.id)
        user_service.add_favorite(user.id, mcp2.id)
        
        # Act
        favorites = user_service.get_user_favorites(user.id)
        
        # Assert
        assert len(favorites) == 2
        favorite_ids = [favorite.id for favorite in favorites]
        assert mcp1.id in favorite_ids
        assert mcp2.id in favorite_ids
        assert mcp3.id not in favorite_ids
    
    def test_get_user_favorites_empty(self, user_service):
        """빈 즐겨찾기 목록 조회 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        
        # Act
        favorites = user_service.get_user_favorites(user.id)
        
        # Assert
        assert len(favorites) == 0
    
    def test_add_favorite_nonexistent_user(self, user_service, mcp_server_service):
        """존재하지 않는 사용자로 즐겨찾기 추가 시도 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Act
        result = user_service.add_favorite(999, mcp_server.id)  # 존재하지 않는 사용자 ID
        
        # Assert
        assert result is False
    
    def test_add_favorite_nonexistent_mcp_server(self, user_service):
        """존재하지 않는 MCP 서버로 즐겨찾기 추가 시도 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        
        # Act
        result = user_service.add_favorite(user.id, 999)  # 존재하지 않는 MCP 서버 ID
        
        # Assert
        assert result is False
    
    def test_multiple_users_favorites(self, user_service, mcp_server_service):
        """여러 사용자의 즐겨찾기 테스트"""
        # Arrange
        user1 = user_service.create_user("user1", "user1@example.com", "password")
        user2 = user_service.create_user("user2", "user2@example.com", "password")
        
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user1.id)
        
        # Act
        user1_favorite = user_service.add_favorite(user1.id, mcp_server.id)
        user2_favorite = user_service.add_favorite(user2.id, mcp_server.id)
        
        # Assert
        assert user1_favorite is True
        assert user2_favorite is True
        
        # 각 사용자의 즐겨찾기 목록 확인
        user1_favorites = user_service.get_user_favorites(user1.id)
        user2_favorites = user_service.get_user_favorites(user2.id)
        
        assert len(user1_favorites) == 1
        assert len(user2_favorites) == 1
        assert user1_favorites[0].id == mcp_server.id
        assert user2_favorites[0].id == mcp_server.id
    
    def test_favorite_after_remove_and_add(self, user_service, mcp_server_service):
        """즐겨찾기 제거 후 다시 추가 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Act
        user_service.add_favorite(user.id, mcp_server.id)
        user_service.remove_favorite(user.id, mcp_server.id)
        result = user_service.add_favorite(user.id, mcp_server.id)
        
        # Assert
        assert result is True
        
        # 즐겨찾기 목록 확인
        favorites = user_service.get_user_favorites(user.id)
        assert len(favorites) == 1
        assert favorites[0].id == mcp_server.id 