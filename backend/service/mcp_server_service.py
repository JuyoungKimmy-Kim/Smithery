import requests
import json
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import os
from bs4 import BeautifulSoup
import subprocess
import time
import tempfile
import shutil
import socket
import struct
from backend.service.github_api_service import GitHubAPIService


class MCPServerService:
    """
    Service class providing business logic related to MCPServer and external repo parsing functions
    MCP Registry 방식을 참고하여 개선된 MCP 서버 분석 기능 제공
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize MCP server service

        Args:
            github_token (Optional[str]): GitHub Personal Access Token
        """
        self.github_api = GitHubAPIService(github_token)

        # 지원하는 파일 확장자
        self.supported_extensions = [
            ".py",
            ".ts",
            ".mjs",
            ".js",
            ".json",
            ".jsx",
            ".tsx",
        ]

        # MCP 설정 파일명
        self.mcp_config_files = [
            ".mcp.json",
            ".mcp.config.js",
            ".mcp.config.ts",
            "mcp.json",
            "mcp.config.js",
        ]

    def read_mcp_server_tool_list(self, github_link: str) -> list:
        """
        GitHub 저장소에서 MCP 서버의 tool 목록을 읽어옵니다.
        MCP Registry 방식을 참고하여 개선된 분석 수행

        Args:
            github_link (str): GitHub 저장소 링크

        Returns:
            list: Tool 목록
        """
        try:
            # GitHub 링크에서 저장소 정보 추출
            repo_info = self._parse_github_url(github_link)
            if not repo_info:
                return []

            owner, repo, path = repo_info

            # 1단계: MCP 설정 파일 찾기
            mcp_config = self._find_mcp_config_files(owner, repo, path)

            # 2단계: 설정 파일에서 entry point 및 tools 정보 추출
            entry_points = self._extract_entry_points_from_config(
                mcp_config, owner, repo
            )

            # 3단계: 소스 파일에서 tools 추출
            source_files = self._find_source_files(owner, repo, path)
            tools = self._extract_tools_from_source_files(source_files, owner, repo)

            # 4단계: 설정 파일에서 정의된 tools 추가
            config_tools = self._extract_tools_from_config_files(
                mcp_config, owner, repo
            )
            tools.extend(config_tools)

            # 중복 제거 및 정리
            return self._deduplicate_tools(tools)

        except Exception as e:
            print(f"Error reading MCP server tools: {e}")
            return []

    def read_mcp_server_resource_list(self, github_link: str) -> list:
        """
        GitHub 저장소에서 MCP 서버의 resource 목록을 읽어옵니다.
        MCP Registry 방식을 참고하여 개선된 분석 수행

        Args:
            github_link (str): GitHub 저장소 링크

        Returns:
            list: Resource 목록
        """
        try:
            # GitHub 링크에서 저장소 정보 추출
            repo_info = self._parse_github_url(github_link)
            if not repo_info:
                return []

            owner, repo, path = repo_info

            # 1단계: MCP 설정 파일 찾기
            mcp_config = self._find_mcp_config_files(owner, repo, path)

            # 2단계: 소스 파일에서 resources 추출
            source_files = self._find_source_files(owner, repo, path)
            resources = self._extract_resources_from_source_files(
                source_files, owner, repo
            )

            # 3단계: 설정 파일에서 정의된 resources 추가
            config_resources = self._extract_resources_from_config_files(
                mcp_config, owner, repo
            )
            resources.extend(config_resources)

            # 중복 제거 및 정리
            return self._deduplicate_resources(resources)

        except Exception as e:
            print(f"Error reading MCP server resources: {e}")
            return []

    def _find_mcp_config_files(self, owner: str, repo: str, path: str = "") -> list:
        """
        MCP 설정 파일들을 찾습니다.

        Args:
            owner (str): GitHub 저장소 소유자
            repo (str): GitHub 저장소명
            path (str): 서브디렉토리 경로

        Returns:
            list: MCP 설정 파일 목록
        """
        config_files = []

        # 루트 디렉토리에서 검색
        files = self.github_api.get_repo_files(owner, repo, path)

        for file_info in files:
            if file_info["type"] == "file":
                name = file_info.get("name", "").lower()
                if name in [f.lower() for f in self.mcp_config_files]:
                    config_files.append(file_info)

        # 상위 디렉토리에서도 검색 (package.json, pyproject.toml 등)
        if path:
            parent_files = self.github_api.get_repo_files(
                owner, repo, path.rsplit("/", 1)[0] if "/" in path else ""
            )
            for file_info in parent_files:
                if file_info["type"] == "file":
                    name = file_info.get("name", "").lower()
                    if name in [
                        "package.json",
                        "pyproject.toml",
                        "setup.py",
                        "requirements.txt",
                    ]:
                        config_files.append(file_info)

        return config_files

    def _extract_entry_points_from_config(
        self, config_files: list, owner: str, repo: str
    ) -> list:
        """
        MCP 설정 파일에서 entry point를 추출합니다.

        Args:
            config_files (list): MCP 설정 파일 목록
            owner (str): GitHub 저장소 소유자
            repo (str): GitHub 저장소명

        Returns:
            list: Entry point 목록
        """
        entry_points = []

        for file_info in config_files:
            content = self.github_api.get_file_content(owner, repo, file_info["path"])
            if not content:
                continue

            try:
                if file_info["path"].endswith(".json"):
                    config_data = json.loads(content)
                    # JSON 설정에서 entry point 찾기
                    if "entrypoint" in config_data:
                        entry_points.append(config_data["entrypoint"])
                    elif "main" in config_data:
                        entry_points.append(config_data["main"])
                else:
                    # JavaScript/TypeScript 설정 파일에서 entry point 찾기
                    entry_patterns = [
                        r'entrypoint\s*[:=]\s*["\']([^"\']+)["\']',
                        r'main\s*[:=]\s*["\']([^"\']+)["\']',
                        r'export\s+default\s*[:=]\s*["\']([^"\']+)["\']',
                    ]

                    for pattern in entry_patterns:
                        matches = re.findall(pattern, content)
                        entry_points.extend(matches)

            except Exception as e:
                print(f"Error parsing config file {file_info['path']}: {e}")

        return entry_points

    def _find_source_files(self, owner: str, repo: str, path: str = "") -> list:
        """
        소스 파일들을 찾습니다. 재귀적으로 디렉토리를 탐색합니다.

        Args:
            owner (str): GitHub 저장소 소유자
            repo (str): GitHub 저장소명
            path (str): 서브디렉토리 경로

        Returns:
            list: 소스 파일 목록
        """
        source_files = []

        def explore_directory(
            current_path: str, max_depth: int = 3, current_depth: int = 0
        ):
            """재귀적으로 디렉토리를 탐색합니다."""
            if current_depth > max_depth:
                return

            try:
                files = self.github_api.get_repo_files(owner, repo, current_path)

                for file_info in files:
                    if file_info["type"] == "file":
                        file_path = file_info.get("path", "")
                        name = file_info.get("name", "")

                        # 지원하는 확장자를 가진 파일들
                        if any(
                            file_path.endswith(ext) for ext in self.supported_extensions
                        ):
                            source_files.append(file_info)

                        # 특정 디렉토리의 파일들
                        elif any(
                            keyword in file_path.lower()
                            for keyword in [
                                "src/",
                                "tools/",
                                "resources/",
                                "lib/",
                                "dist/",
                                "main.py",
                                "index.py",
                                "server.py",
                            ]
                        ):
                            source_files.append(file_info)

                    elif file_info["type"] == "dir":
                        # 디렉토리인 경우 재귀적으로 탐색
                        dir_path = file_info.get("path", "")
                        if dir_path and current_depth < max_depth:
                            explore_directory(dir_path, max_depth, current_depth + 1)

            except Exception as e:
                print(f"Error exploring directory {current_path}: {e}")

        # 지정된 경로에서 시작하여 재귀적으로 탐색
        explore_directory(path)

        # 상위 디렉토리에서도 검색
        if path:
            parent_path = path.rsplit("/", 1)[0] if "/" in path else ""
            try:
                parent_files = self.github_api.get_repo_files(owner, repo, parent_path)

                for file_info in parent_files:
                    if file_info["type"] == "file":
                        file_path = file_info.get("path", "")
                        name = file_info.get("name", "")

                        # 주요 소스 파일들
                        if name in [
                            "main.py",
                            "index.py",
                            "server.py",
                            "app.py",
                            "index.js",
                            "server.js",
                            "app.js",
                        ]:
                            source_files.append(file_info)
                        elif any(
                            file_path.endswith(ext) for ext in self.supported_extensions
                        ):
                            source_files.append(file_info)
            except Exception as e:
                print(f"Error exploring parent directory {parent_path}: {e}")

        return source_files

    def _extract_tools_from_source_files(
        self, source_files: list, owner: str, repo: str
    ) -> list:
        """
        소스 파일들에서 tools를 추출합니다.

        Args:
            source_files (list): 소스 파일 목록
            owner (str): GitHub 저장소 소유자
            repo (str): GitHub 저장소명

        Returns:
            list: Tool 목록
        """
        tools = []

        for file_info in source_files:
            content = self.github_api.get_file_content(owner, repo, file_info["path"])
            if not content:
                continue

            file_tools = self._extract_tools_from_file(content, file_info["path"])
            tools.extend(file_tools)

        return tools

    def _extract_resources_from_source_files(
        self, source_files: list, owner: str, repo: str
    ) -> list:
        """
        소스 파일들에서 resources를 추출합니다.

        Args:
            source_files (list): 소스 파일 목록
            owner (str): GitHub 저장소 소유자
            repo (str): GitHub 저장소명

        Returns:
            list: Resource 목록
        """
        resources = []

        for file_info in source_files:
            content = self.github_api.get_file_content(owner, repo, file_info["path"])
            if not content:
                continue

            file_resources = self._extract_resources_from_file(
                content, file_info["path"]
            )
            resources.extend(file_resources)

        return resources

    def _extract_tools_from_config_files(
        self, config_files: list, owner: str, repo: str
    ) -> list:
        """
        설정 파일들에서 tools를 추출합니다.

        Args:
            config_files (list): 설정 파일 목록
            owner (str): GitHub 저장소 소유자
            repo (str): GitHub 저장소명

        Returns:
            list: Tool 목록
        """
        tools = []

        for file_info in config_files:
            content = self.github_api.get_file_content(owner, repo, file_info["path"])
            if not content:
                continue

            file_tools = self._extract_tools_from_file(content, file_info["path"])
            tools.extend(file_tools)

        return tools

    def _extract_resources_from_config_files(
        self, config_files: list, owner: str, repo: str
    ) -> list:
        """
        설정 파일들에서 resources를 추출합니다.

        Args:
            config_files (list): 설정 파일 목록
            owner (str): GitHub 저장소 소유자
            repo (str): GitHub 저장소명

        Returns:
            list: Resource 목록
        """
        resources = []

        for file_info in config_files:
            content = self.github_api.get_file_content(owner, repo, file_info["path"])
            if not content:
                continue

            file_resources = self._extract_resources_from_file(
                content, file_info["path"]
            )
            resources.extend(file_resources)

        return resources

    def _deduplicate_tools(self, tools: list) -> list:
        """
        중복된 tools를 제거합니다.

        Args:
            tools (list): Tool 목록

        Returns:
            list: 중복 제거된 Tool 목록
        """
        seen = set()
        unique_tools = []

        for tool in tools:
            tool_key = f"{tool.get('name', '')}_{tool.get('file', '')}"
            if tool_key not in seen:
                seen.add(tool_key)
                unique_tools.append(tool)

        return unique_tools

    def _deduplicate_resources(self, resources: list) -> list:
        """
        중복된 resources를 제거합니다.

        Args:
            resources (list): Resource 목록

        Returns:
            list: 중복 제거된 Resource 목록
        """
        seen = set()
        unique_resources = []

        for resource in resources:
            resource_key = f"{resource.get('name', '')}_{resource.get('file', '')}"
            if resource_key not in seen:
                seen.add(resource_key)
                unique_resources.append(resource)

        return unique_resources

    def _parse_github_url(self, github_link: str) -> Optional[tuple]:
        """
        GitHub URL에서 owner, repo, path 정보를 추출합니다.

        Args:
            github_link (str): GitHub 저장소 링크

        Returns:
            Optional[tuple]: (owner, repo, path) 튜플 또는 None
        """
        try:
            parsed = urlparse(github_link)
            if "github.com" in parsed.netloc:
                path_parts = parsed.path.strip("/").split("/")
                if len(path_parts) >= 2:
                    owner = path_parts[0]
                    repo = path_parts[1]

                    # 서브디렉토리 경로 추출 (tree/main/ 이후 부분)
                    path = ""
                    if len(path_parts) > 4 and path_parts[2] == "tree":
                        path = "/".join(path_parts[4:])

                    return owner, repo, path
        except Exception as e:
            print(f"Error parsing GitHub URL: {e}")
        return None

    def _is_valid_mcp_tool(self, tool_name: str, content: str, file_path: str) -> bool:
        """
        추출된 tool이 실제 MCP tool인지 검증합니다.

        Args:
            tool_name (str): Tool 이름
            content (str): 파일 내용
            file_path (str): 파일 경로

        Returns:
            bool: 유효한 MCP tool인지 여부
        """
        # MCP 관련 키워드들
        mcp_keywords = [
            "mcp",
            "tool",
            "server",
            "protocol",
            "modelcontextprotocol",
            "defineTool",
            "@mcp.tool",
            "@tool",
            "Tool(",
            "new Tool",
            "setRequestHandler",
            "ListToolsRequestSchema",
            "CallToolRequestSchema",
        ]

        # 파일 경로에서 MCP 관련 키워드 확인
        if any(keyword in file_path.lower() for keyword in ["mcp", "tool", "server"]):
            return True

        # tool_name이 너무 일반적인 이름인지 확인
        common_names = [
            "main",
            "index",
            "app",
            "server",
            "init",
            "start",
            "run",
            "create",
            "get",
            "set",
            "add",
            "remove",
            "update",
            "delete",
        ]
        if tool_name.lower() in common_names:
            # 일반적인 이름인 경우 더 엄격한 검증 필요
            pass
        else:
            # 특별한 이름인 경우 MCP 관련 키워드가 있으면 허용
            if any(keyword in content.lower() for keyword in mcp_keywords):
                return True

        # 함수 정의 주변에서 MCP 관련 키워드 확인
        try:
            # tool_name 주변의 코드를 찾기
            tool_pattern = rf"\b{tool_name}\b"
            matches = list(re.finditer(tool_pattern, content, re.IGNORECASE))

            for match in matches:
                start = max(0, match.start() - 300)
                end = min(len(content), match.end() + 300)
                context = content[start:end]

                # 컨텍스트에서 MCP 관련 키워드 확인
                if any(keyword in context.lower() for keyword in mcp_keywords):
                    return True

                # Tool 객체 정의 확인
                if "Tool" in context and "name" in context:
                    return True

                # 서버 핸들러 등록 확인
                if "setRequestHandler" in context:
                    return True

        except Exception as e:
            print(f"Error validating MCP tool {tool_name}: {e}")

        return False

    def _extract_tools_from_file(self, content: str, file_path: str) -> list:
        """
        파일 내용에서 Tool 정의를 추출합니다.
        MCP Registry 방식을 참고하여 개선된 패턴 매칭

        Args:
            content (str): 파일 내용
            file_path (str): 파일 경로

        Returns:
            list: Tool 목록
        """
        tools = []
        try:
            # Python 파일에서 Tool 정의 찾기
            if file_path.endswith(".py"):
                tool_patterns = [
                    # 클래스 기반 Tool 정의
                    r"class\s+(\w+Tool)\s*:",
                    r"class\s+(\w+)\s*\(.*Tool.*\)\s*:",
                    # 데코레이터 기반 Tool 정의
                    r"@tool\s*\([^)]*\)\s*def\s+(\w+)",
                    r"@mcp\.tool\s*\([^)]*\)\s*async\s+def\s+(\w+)",
                    r"@mcp\.tool\s*\([^)]*\)\s*def\s+(\w+)",
                    r"@mcp\.tools\s*\([^)]*\)\s*async\s+def\s+(\w+)",
                    r"@mcp\.tools\s*\([^)]*\)\s*def\s+(\w+)",
                    r"@server\.tool\s*\([^)]*\)\s*async\s+def\s+(\w+)",
                    r"@server\.tool\s*\([^)]*\)\s*def\s+(\w+)",
                    # 함수 기반 Tool 정의
                    r"def\s+(\w+)\s*\([^)]*\)\s*->\s*Tool[^:]*:",
                    r"async\s+def\s+(\w+)\s*\([^)]*\)\s*->\s*Tool[^:]*:",
                    # Tool 객체 생성
                    r'Tool\s*\(\s*name\s*=\s*["\']([^"\']+)["\']',
                    r'Tool\s*\(\s*["\']([^"\']+)["\']',
                ]

                for pattern in tool_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        tool_info = {
                            "name": match,
                            "file": file_path,
                            "type": "tool",
                            "language": "python",
                        }
                        tools.append(tool_info)

            # JavaScript/TypeScript 파일에서 Tool 정의 찾기
            elif file_path.endswith((".js", ".ts", ".mjs", ".jsx", ".tsx")):
                tool_patterns = [
                    # 1. MCP 데코레이터 기반 정의
                    r"@mcp\.tool\s*\([^)]*\)\s*(?:async\s+)?function\s+(\w+)",
                    r"@mcp\.tool\s*\([^)]*\)\s*const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
                    r"@mcp\.tool\s*\([^)]*\)\s*export\s+(?:async\s+)?function\s+(\w+)",
                    r"@mcp\.tool\s*\([^)]*\)\s*export\s+const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
                    # 2. defineTool 사용
                    r'defineTool\s*\(\s*["\']([^"\']+)["\']',
                    r'defineTool\s*\(\s*\{[^}]*name\s*:\s*["\']([^"\']+)["\']',
                    # 3. Tool 객체 정의 (Mem0 방식)
                    r'const\s+(\w+)\s*:\s*Tool\s*=\s*\{[^}]*name\s*:\s*["\']([^"\']+)["\']',
                    r'const\s+(\w+)\s*:\s*Tool\s*=\s*\{[^}]*name\s*:\s*["\']([^"\']+)["\']',
                    r'const\s+(\w+)_TOOL\s*:\s*Tool\s*=\s*\{[^}]*name\s*:\s*["\']([^"\']+)["\']',
                    r'const\s+(\w+)_TOOL\s*:\s*Tool\s*=\s*\{[^}]*name\s*:\s*["\']([^"\']+)["\']',
                    # 4. Tool 객체 생성
                    r'Tool\s*\(\s*["\']([^"\']+)["\']',
                    r'new\s+Tool\s*\(\s*["\']([^"\']+)["\']',
                    # 5. MCP 서버에서 export된 함수들 (더 구체적인 패턴)
                    r"export\s+(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*:\s*Promise<[^>]*>",
                    r"export\s+const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*:\s*Promise<[^>]*>",
                    # 6. MCP 관련 키워드가 포함된 함수들
                    r"(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*mcp[^}]*\}",
                    r"const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{[^}]*mcp[^}]*\}",
                    # 7. 서버 핸들러 등록 (Mem0 방식)
                    r"server\.setRequestHandler\s*\(\s*[^,]+,\s*async\s+function\s+(\w+)",
                    r"server\.setRequestHandler\s*\(\s*[^,]+,\s*async\s+\([^)]*\)\s*=>\s*\{[^}]*(\w+)[^}]*\}",
                    # 8. Tool 이름을 직접 추출하는 패턴
                    r'name\s*:\s*["\']([^"\']+)["\']\s*,?\s*description\s*:',
                    r'name\s*:\s*["\']([^"\']+)["\']\s*,?\s*inputSchema\s*:',
                ]

                for pattern in tool_patterns:
                    matches = re.findall(
                        pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL
                    )
                    for match in matches:
                        # match가 튜플인 경우 (그룹이 여러 개인 패턴)
                        if isinstance(match, tuple):
                            # 첫 번째 그룹이 함수명, 두 번째 그룹이 tool 이름
                            if len(match) >= 2 and match[1]:
                                tool_name = match[1]
                            else:
                                tool_name = match[0]
                        else:
                            tool_name = match

                        # 실제 MCP tool인지 확인 (더 엄격한 검증)
                        if self._is_valid_mcp_tool(tool_name, content, file_path):
                            tool_info = {
                                "name": tool_name,
                                "file": file_path,
                                "type": "tool",
                                "language": (
                                    "javascript"
                                    if file_path.endswith(".js")
                                    else "typescript"
                                ),
                            }
                            tools.append(tool_info)

            # JSON 파일에서 tool 정의 찾기
            elif file_path.endswith(".json"):
                try:
                    json_data = json.loads(content)
                    if "tools" in json_data:
                        for tool in json_data["tools"]:
                            tools.append(
                                {
                                    "name": tool.get("name", "Unknown"),
                                    "description": tool.get("description", ""),
                                    "file": file_path,
                                    "type": "tool",
                                    "language": "json",
                                }
                            )
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            print(f"Error extracting tools from {file_path}: {e}")

        return tools

    def _extract_resources_from_file(self, content: str, file_path: str) -> list:
        """
        파일 내용에서 Resource 정의를 추출합니다.
        MCP Registry 방식을 참고하여 개선된 패턴 매칭

        Args:
            content (str): 파일 내용
            file_path (str): 파일 경로

        Returns:
            list: Resource 목록
        """
        resources = []
        try:
            # Python 파일에서 Resource 정의 찾기
            if file_path.endswith(".py"):
                resource_patterns = [
                    # 클래스 기반 Resource 정의
                    r"class\s+(\w+Resource)\s*:",
                    r"class\s+(\w+)\s*\(.*Resource.*\)\s*:",
                    # 데코레이터 기반 Resource 정의
                    r"@resource\s*\([^)]*\)\s*def\s+(\w+)",
                    r"@mcp\.resource\s*\([^)]*\)\s*async\s+def\s+(\w+)",
                    r"@mcp\.resource\s*\([^)]*\)\s*def\s+(\w+)",
                    r"@mcp\.resources\s*\([^)]*\)\s*async\s+def\s+(\w+)",
                    r"@mcp\.resources\s*\([^)]*\)\s*def\s+(\w+)",
                    r"@server\.resource\s*\([^)]*\)\s*async\s+def\s+(\w+)",
                    r"@server\.resource\s*\([^)]*\)\s*def\s+(\w+)",
                    # 함수 기반 Resource 정의
                    r"def\s+(\w+)\s*\([^)]*\)\s*->\s*Resource[^:]*:",
                    r"async\s+def\s+(\w+)\s*\([^)]*\)\s*->\s*Resource[^:]*:",
                    # Resource 객체 생성
                    r'Resource\s*\(\s*name\s*=\s*["\']([^"\']+)["\']',
                    r'Resource\s*\(\s*["\']([^"\']+)["\']',
                ]

                for pattern in resource_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        resource_info = {
                            "name": match,
                            "file": file_path,
                            "type": "resource",
                            "language": "python",
                        }
                        resources.append(resource_info)

            # JavaScript/TypeScript 파일에서 Resource 정의 찾기
            elif file_path.endswith((".js", ".ts", ".mjs", ".jsx", ".tsx")):
                resource_patterns = [
                    # 함수 기반 Resource 정의
                    r"function\s+(\w+)\s*\([^)]*\)\s*{",
                    r"const\s+(\w+)\s*=\s*\([^)]*\)\s*=>",
                    r"async\s+function\s+(\w+)\s*\([^)]*\)\s*{",
                    r"const\s+(\w+)\s*=\s*async\s*\([^)]*\)\s*=>",
                    # defineResource 사용
                    r'defineResource\s*\(\s*["\']([^"\']+)["\']',
                    r'defineResource\s*\(\s*\{[^}]*name\s*:\s*["\']([^"\']+)["\']',
                    # export 기반 Resource 정의
                    r"export\s+(?:async\s+)?function\s+(\w+)",
                    r"export\s+const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
                    # Resource 객체 생성
                    r'Resource\s*\(\s*["\']([^"\']+)["\']',
                    r'new\s+Resource\s*\(\s*["\']([^"\']+)["\']',
                ]

                for pattern in resource_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        resource_info = {
                            "name": match,
                            "file": file_path,
                            "type": "resource",
                            "language": (
                                "javascript"
                                if file_path.endswith(".js")
                                else "typescript"
                            ),
                        }
                        resources.append(resource_info)

            # JSON 파일에서 resource 정의 찾기
            elif file_path.endswith(".json"):
                try:
                    json_data = json.loads(content)
                    if "resources" in json_data:
                        for resource in json_data["resources"]:
                            resources.append(
                                {
                                    "name": resource.get("name", "Unknown"),
                                    "description": resource.get("description", ""),
                                    "file": file_path,
                                    "type": "resource",
                                    "language": "json",
                                }
                            )
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            print(f"Error extracting resources from {file_path}: {e}")

        return resources
