import os
from dotenv import load_dotenv

load_dotenv()

from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.model.mcp_server import (
    MCPServer,
    TransportType,
    MCPServerTool,
    MCPServerProperty,
)
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
                required=prop_dict.get("required", False),
            )
            input_properties.append(prop)

        # MCPServerTool 객체 생성
        tool = MCPServerTool(
            name=tool_dict["name"],
            description=tool_dict.get(
                "description", ""
            ),  # description이 없으면 빈 문자열
            input_properties=input_properties,
        )
        mcp_tools.append(tool)
    return mcp_tools


def debug_tools_extraction(github_link, server_name):
    """Tools 추출 과정을 디버깅하는 함수"""
    print(f"\n=== {server_name} Tools 추출 디버깅 ===")
    print(f"GitHub 링크: {github_link}")

    # GitHub URL 파싱 테스트
    repo_info = mcp_service._parse_github_url(github_link)
    print(f"파싱된 repo 정보: {repo_info}")

    if not repo_info:
        print("❌ GitHub URL 파싱 실패")
        return []

    owner, repo, path = repo_info
    print(f"Owner: {owner}, Repo: {repo}, Path: {path}")

    # MCP 설정 파일 찾기
    try:
        mcp_config = mcp_service._find_mcp_config_files(owner, repo, path)
        print(f"발견된 MCP 설정 파일: {len(mcp_config)}개")
        for config in mcp_config:
            print(f"  - {config.get('path', 'unknown')}")
    except Exception as e:
        print(f"❌ MCP 설정 파일 찾기 실패: {e}")

    # 소스 파일 찾기
    try:
        source_files = mcp_service._find_source_files(owner, repo, path)
        print(f"발견된 소스 파일: {len(source_files)}개")

        # 파일 타입별 통계
        file_types = {}
        for file_info in source_files:
            ext = (
                file_info.get("path", "").split(".")[-1]
                if "." in file_info.get("path", "")
                else "no_ext"
            )
            file_types[ext] = file_types.get(ext, 0) + 1

        print("파일 타입별 통계:")
        for ext, count in file_types.items():
            print(f"  - .{ext}: {count}개")

        # 처음 10개 파일 경로 출력
        print("발견된 파일들 (처음 10개):")
        for i, file_info in enumerate(source_files[:10]):
            print(f"  {i+1}. {file_info.get('path', 'unknown')}")
        if len(source_files) > 10:
            print(f"  ... 그리고 {len(source_files) - 10}개 더")

    except Exception as e:
        print(f"❌ 소스 파일 찾기 실패: {e}")

    # Tools 추출
    try:
        tools = mcp_service.read_mcp_server_tool_list(github_link)
        print(f"추출된 tools: {len(tools)}개")

        for i, tool in enumerate(tools[:10]):  # 처음 10개만 출력
            print(
                f"  {i+1}. {tool.get('name', 'Unknown')} ({tool.get('language', 'unknown')}) - {tool.get('file', 'unknown')}"
            )

        if len(tools) > 10:
            print(f"  ... 그리고 {len(tools) - 10}개 더")

        return tools
    except Exception as e:
        print(f"❌ Tools 추출 실패: {e}")
        return []


# 예시 config JSON
example_config = {
    "mcpServers": {
        "weather": {
            "command": "uv",
            "args": [
                "--directory",
                "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\weather",
                "run",
                "weather.py",
            ],
        }
    }
}

# 실제 MCP 서버들로 테스트
test_servers = [
    {
        "id": "1",
        "github_link": "https://github.com/smithery-ai/mcp-servers/tree/main/github",
        "name": "GitHub MCP Server",
        "description": "This tools provide various github features using github API",
        "category": "Code Tools",
        "tags": ["github", "code"],
    },
    {
        "id": "2",
        "github_link": "https://github.com/big-omega/mem0-mcp/tree/main/node/mem0",
        "name": "Mem0 MCP Server",
        "description": "This toolkit allows AI to access the JIRA",
        "category": "Documentation",
        "tags": ["jira", "issue"],
    },
]

print("=== Starting MCP server tools extraction and insertion ===")

for server_info in test_servers:
    print(f"\n{'='*60}")
    print(f"처리 중: {server_info['name']}")
    print(f"{'='*60}")

    # Tools 추출 디버깅
    tools_dict = debug_tools_extraction(server_info["github_link"], server_info["name"])

    # MCPServer 객체 생성
    mcp_server = MCPServer(
        id=server_info["id"],
        github_link=server_info["github_link"],
        name=server_info["name"],
        description=server_info["description"],
        transport=TransportType.sse,
        category=server_info["category"],
        tags=server_info["tags"],
        status="active",
        config=example_config,
    )

    # Tools 변환 및 저장
    if tools_dict:
        tools = convert_dict_to_mcp_tools(tools_dict)
        mcp_server.tools = tools
        print(f"✅ {len(tools)}개의 tools 변환 완료")
    else:
        mcp_server.tools = []
        print("⚠️  Tools가 없습니다")

    # DB에 저장
    try:
        dao.create_mcp(mcp_server)
        print(f"✅ DB 저장 완료")
    except Exception as e:
        print(f"❌ DB 저장 실패: {e}")

dao.close()
print("\n=== MCP server data insertion completed! ===")
