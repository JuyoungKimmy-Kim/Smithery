from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.model.mcp_server import MCPServer, TransportType

dao = MCPServerDAO("mcp_market.db")
dao.connect()
dao.create_table()

dummy1 = MCPServer(
    id="1",
    github_link="https://github.com/example/mcp1",
    name="github mcp",
    description="This tools provide various github features using github API",
    transport=TransportType.sse,
    category="review system",
    tags=["github", "code"],
    status="active",
)
dummy2 = MCPServer(
    id="2",
    github_link="https://github.com/example/mcp2",
    name="Jirahub",
    description="This toolkit allows AI to access the JIRA",
    transport=TransportType.sse,
    category="issue",
    tags=["jira", "issue"],
    status="active",
)
dummy3 = MCPServer(
    id="3",
    github_link="https://github.com/example/mcp3",
    name="Test Vitlas",
    description="One system for all our projects' test results.",
    transport=TransportType.streamable_http,
    category="test",
    tags=["test", "issue"],
    status="active",
)
dummy4 = MCPServer(
    id="4",
    github_link="https://github.com/example/mcp4",
    name="Knowhub",
    description="This toolkit helps AI search for knowledge, tables, and images stored in the database.",
    transport=TransportType.sse,
    category="search",
    tags=["search", "issue"],
    status="active",
)
dummy5 = MCPServer(
    id="5",
    github_link="https://github.com/example/mcp5",
    name="Perforce",
    description="This toolkit enables AI to interact Perforce P4 and its review system Swarm",
    transport=TransportType.sse,
    category="test",
    tags=["perforce", "code"],
    status="active",
)

dao.create_mcp(dummy1)
dao.create_mcp(dummy2)
dao.create_mcp(dummy3)
dao.create_mcp(dummy4)
dao.create_mcp(dummy5)
dao.close()
print("더미 데이터 입력 완료!")
