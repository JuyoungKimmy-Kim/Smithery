from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.model.mcp_server import MCPServer, TransportType
from backend.service.mcp_server_service import MCPServerService

dao = MCPServerDAO("mcp_market.db")
dao.connect()
dao.create_table()

# MCP 서비스 인스턴스 생성
mcp_service = MCPServerService()

dummy1 = MCPServer(
    id="1",
    github_link="https://github.com/modelcontextprotocol/server-filesystem",
    name="github mcp",
    description="This tools provide various github features using github API",
    transport=TransportType.sse,
    category="review system",
    tags=["github", "code"],
    status="active",
)
dummy2 = MCPServer(
    id="2",
    github_link="https://github.com/modelcontextprotocol/server-git",
    name="Jirahub",
    description="This toolkit allows AI to access the JIRA",
    transport=TransportType.sse,
    category="issue",
    tags=["jira", "issue"],
    status="active",
)
dummy3 = MCPServer(
    id="3",
    github_link="https://github.com/modelcontextprotocol/server-http",
    name="Test Vitlas",
    description="One system for all our projects' test results.",
    transport=TransportType.streamable_http,
    category="test",
    tags=["test", "issue"],
    status="active",
)
dummy4 = MCPServer(
    id="4",
    github_link="https://github.com/modelcontextprotocol/server-ollama",
    name="Knowhub",
    description="This toolkit helps AI search for knowledge, tables, and images stored in the database.",
    transport=TransportType.sse,
    category="search",
    tags=["search", "issue"],
    status="active",
)
dummy5 = MCPServer(
    id="5",
    github_link="https://github.com/modelcontextprotocol/server-ollama",
    name="Perforce",
    description="This toolkit enables AI to interact Perforce P4 and its review system Swarm",
    transport=TransportType.sse,
    category="test",
    tags=["perforce", "code"],
    status="active",
)

# MCP 서버들을 DB에 저장하고 tools 정보도 함께 저장
print("=== Starting MCP server data insertion ===")

# dummy1 - Filesystem MCP Server
print("1. Processing Filesystem MCP Server...")
tools1 = mcp_service.read_mcp_server_tool_list(dummy1.github_link)
dummy1.tools = tools1
dao.create_mcp(dummy1)
print(f"   - Saved {len(tools1)} tools")

# dummy2 - Git MCP Server
print("2. Processing Git MCP Server...")
tools2 = mcp_service.read_mcp_server_tool_list(dummy2.github_link)
dummy2.tools = tools2
dao.create_mcp(dummy2)
print(f"   - Saved {len(tools2)} tools")

# dummy3 - HTTP MCP Server
print("3. Processing HTTP MCP Server...")
tools3 = mcp_service.read_mcp_server_tool_list(dummy3.github_link)
dummy3.tools = tools3
dao.create_mcp(dummy3)
print(f"   - Saved {len(tools3)} tools")

# dummy4 - Ollama MCP Server
print("4. Processing Ollama MCP Server...")
tools4 = mcp_service.read_mcp_server_tool_list(dummy4.github_link)
dummy4.tools = tools4
dao.create_mcp(dummy4)
print(f"   - Saved {len(tools4)} tools")

# dummy5 - Ollama MCP Server (duplicate but with different name)
print("5. Processing Ollama MCP Server (2)...")
tools5 = mcp_service.read_mcp_server_tool_list(dummy5.github_link)
dummy5.tools = tools5
dao.create_mcp(dummy5)
print(f"   - Saved {len(tools5)} tools")

dao.close()
print("=== MCP server data insertion completed! ===")
