import os
from dotenv import load_dotenv
load_dotenv()

from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.model.mcp_server import MCPServer, TransportType, MCPServerTool, MCPServerProperty
from backend.service.mcp_server_service import MCPServerService

dao = MCPServerDAO("mcp_market.db")
dao.connect()
dao.create_table()

# GitHub 토큰 가져오기
github_token = os.getenv("GITHUB_TOKEN")
print(f"GitHub 토큰 설정: {'있음' if github_token else '없음'}")

# MCP 서비스 인스턴스 생성
mcp_service = MCPServerService(github_token)

def convert_dict_to_mcp_tools(tools_dict_list):
    """딕셔너리 리스트를 MCPServerTool 객체 리스트로 변환"""
    mcp_tools = []
    for tool_dict in tools_dict_list:
        # input_properties를 MCPServerProperty 객체로 변환
        input_properties = []
        for prop_dict in tool_dict.get("input_properties", []):
            prop = MCPServerProperty(
                name=prop_dict.get("name", ""),
                description=prop_dict.get("description"),
                required=prop_dict.get("required", False)
            )
            input_properties.append(prop)
        
        # MCPServerTool 객체 생성
        tool = MCPServerTool(
            name=tool_dict["name"],
            description=tool_dict.get("description", ""),  # description이 없으면 빈 문자열
            input_properties=input_properties
        )
        mcp_tools.append(tool)
    return mcp_tools

# 예시 config JSON
example_config = {
    "mcpServers": {
        "weather": {
            "command": "uv",
            "args": [
                "--directory",
                "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\weather",
                "run",
                "weather.py"
            ]
        }
    }
}

dummy1 = MCPServer(
    id="1",
    github_link="https://github.com/redis/mcp-redis",
    name="github mcp",
    description="This tools provide various github features using github API",
    transport=TransportType.sse,
    category="Code Tools",
    tags=["github", "code"],
    status="active",
    config=example_config
)
dummy2 = MCPServer(
    id="2",
    github_link="https://github.com/exa-labs/exa-mcp-server",
    name="Jirahub",
    description="This toolkit allows AI to access the JIRA",
    transport=TransportType.sse,
    category="Documentation",
    tags=["jira", "issue"],
    status="active",
    config=example_config
)
dummy3 = MCPServer(
    id="3",
    github_link="https://github.com/brightdata/brightdata-mcp",
    name="Test Vitlas",
    description="One system for all our projects' test results.",
    transport=TransportType.streamable_http,
    category="DevOps",
    tags=["test", "issue"],
    status="active",
    config=example_config
)
# MCP 서버들을 DB에 저장하고 tools 정보도 함께 저장
print("=== Starting MCP server data insertion ===")

tools1_dict = mcp_service.read_mcp_server_tool_list(dummy1.github_link)
tools1 = convert_dict_to_mcp_tools(tools1_dict)
dummy1.tools = tools1
dao.create_mcp(dummy1)
print(f"   - Saved {len(tools1)} tools")

tools2_dict = mcp_service.read_mcp_server_tool_list(dummy2.github_link)
tools2 = convert_dict_to_mcp_tools(tools2_dict)
dummy2.tools = tools2
dao.create_mcp(dummy2)
print(f"   - Saved {len(tools2)} tools")

tools3_dict = mcp_service.read_mcp_server_tool_list(dummy3.github_link)
tools3 = convert_dict_to_mcp_tools(tools3_dict)
dummy3.tools = tools3
dao.create_mcp(dummy3)
print(f"   - Saved {len(tools3)} tools")


dao.close()
print("=== MCP server data insertion completed! ===")
