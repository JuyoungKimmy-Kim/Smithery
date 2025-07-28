import os
import tempfile
import pytest
from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.model.mcp_server import MCPServer, TransportType
from backend.service.mcp_server_service import MCPServerService

@pytest.fixture(scope="module")
def test_db_path():
    # test 디렉터리에 임시 DB 파일 생성
    db_path = os.path.join(os.path.dirname(__file__), "test_mcp_market.db")
    # 기존 파일 있으면 삭제
    if os.path.exists(db_path):
        os.remove(db_path)
    yield db_path
    # 테스트 끝나면 삭제
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture(scope="module")
def mcp_service():
    github_token = os.getenv("GITHUB_TOKEN")
    return MCPServerService(github_token)


def test_insert_and_fetch_tools(test_db_path, mcp_service):
    dao = MCPServerDAO(test_db_path)
    dao.connect()
    dao.create_table()

    # 테스트용 MCP 서버 정보
    repo_url = "https://github.com/modelcontextprotocol/server-filesystem"
    mcp = MCPServer(
        id="test1",
        github_link=repo_url,
        name="Test MCP",
        description="pytest용 MCP",
        transport=TransportType.sse,
        category="test",
        tags=["pytest", "test"],
        status="active",
    )
    # tools 정보 가져오기
    tools = mcp_service.read_mcp_server_tool_list(repo_url)
    mcp.tools = tools
    # DB에 저장
    dao.create_mcp(mcp)
    # DB에서 다시 가져오기
    fetched = dao.get_mcp("test1")
    dao.close()

    assert fetched is not None
    assert fetched.tools is not None
    assert isinstance(fetched.tools, list)
    assert len(fetched.tools) > 0
