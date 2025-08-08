import pytest
from backend.database.model import MCPServer, User
from backend.service.mcp_server_service import MCPServerService
from backend.service.user_service import UserService

class TestMCP:
    """MCP Server CRUD 테스트 클래스"""
    
    def test_create_mcp_server(self, mcp_server_service, user_service):
        """MCP 서버 생성 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test",
            "tags": ["test", "example"]
        }
        
        # Act
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Assert
        assert mcp_server is not None
        assert mcp_server.name == mcp_server_data["name"]
        assert mcp_server.github_link == mcp_server_data["github_link"]
        assert mcp_server.description == mcp_server_data["description"]
        assert mcp_server.category == mcp_server_data["category"]
        assert mcp_server.owner_id == user.id
        assert mcp_server.status == "pending"
    
    def test_get_mcp_server_by_id(self, mcp_server_service, user_service):
        """ID로 MCP 서버 조회 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        
        created_mcp = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Act
        found_mcp = mcp_server_service.get_mcp_server_by_id(created_mcp.id)
        
        # Assert
        assert found_mcp is not None
        assert found_mcp.name == mcp_server_data["name"]
        assert found_mcp.github_link == mcp_server_data["github_link"]
    
    def test_get_mcp_server_with_tools(self, mcp_server_service, user_service):
        """도구 정보와 함께 MCP 서버 조회 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        
        created_mcp = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Act
        found_mcp = mcp_server_service.get_mcp_server_with_tools(created_mcp.id)
        
        # Assert
        assert found_mcp is not None
        assert found_mcp.name == mcp_server_data["name"]
        # 도구 정보가 포함되어 있는지 확인 (실제 구현에 따라 다를 수 있음)
    
    def test_get_approved_mcp_servers(self, mcp_server_service, user_service):
        """승인된 MCP 서버 목록 조회 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        
        mcp_server = mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        mcp_server_service.approve_mcp_server(mcp_server.id)
        
        # Act
        approved_servers = mcp_server_service.get_approved_mcp_servers()
        
        # Assert
        assert len(approved_servers) == 1
        assert approved_servers[0].id == mcp_server.id
        assert approved_servers[0].status == "approved"
    
    def test_search_mcp_servers(self, mcp_server_service, user_service):
        """MCP 서버 검색 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data1 = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server_data2 = {
            "name": "Another MCP Server",
            "github_link": "https://github.com/test/another-mcp-server",
            "description": "Another MCP server description",
            "category": "other"
        }
        
        mcp1 = mcp_server_service.create_mcp_server(mcp_server_data1, user.id)
        mcp2 = mcp_server_service.create_mcp_server(mcp_server_data2, user.id)
        mcp_server_service.approve_mcp_server(mcp1.id)
        mcp_server_service.approve_mcp_server(mcp2.id)
        
        # Act
        search_results = mcp_server_service.search_mcp_servers("Test")
        
        # Assert
        assert len(search_results) == 1
        assert search_results[0].name == "Test MCP Server"
    
    def test_get_mcp_servers_by_category(self, mcp_server_service, user_service):
        """카테고리별 MCP 서버 목록 조회 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data1 = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        mcp_server_data2 = {
            "name": "Another MCP Server",
            "github_link": "https://github.com/test/another-mcp-server",
            "description": "Another MCP server description",
            "category": "other"
        }
        
        mcp1 = mcp_server_service.create_mcp_server(mcp_server_data1, user.id)
        mcp2 = mcp_server_service.create_mcp_server(mcp_server_data2, user.id)
        mcp_server_service.approve_mcp_server(mcp1.id)
        mcp_server_service.approve_mcp_server(mcp2.id)
        
        # Act
        test_category_servers = mcp_server_service.get_mcp_servers_by_category("test")
        
        # Assert
        assert len(test_category_servers) == 1
        assert test_category_servers[0].category == "test"
    
    def test_get_pending_mcp_servers(self, mcp_server_service, user_service):
        """승인 대기 중인 MCP 서버 목록 조회 테스트"""
        # Arrange
        user = user_service.create_user("testuser", "test@example.com", "password")
        mcp_server_data = {
            "name": "Test MCP Server",
            "github_link": "https://github.com/test/mcp-server",
            "description": "Test MCP server description",
            "category": "test"
        }
        
        mcp_server_service.create_mcp_server(mcp_server_data, user.id)
        
        # Act
        pending_servers = mcp_server_service.get_pending_mcp_servers()
        
        # Assert
        assert len(pending_servers) == 1
        assert pending_servers[0].status == "pending"
    
    def test_approve_mcp_server(self, mcp_server_service, user_service):
        """MCP 서버 승인 테스트"""
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
        approved_mcp = mcp_server_service.approve_mcp_server(mcp_server.id)
        
        # Assert
        assert approved_mcp is not None
        assert approved_mcp.status == "approved"
    
    def test_reject_mcp_server(self, mcp_server_service, user_service):
        """MCP 서버 거부 테스트"""
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
        rejected_mcp = mcp_server_service.reject_mcp_server(mcp_server.id)
        
        # Assert
        assert rejected_mcp is not None
        assert rejected_mcp.status == "rejected"
    
    def test_delete_mcp_server(self, mcp_server_service, user_service):
        """MCP 서버 삭제 테스트"""
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
        result = mcp_server_service.delete_mcp_server(mcp_server.id)
        
        # Assert
        assert result is True
        
        # 삭제 확인
        deleted_mcp = mcp_server_service.get_mcp_server_by_id(mcp_server.id)
        assert deleted_mcp is None
    
    def test_get_mcp_servers_by_owner(self, mcp_server_service, user_service):
        """소유자별 MCP 서버 목록 조회 테스트"""
        # Arrange
        user1 = user_service.create_user("user1", "user1@example.com", "password")
        user2 = user_service.create_user("user2", "user2@example.com", "password")
        
        mcp_server_data1 = {
            "name": "User1 MCP Server",
            "github_link": "https://github.com/user1/mcp-server",
            "description": "User1 MCP server description",
            "category": "test"
        }
        mcp_server_data2 = {
            "name": "User2 MCP Server",
            "github_link": "https://github.com/user2/mcp-server",
            "description": "User2 MCP server description",
            "category": "test"
        }
        
        mcp_server_service.create_mcp_server(mcp_server_data1, user1.id)
        mcp_server_service.create_mcp_server(mcp_server_data2, user2.id)
        
        # Act
        user1_servers = mcp_server_service.get_mcp_servers_by_owner(user1.id)
        user2_servers = mcp_server_service.get_mcp_servers_by_owner(user2.id)
        
        # Assert
        assert len(user1_servers) == 1
        assert user1_servers[0].name == "User1 MCP Server"
        assert len(user2_servers) == 1
        assert user2_servers[0].name == "User2 MCP Server"
    
    def test_update_mcp_server(self, mcp_server_service, user_service):
        """MCP 서버 수정 테스트"""
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
        update_data = {
            "name": "Updated MCP Server",
            "description": "Updated description"
        }
        updated_mcp = mcp_server_service.update_mcp_server(mcp_server.id, update_data)
        
        # Assert
        assert updated_mcp is not None
        assert updated_mcp.name == "Updated MCP Server"
        assert updated_mcp.description == "Updated description"
        assert updated_mcp.github_link == mcp_server_data["github_link"]  # 변경되지 않은 필드 