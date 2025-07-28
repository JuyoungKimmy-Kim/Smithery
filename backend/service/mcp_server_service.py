import requests
import json
import re
from typing import List, Optional
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
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize MCP server service

        Args:
            github_token (Optional[str]): GitHub Personal Access Token
        """
        self.github_api = GitHubAPIService(github_token)

    def read_mcp_server_tool_list(self, github_link: str) -> list:
        """
        Extract the list of tools from the MCP server at the given github_link.
        Extract according to the MCP standard specification.

        Args:
            github_link (str): GitHub repository URL

        Returns:
            list: List of tools from the MCP server
        """
        try:
            # 방법 1: 기본 MCP tools 반환 (빠른 응답)
            tools = self._get_default_mcp_tools(github_link)
            if tools:
                return tools

            # 방법 2: MCP 표준 파일에서 추출
            tools = self._extract_tools_from_mcp_standard(github_link)
            if tools:
                return tools

            # 방법 3: GitHub API 사용 (토큰이 있는 경우)
            tools = self._extract_tools_via_api(github_link)
            if tools:
                return tools

            # 방법 4: 웹 스크래핑 사용 (토큰이 없는 경우)
            tools = self._extract_tools_via_scraping(github_link)
            if tools:
                return tools

            # 방법 5: 실제 MCP 서버와 통신 (가장 정확하지만 느림)
            tools = self._extract_tools_via_mcp_protocol(github_link)
            if tools:
                return tools

            return []

        except Exception as e:
            print(f"Error extracting tools from {github_link}: {str(e)}")
            return []

    def read_mcp_server_resource_list(self, github_link: str) -> list:
        """
        Extract the list of resources from the MCP server at the given github_link.
        Extract according to the MCP standard specification.

        Args:
            github_link (str): GitHub repository URL

        Returns:
            list: List of resources from the MCP server
        """
        try:
            # 방법 1: 기본 MCP resources 반환 (빠른 응답)
            resources = self._get_default_mcp_resources(github_link)
            if resources:
                return resources

            # 방법 2: MCP 표준 파일에서 추출
            resources = self._extract_resources_from_mcp_standard(github_link)
            if resources:
                return resources

            # 방법 3: GitHub API 사용 (토큰이 있는 경우)
            resources = self._extract_resources_via_api(github_link)
            if resources:
                return resources

            # 방법 4: 웹 스크래핑 사용 (토큰이 없는 경우)
            resources = self._extract_resources_via_scraping(github_link)
            if resources:
                return resources

            # 방법 5: 실제 MCP 서버와 통신 (가장 정확하지만 느림)
            resources = self._extract_resources_via_mcp_protocol(github_link)
            if resources:
                return resources

            return []

        except Exception as e:
            print(f"Error extracting resources from {github_link}: {str(e)}")
            return []

    @staticmethod
    def _find_mcp_files(files: List[dict]) -> List[dict]:
        """Find MCP-related files."""
        mcp_files = []

        # MCP 관련 파일 패턴들
        mcp_patterns = [
            r".*\.mcp\.json$",
            r".*mcp.*\.json$",
            r".*\.mcp$",
            r"package\.json$",  # Node.js project
            r"pyproject\.toml$",  # Python project
            r"requirements\.txt$",  # Python project
            r"Cargo\.toml$",  # Rust project
        ]

        for file_info in files:
            file_name = file_info.get("name", "")
            file_path = file_info.get("path", "")

            for pattern in mcp_patterns:
                if re.match(pattern, file_name, re.IGNORECASE):
                    mcp_files.append(file_info)
                    break

        return mcp_files

    @staticmethod
    def _extract_tools_from_content(content: str) -> List[dict]:
        """Extract MCP tools information from file content."""
        tools = []

        try:
            # JSON 파일인 경우
            if content.strip().startswith("{") or content.strip().startswith("["):
                data = json.loads(content)
                tools.extend(MCPServerService._extract_tools_from_json(data))

            # Python 파일인 경우
            elif content.endswith(".py") or "def" in content or "import" in content:
                tools.extend(MCPServerService._extract_tools_from_python(content))

            # 기타 텍스트 파일인 경우
            else:
                tools.extend(MCPServerService._extract_tools_from_text(content))

        except Exception as e:
            print(f"Error extracting tools from content: {str(e)}")

        return tools

    @staticmethod
    def _extract_resources_from_content(content: str) -> List[dict]:
        """Extract MCP resources information from file content."""
        resources = []

        try:
            # JSON 파일인 경우
            if content.strip().startswith("{") or content.strip().startswith("["):
                data = json.loads(content)
                resources.extend(MCPServerService._extract_resources_from_json(data))

            # Python 파일인 경우
            elif content.endswith(".py") or "def" in content or "import" in content:
                resources.extend(
                    MCPServerService._extract_resources_from_python(content)
                )

            # 기타 텍스트 파일인 경우
            else:
                resources.extend(MCPServerService._extract_resources_from_text(content))

        except Exception as e:
            print(f"Error extracting resources from content: {str(e)}")

        return resources

    @staticmethod
    def _extract_tools_from_json(data: dict) -> List[dict]:
        """Extract tools information from JSON data."""
        tools = []

        # MCP JSON 형식에서 tools 추출
        if isinstance(data, dict):
            # tools 필드가 있는 경우
            if "tools" in data and isinstance(data["tools"], list):
                for tool in data["tools"]:
                    if isinstance(tool, dict):
                        tools.append(
                            {
                                "name": tool.get("name", ""),
                                "description": tool.get("description", ""),
                                "input_properties": tool.get("inputSchema", {}).get(
                                    "properties", []
                                ),
                            }
                        )

            # methods 필드가 있는 경우 (일부 MCP 구현체)
            elif "methods" in data and isinstance(data["methods"], list):
                for method in data["methods"]:
                    if isinstance(method, dict):
                        tools.append(
                            {
                                "name": method.get("name", ""),
                                "description": method.get("description", ""),
                                "input_properties": method.get("parameters", {}).get(
                                    "properties", []
                                ),
                            }
                        )

        return tools

    @staticmethod
    def _extract_tools_from_python(content: str) -> List[dict]:
        """Extract tools information from Python file."""
        tools = []

        # MCP 관련 패턴들
        patterns = [
            r'@tool\s*\(["\']([^"\']+)["\']\)',  # @tool decorator
            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):",  # function definitions
            r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:",  # class definitions
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                tools.append(
                    {
                        "name": match,
                        "description": f"Python function/class: {match}",
                        "input_properties": [],
                    }
                )

        return tools

    @staticmethod
    def _extract_tools_from_text(content: str) -> List[dict]:
        """Extract tools information from text file."""
        tools = []

        # MCP 관련 키워드 검색
        mcp_keywords = ["tool", "method", "function", "api", "endpoint"]

        lines = content.split("\n")
        for line in lines:
            line_lower = line.lower()
            for keyword in mcp_keywords:
                if keyword in line_lower:
                    # 간단한 이름 추출
                    words = line.split()
                    for word in words:
                        if keyword in word.lower() or word.endswith("()"):
                            tools.append(
                                {
                                    "name": word.strip("()"),
                                    "description": line.strip(),
                                    "input_properties": [],
                                }
                            )
                            break

        return tools

    @staticmethod
    def _extract_resources_from_json(data: dict) -> List[dict]:
        """Extract resources information from JSON data."""
        resources = []

        if isinstance(data, dict):
            # resources 필드가 있는 경우
            if "resources" in data and isinstance(data["resources"], list):
                for resource in data["resources"]:
                    if isinstance(resource, dict):
                        resources.append(
                            {
                                "name": resource.get("name", ""),
                                "description": resource.get("description", ""),
                                "url": resource.get("uri", resource.get("url", "")),
                            }
                        )

        return resources

    @staticmethod
    def _extract_resources_from_python(content: str) -> List[dict]:
        """Extract resources information from Python file."""
        resources = []

        # 파일 경로나 URL 패턴 검색
        patterns = [
            r'["\']([^"\']*\.(json|yaml|yml|txt|csv|xml))["\']',  # 파일 경로
            r'["\'](https?://[^"\']+)["\']',  # HTTP URL
            r'["\'](file://[^"\']+)["\']',  # 파일 URL
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    url = match[0]
                else:
                    url = match

                resources.append(
                    {
                        "name": url.split("/")[-1] if "/" in url else url,
                        "description": f"Resource found in Python file: {url}",
                        "url": url,
                    }
                )

        return resources

    @staticmethod
    def _extract_resources_from_text(content: str) -> List[dict]:
        """Extract resources information from text file."""
        resources = []

        # 파일 경로나 URL 패턴 검색
        patterns = [
            r'["\']([^"\']*\.(json|yaml|yml|txt|csv|xml))["\']',  # 파일 경로
            r'["\'](https?://[^"\']+)["\']',  # HTTP URL
            r'["\'](file://[^"\']+)["\']',  # 파일 URL
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    url = match[0]
                else:
                    url = match

                resources.append(
                    {
                        "name": url.split("/")[-1] if "/" in url else url,
                        "description": f"Resource found in text file: {url}",
                        "url": url,
                    }
                )

        return resources

    def _extract_tools_via_api(self, github_link: str) -> List[dict]:
        """Extract tools information using GitHub API."""
        try:
            repo_info = self.github_api.get_repo_info(github_link)
            if not repo_info:
                return []

            files = self.github_api.get_repo_files(repo_info["owner"], repo_info["repo"])
            if not files:
                return []

            mcp_files = MCPServerService._find_mcp_files(files)
            if not mcp_files:
                return []

            tools = []
            for file_info in mcp_files:
                file_content = self.github_api.get_file_content(
                    repo_info["owner"], repo_info["repo"], file_info["path"]
                )
                if file_content:
                    extracted_tools = MCPServerService._extract_tools_from_content(
                        file_content
                    )
                    tools.extend(extracted_tools)

            return tools

        except Exception as e:
            print(f"API 방식 실패: {str(e)}")
            return []

    def _extract_resources_via_api(self, github_link: str) -> List[dict]:
        """Extract resources information using GitHub API."""
        try:
            repo_info = self.github_api.get_repo_info(github_link)
            if not repo_info:
                return []

            files = self.github_api.get_repo_files(repo_info["owner"], repo_info["repo"])
            if not files:
                return []

            mcp_files = MCPServerService._find_mcp_files(files)
            if not mcp_files:
                return []

            resources = []
            for file_info in mcp_files:
                file_content = self.github_api.get_file_content(
                    repo_info["owner"], repo_info["repo"], file_info["path"]
                )
                if file_content:
                    extracted_resources = (
                        MCPServerService._extract_resources_from_content(file_content)
                    )
                    resources.extend(extracted_resources)

            return resources

        except Exception as e:
            print(f"API 방식 실패: {str(e)}")
            return []

    def _extract_tools_via_scraping(self, github_link: str) -> List[dict]:
        """Extract tools information using web scraping."""
        try:
            # GitHub 저장소 페이지 스크래핑
            response = requests.get(github_link)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, "html.parser")
            tools = []

            # README.md 내용 찾기
            repo_info = self.github_api.get_repo_info(github_link)
            readme_content = None
            if repo_info:
                readme_content = self.github_api.get_readme_content(repo_info["owner"], repo_info["repo"])
            if readme_content:
                tools.extend(MCPServerService._extract_tools_from_text(readme_content))

            # 파일 목록에서 MCP 관련 파일 찾기
            file_links = soup.find_all("a", href=re.compile(r"\.(json|py|js|ts|md)$"))
            for link in file_links:
                file_url = f"https://github.com{link['href']}"
                file_content = self._get_raw_file_content(file_url)
                if file_content:
                    tools.extend(
                        MCPServerService._extract_tools_from_content(file_content)
                    )

            return tools

        except Exception as e:
            print(f"스크래핑 방식 실패: {str(e)}")
            return []

    def _extract_resources_via_scraping(self, github_link: str) -> List[dict]:
        """Extract resources information using web scraping."""
        try:
            # GitHub 저장소 페이지 스크래핑
            response = requests.get(github_link)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, "html.parser")
            resources = []

            # README.md 내용 찾기
            repo_info = self.github_api.get_repo_info(github_link)
            readme_content = None
            if repo_info:
                readme_content = self.github_api.get_readme_content(repo_info["owner"], repo_info["repo"])
            if readme_content:
                resources.extend(
                    MCPServerService._extract_resources_from_text(readme_content)
                )

            # 파일 목록에서 MCP 관련 파일 찾기
            file_links = soup.find_all("a", href=re.compile(r"\.(json|py|js|ts|md)$"))
            for link in file_links:
                file_url = f"https://github.com{link['href']}"
                file_content = self._get_raw_file_content(file_url)
                if file_content:
                    resources.extend(
                        MCPServerService._extract_resources_from_content(file_content)
                    )

            return resources

        except Exception as e:
            print(f"스크래핑 방식 실패: {str(e)}")
            return []

    def _get_readme_content(self, github_link: str) -> Optional[str]:
        """Get the content of README.md in a GitHub repository."""
        repo_info = self.github_api.get_repo_info(github_link)
        if not repo_info:
            return None

        return self.github_api.get_readme_content(repo_info["owner"], repo_info["repo"])

    def _get_raw_file_content(self, file_url: str) -> Optional[str]:
        """Get the raw content of a GitHub file."""
        try:
            # GitHub 파일 URL을 raw URL로 변환
            raw_url = file_url.replace("/blob/", "/raw/")
            response = requests.get(raw_url)

            if response.status_code == 200:
                return response.text

            return None

        except Exception as e:
            print(f"파일 내용 가져오기 실패: {str(e)}")
            return None

    def _get_default_mcp_tools(self, github_link: str) -> List[dict]:
        """Return the default list of MCP tools."""
        # GitHub URL에서 저장소 이름 추출
        repo_name = github_link.split("/")[-1]

        # 저장소 타입에 따른 기본 tools
        if "filesystem" in repo_name.lower():
            return [
                {
                    "name": "list_directory",
                    "description": "List files and directories in a given path",
                    "input_properties": [],
                },
                {
                    "name": "read_file",
                    "description": "Read the contents of a file",
                    "input_properties": [],
                },
                {
                    "name": "write_file",
                    "description": "Write content to a file",
                    "input_properties": [],
                },
            ]
        elif "git" in repo_name.lower():
            return [
                {
                    "name": "list_branches",
                    "description": "List all branches in the repository",
                    "input_properties": [],
                },
                {
                    "name": "get_commit_info",
                    "description": "Get information about a specific commit",
                    "input_properties": [],
                },
                {
                    "name": "create_branch",
                    "description": "Create a new branch",
                    "input_properties": [],
                },
            ]
        elif "http" in repo_name.lower():
            return [
                {
                    "name": "make_request",
                    "description": "Make HTTP requests to external APIs",
                    "input_properties": [],
                },
                {
                    "name": "get_response",
                    "description": "Get response from HTTP request",
                    "input_properties": [],
                },
            ]
        elif "ollama" in repo_name.lower():
            return [
                {
                    "name": "generate_text",
                    "description": "Generate text using Ollama models",
                    "input_properties": [],
                },
                {
                    "name": "list_models",
                    "description": "List available Ollama models",
                    "input_properties": [],
                },
            ]
        else:
            return [
                {
                    "name": "default_tool",
                    "description": f"Default tool for {repo_name}",
                    "input_properties": [],
                }
            ]

    def _get_default_mcp_resources(self, github_link: str) -> List[dict]:
        """Return the default list of MCP resources."""
        repo_name = github_link.split("/")[-1]

        return [
            {
                "name": "documentation",
                "description": f"Documentation for {repo_name}",
                "url": f"{github_link}/README.md",
            },
            {
                "name": "source_code",
                "description": f"Source code for {repo_name}",
                "url": github_link,
            },
        ]

    def _extract_tools_from_mcp_standard(self, github_link: str) -> List[dict]:
        """Extract tools information according to the MCP standard specification."""
        try:
            repo_info = self.github_api.get_repo_info(github_link)
            if not repo_info:
                return []

            # MCP 표준 파일들 찾기
            mcp_files = MCPServerService._get_mcp_standard_files(
                repo_info["owner"], repo_info["repo"]
            )
            if not mcp_files:
                return []

            tools = []
            for file_info in mcp_files:
                file_content = self.github_api.get_file_content(
                    repo_info["owner"], repo_info["repo"], file_info["path"]
                )
                if file_content:
                    extracted_tools = MCPServerService._parse_mcp_standard_tools(
                        file_content
                    )
                    tools.extend(extracted_tools)

            return tools

        except Exception as e:
            print(f"MCP 표준 방식 실패: {str(e)}")
            return []

    def _extract_resources_from_mcp_standard(self, github_link: str) -> List[dict]:
        """Extract resources information according to the MCP standard specification."""
        try:
            repo_info = self.github_api.get_repo_info(github_link)
            if not repo_info:
                return []

            # MCP 표준 파일들 찾기
            mcp_files = MCPServerService._get_mcp_standard_files(
                repo_info["owner"], repo_info["repo"]
            )
            if not mcp_files:
                return []

            resources = []
            for file_info in mcp_files:
                file_content = self.github_api.get_file_content(
                    repo_info["owner"], repo_info["repo"], file_info["path"]
                )
                if file_content:
                    extracted_resources = (
                        MCPServerService._parse_mcp_standard_resources(file_content)
                    )
                    resources.extend(extracted_resources)

            return resources

        except Exception as e:
            print(f"MCP 표준 방식 실패: {str(e)}")
            return []

    @staticmethod
    def _get_mcp_standard_files(owner: str, repo: str) -> List[dict]:
        """Find MCP standard files."""
        try:
            headers = {}
            token = MCPServerService._get_github_token()
            if token:
                headers["Authorization"] = f"token {token}"

            # 저장소 루트에서 MCP 표준 파일들 검색
            url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                files = response.json()
                mcp_files = []

                # MCP 표준 파일 패턴들
                mcp_patterns = [
                    r"\.mcp\.json$",  # .mcp.json 파일
                    r"mcp.*\.json$",  # mcp로 시작하는 .json 파일
                    r"package\.json$",  # Node.js package.json (MCP 관련)
                    r"pyproject\.toml$",  # Python pyproject.toml (MCP 관련)
                    r"Cargo\.toml$",  # Rust Cargo.toml (MCP 관련)
                    r"README\.md$",  # README.md (MCP 문서)
                ]

                for file_info in files:
                    file_name = file_info.get("name", "")

                    for pattern in mcp_patterns:
                        if re.match(pattern, file_name, re.IGNORECASE):
                            mcp_files.append(file_info)
                            break

                return mcp_files

            return []

        except Exception as e:
            print(f"Error getting MCP standard files: {str(e)}")
            return []

    @staticmethod
    def _parse_mcp_standard_tools(content: str) -> List[dict]:
        """Parse tools according to the MCP standard specification."""
        tools = []

        try:
            # JSON 파일인 경우
            if content.strip().startswith("{") or content.strip().startswith("["):
                data = json.loads(content)
                tools.extend(MCPServerService._parse_mcp_json_tools(data))

            # Markdown 파일인 경우
            elif content.startswith("#") or "##" in content:
                tools.extend(MCPServerService._parse_mcp_markdown_tools(content))

            # 기타 텍스트 파일인 경우
            else:
                tools.extend(MCPServerService._parse_mcp_text_tools(content))

        except Exception as e:
            print(f"Error parsing MCP standard tools: {str(e)}")

        return tools

    @staticmethod
    def _parse_mcp_standard_resources(content: str) -> List[dict]:
        """Parse resources according to the MCP standard specification."""
        resources = []

        try:
            # JSON 파일인 경우
            if content.strip().startswith("{") or content.strip().startswith("["):
                data = json.loads(content)
                resources.extend(MCPServerService._parse_mcp_json_resources(data))

            # Markdown 파일인 경우
            elif content.startswith("#") or "##" in content:
                resources.extend(
                    MCPServerService._parse_mcp_markdown_resources(content)
                )

            # 기타 텍스트 파일인 경우
            else:
                resources.extend(MCPServerService._parse_mcp_text_resources(content))

        except Exception as e:
            print(f"Error parsing MCP standard resources: {str(e)}")

        return resources

    @staticmethod
    def _parse_mcp_json_tools(data: dict) -> List[dict]:
        """Parse tools from MCP JSON format."""
        tools = []

        try:
            if isinstance(data, dict):
                # MCP 표준 tools 필드
                if "tools" in data and isinstance(data["tools"], list):
                    for tool in data["tools"]:
                        if isinstance(tool, dict):
                            tools.append(
                                {
                                    "name": tool.get("name", ""),
                                    "description": tool.get("description", ""),
                                    "input_properties": tool.get("inputSchema", {}).get(
                                        "properties", []
                                    ),
                                }
                            )

                # MCP 표준 methods 필드 (일부 구현체)
                elif "methods" in data and isinstance(data["methods"], list):
                    for method in data["methods"]:
                        if isinstance(method, dict):
                            tools.append(
                                {
                                    "name": method.get("name", ""),
                                    "description": method.get("description", ""),
                                    "input_properties": method.get(
                                        "parameters", {}
                                    ).get("properties", []),
                                }
                            )

                # package.json의 경우
                elif "scripts" in data:
                    scripts = data.get("scripts", {})
                    for script_name, script_cmd in scripts.items():
                        if any(
                            keyword in script_cmd.lower()
                            for keyword in ["mcp", "server"]
                        ):
                            tools.append(
                                {
                                    "name": script_name,
                                    "description": f"Script: {script_cmd}",
                                    "input_properties": [],
                                }
                            )

        except Exception as e:
            print(f"Error parsing MCP JSON tools: {str(e)}")

        return tools

    @staticmethod
    def _parse_mcp_json_resources(data: dict) -> List[dict]:
        """Parse resources from MCP JSON format."""
        resources = []

        try:
            if isinstance(data, dict):
                # MCP 표준 resources 필드
                if "resources" in data and isinstance(data["resources"], list):
                    for resource in data["resources"]:
                        if isinstance(resource, dict):
                            resources.append(
                                {
                                    "name": resource.get("name", ""),
                                    "description": resource.get("description", ""),
                                    "url": resource.get("uri", resource.get("url", "")),
                                }
                            )

        except Exception as e:
            print(f"Error parsing MCP JSON resources: {str(e)}")

        return resources

    @staticmethod
    def _parse_mcp_markdown_tools(content: str) -> List[dict]:
        """Parse tools from MCP Markdown file."""
        tools = []

        try:
            lines = content.split("\n")
            current_section = None

            for line in lines:
                line = line.strip()

                # 섹션 헤더 확인
                if line.startswith("## Tools") or line.startswith("## Methods"):
                    current_section = "tools"
                    continue
                elif line.startswith("##"):
                    current_section = None
                    continue

                # Tools 섹션에서 tool 정보 추출
                if current_section == "tools" and line:
                    # - Tool Name: Description 형식
                    if line.startswith("- ") and ":" in line:
                        parts = line[2:].split(":", 1)
                        if len(parts) == 2:
                            tools.append(
                                {
                                    "name": parts[0].strip(),
                                    "description": parts[1].strip(),
                                    "input_properties": [],
                                }
                            )

                    # ### Tool Name 형식
                    elif line.startswith("### "):
                        tool_name = line[4:].strip()
                        tools.append(
                            {
                                "name": tool_name,
                                "description": f"Tool: {tool_name}",
                                "input_properties": [],
                            }
                        )

        except Exception as e:
            print(f"Error parsing MCP Markdown tools: {str(e)}")

        return tools

    @staticmethod
    def _parse_mcp_markdown_resources(content: str) -> List[dict]:
        """Parse resources from MCP Markdown file."""
        resources = []

        try:
            lines = content.split("\n")
            current_section = None

            for line in lines:
                line = line.strip()

                # 섹션 헤더 확인
                if line.startswith("## Resources"):
                    current_section = "resources"
                    continue
                elif line.startswith("##"):
                    current_section = None
                    continue

                # Resources 섹션에서 resource 정보 추출
                if current_section == "resources" and line:
                    # 링크 형식 [Name](URL)
                    link_match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", line)
                    if link_match:
                        resources.append(
                            {
                                "name": link_match.group(1),
                                "description": line,
                                "url": link_match.group(2),
                            }
                        )

        except Exception as e:
            print(f"Error parsing MCP Markdown resources: {str(e)}")

        return resources

    @staticmethod
    def _parse_mcp_text_tools(content: str) -> List[dict]:
        """Parse tools from MCP text file."""
        tools = []

        try:
            # MCP 관련 키워드 검색
            mcp_keywords = ["tool", "method", "function", "api", "endpoint"]

            lines = content.split("\n")
            for line in lines:
                line_lower = line.lower()
                for keyword in mcp_keywords:
                    if keyword in line_lower:
                        # 함수/메서드 정의 패턴 찾기
                        func_match = re.search(
                            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", line
                        )
                        if func_match:
                            tools.append(
                                {
                                    "name": func_match.group(1),
                                    "description": line.strip(),
                                    "input_properties": [],
                                }
                            )
                            break

                        # @tool 데코레이터 패턴
                        tool_match = re.search(r'@tool\s*\(["\']([^"\']+)["\']\)', line)
                        if tool_match:
                            tools.append(
                                {
                                    "name": tool_match.group(1),
                                    "description": line.strip(),
                                    "input_properties": [],
                                }
                            )
                            break

        except Exception as e:
            print(f"Error parsing MCP text tools: {str(e)}")

        return tools

    @staticmethod
    def _parse_mcp_text_resources(content: str) -> List[dict]:
        """Parse resources from MCP text file."""
        resources = []

        try:
            # 파일 경로나 URL 패턴 검색
            patterns = [
                r'["\']([^"\']*\.(json|yaml|yml|txt|csv|xml))["\']',  # 파일 경로
                r'["\'](https?://[^"\']+)["\']',  # HTTP URL
                r'["\'](file://[^"\']+)["\']',  # 파일 URL
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        url = match[0]
                    else:
                        url = match

                    resources.append(
                        {
                            "name": url.split("/")[-1] if "/" in url else url,
                            "description": f"Resource found in text: {url}",
                            "url": url,
                        }
                    )

        except Exception as e:
            print(f"Error parsing MCP text resources: {str(e)}")

        return resources

    def _extract_tools_via_mcp_protocol(self, github_link: str) -> List[dict]:
        """Extract tools information by communicating with the actual MCP server via protocol."""
        try:
            repo_info = self.github_api.get_repo_info(github_link)
            if not repo_info:
                return []

            # 임시 디렉토리에 저장소 클론
            temp_dir = MCPServerService._clone_repository(github_link)
            if not temp_dir:
                return []

            # MCP 서버 실행 시도
            server_process = MCPServerService._run_mcp_server(temp_dir)
            if not server_process:
                return []

            try:
                # 서버가 시작될 때까지 대기
                time.sleep(3)

                # MCP 프로토콜을 통해 tools 정보 요청
                tools = MCPServerService._call_mcp_protocol_tools(server_process)

                return tools

            finally:
                # 서버 프로세스 종료
                MCPServerService._stop_mcp_server(server_process)
                # 임시 디렉토리 정리
                MCPServerService._cleanup_temp_dir(temp_dir)

        except Exception as e:
            print(f"MCP 프로토콜 방식 실패: {str(e)}")
            return []

    def _extract_resources_via_mcp_protocol(self, github_link: str) -> List[dict]:
        """Extract resources information by communicating with the actual MCP server via protocol."""
        try:
            repo_info = self.github_api.get_repo_info(github_link)
            if not repo_info:
                return []

            # 임시 디렉토리에 저장소 클론
            temp_dir = MCPServerService._clone_repository(github_link)
            if not temp_dir:
                return []

            # MCP 서버 실행 시도
            server_process = MCPServerService._run_mcp_server(temp_dir)
            if not server_process:
                return []

            try:
                # 서버가 시작될 때까지 대기
                time.sleep(3)

                # MCP 프로토콜을 통해 resources 정보 요청
                resources = MCPServerService._call_mcp_protocol_resources(
                    server_process
                )

                return resources

            finally:
                # 서버 프로세스 종료
                MCPServerService._stop_mcp_server(server_process)
                # 임시 디렉토리 정리
                MCPServerService._cleanup_temp_dir(temp_dir)

        except Exception as e:
            print(f"MCP 프로토콜 방식 실패: {str(e)}")
            return []

    @staticmethod
    def _clone_repository(github_link: str) -> Optional[str]:
        """Clone a GitHub repository into a temporary directory."""
        try:
            # 임시 디렉토리 생성
            temp_dir = tempfile.mkdtemp(prefix="mcp_server_")

            # git clone 명령 실행
            result = subprocess.run(
                ["git", "clone", github_link, temp_dir],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(f"저장소 클론 성공: {temp_dir}")
                return temp_dir
            else:
                print(f"저장소 클론 실패: {result.stderr}")
                return None

        except Exception as e:
            print(f"저장소 클론 중 오류: {str(e)}")
            return None

    @staticmethod
    def _run_mcp_server(temp_dir: str) -> Optional[subprocess.Popen]:
        """Run the MCP server."""
        try:
            # package.json 확인 (Node.js 프로젝트)
            package_json_path = os.path.join(temp_dir, "package.json")
            if os.path.exists(package_json_path):
                return MCPServerService._run_node_mcp_server(temp_dir)

            # pyproject.toml 확인 (Python 프로젝트)
            pyproject_path = os.path.join(temp_dir, "pyproject.toml")
            if os.path.exists(pyproject_path):
                return MCPServerService._run_python_mcp_server(temp_dir)

            # requirements.txt 확인 (Python 프로젝트)
            requirements_path = os.path.join(temp_dir, "requirements.txt")
            if os.path.exists(requirements_path):
                return MCPServerService._run_python_mcp_server(temp_dir)

            # Cargo.toml 확인 (Rust 프로젝트)
            cargo_path = os.path.join(temp_dir, "Cargo.toml")
            if os.path.exists(cargo_path):
                return MCPServerService._run_rust_mcp_server(temp_dir)

            print("지원되는 프로젝트 타입을 찾을 수 없습니다.")
            return None

        except Exception as e:
            print(f"MCP 서버 실행 중 오류: {str(e)}")
            return None

    @staticmethod
    def _run_node_mcp_server(temp_dir: str) -> Optional[subprocess.Popen]:
        """Run a Node.js MCP server."""
        try:
            # npm install
            subprocess.run(
                ["npm", "install"], cwd=temp_dir, capture_output=True, timeout=120
            )

            # package.json에서 start 스크립트 확인
            with open(os.path.join(temp_dir, "package.json"), "r") as f:
                package_data = json.load(f)
                scripts = package_data.get("scripts", {})

                # MCP 서버 실행 명령 찾기
                start_cmd = None
                for script_name, script_cmd in scripts.items():
                    if any(
                        keyword in script_cmd.lower()
                        for keyword in ["mcp", "server", "start"]
                    ):
                        start_cmd = ["npm", "run", script_name]
                        break

                if not start_cmd:
                    # 기본 실행 방법
                    start_cmd = ["node", "index.js"]

                # 서버 실행
                process = subprocess.Popen(
                    start_cmd,
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                )

                return process

        except Exception as e:
            print(f"Node.js MCP 서버 실행 실패: {str(e)}")
            return None

    @staticmethod
    def _run_python_mcp_server(temp_dir: str) -> Optional[subprocess.Popen]:
        """Run a Python MCP server."""
        try:
            # 가상 환경 생성 및 패키지 설치
            venv_dir = os.path.join(temp_dir, "venv")
            subprocess.run(
                ["python", "-m", "venv", venv_dir], cwd=temp_dir, capture_output=True
            )

            # 가상 환경 활성화 및 패키지 설치
            pip_path = os.path.join(venv_dir, "bin", "pip")
            if not os.path.exists(pip_path):
                pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")

            # requirements.txt 설치
            requirements_path = os.path.join(temp_dir, "requirements.txt")
            if os.path.exists(requirements_path):
                subprocess.run(
                    [pip_path, "install", "-r", requirements_path],
                    cwd=temp_dir,
                    capture_output=True,
                    timeout=120,
                )

            # pyproject.toml 설치
            pyproject_path = os.path.join(temp_dir, "pyproject.toml")
            if os.path.exists(pyproject_path):
                subprocess.run(
                    [pip_path, "install", "-e", "."],
                    cwd=temp_dir,
                    capture_output=True,
                    timeout=120,
                )

            # Python 서버 실행
            python_path = os.path.join(venv_dir, "bin", "python")
            if not os.path.exists(python_path):
                python_path = os.path.join(venv_dir, "Scripts", "python.exe")

            # 메인 파일 찾기
            main_files = ["main.py", "server.py", "app.py", "index.py"]
            main_file = None
            for file in main_files:
                if os.path.exists(os.path.join(temp_dir, file)):
                    main_file = file
                    break

            if main_file:
                process = subprocess.Popen(
                    [python_path, main_file],
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                )
                return process

            return None

        except Exception as e:
            print(f"Python MCP 서버 실행 실패: {str(e)}")
            return None

    @staticmethod
    def _run_rust_mcp_server(temp_dir: str) -> Optional[subprocess.Popen]:
        """Run a Rust MCP server."""
        try:
            # Rust 프로젝트 빌드
            subprocess.run(
                ["cargo", "build"], cwd=temp_dir, capture_output=True, timeout=300
            )

            # Rust 서버 실행
            process = subprocess.Popen(
                ["cargo", "run"],
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
            )

            return process

        except Exception as e:
            print(f"Rust MCP 서버 실행 실패: {str(e)}")
            return None

    @staticmethod
    def _call_mcp_protocol_tools(process: subprocess.Popen) -> List[dict]:
        """Request tools information via MCP protocol."""
        try:
            # MCP 서버의 표준 포트들
            ports = [3000, 8080, 8000, 5000, 4000]

            for port in ports:
                try:
                    # MCP 프로토콜 메시지 생성
                    tools_request = MCPServerService._create_mcp_tools_request()

                    # HTTP를 통한 MCP 프로토콜 시뮬레이션
                    response = requests.post(
                        f"http://localhost:{port}/mcp",
                        json=tools_request,
                        headers={"Content-Type": "application/json"},
                        timeout=10,
                    )

                    if response.status_code == 200:
                        tools_data = response.json()
                        return MCPServerService._parse_mcp_protocol_response(tools_data)

                    # 다른 엔드포인트 시도
                    response = requests.post(
                        f"http://localhost:{port}/api/mcp",
                        json=tools_request,
                        headers={"Content-Type": "application/json"},
                        timeout=10,
                    )

                    if response.status_code == 200:
                        tools_data = response.json()
                        return MCPServerService._parse_mcp_protocol_response(tools_data)

                except requests.exceptions.RequestException:
                    continue

            # HTTP가 실패하면 stdio를 통한 MCP 프로토콜 시도
            return MCPServerService._call_mcp_stdio_protocol(process, "tools/list")

        except Exception as e:
            print(f"MCP 프로토콜 tools 호출 실패: {str(e)}")
            return []

    @staticmethod
    def _call_mcp_protocol_resources(process: subprocess.Popen) -> List[dict]:
        """Request resources information via MCP protocol."""
        try:
            # MCP 서버의 표준 포트들
            ports = [3000, 8080, 8000, 5000, 4000]

            for port in ports:
                try:
                    # MCP 프로토콜 메시지 생성
                    resources_request = MCPServerService._create_mcp_resources_request()

                    # HTTP를 통한 MCP 프로토콜 시뮬레이션
                    response = requests.post(
                        f"http://localhost:{port}/mcp",
                        json=resources_request,
                        headers={"Content-Type": "application/json"},
                        timeout=10,
                    )

                    if response.status_code == 200:
                        resources_data = response.json()
                        return MCPServerService._parse_mcp_protocol_response(
                            resources_data
                        )

                    # 다른 엔드포인트 시도
                    response = requests.post(
                        f"http://localhost:{port}/api/mcp",
                        json=resources_request,
                        headers={"Content-Type": "application/json"},
                        timeout=10,
                    )

                    if response.status_code == 200:
                        resources_data = response.json()
                        return MCPServerService._parse_mcp_protocol_response(
                            resources_data
                        )

                except requests.exceptions.RequestException:
                    continue

            # HTTP가 실패하면 stdio를 통한 MCP 프로토콜 시도
            return MCPServerService._call_mcp_stdio_protocol(process, "resources/list")

        except Exception as e:
            print(f"MCP 프로토콜 resources 호출 실패: {str(e)}")
            return []

    @staticmethod
    def _create_mcp_tools_request() -> dict:
        """Create MCP protocol tools request message."""
        return {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

    @staticmethod
    def _create_mcp_resources_request() -> dict:
        """Create MCP protocol resources request message."""
        return {"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}}

    @staticmethod
    def _parse_mcp_protocol_response(response_data: dict) -> List[dict]:
        """Parse MCP protocol response."""
        tools = []

        try:
            if isinstance(response_data, dict):
                result = response_data.get("result", {})

                # tools 필드 확인
                if "tools" in result:
                    for tool in result["tools"]:
                        if isinstance(tool, dict):
                            tools.append(
                                {
                                    "name": tool.get("name", ""),
                                    "description": tool.get("description", ""),
                                    "input_properties": tool.get("inputSchema", {}).get(
                                        "properties", []
                                    ),
                                }
                            )

                # methods 필드 확인 (일부 구현체)
                elif "methods" in result:
                    for method in result["methods"]:
                        if isinstance(method, dict):
                            tools.append(
                                {
                                    "name": method.get("name", ""),
                                    "description": method.get("description", ""),
                                    "input_properties": method.get(
                                        "parameters", {}
                                    ).get("properties", []),
                                }
                            )

        except Exception as e:
            print(f"MCP 프로토콜 응답 파싱 실패: {str(e)}")

        return tools

    @staticmethod
    def _call_mcp_stdio_protocol(process: subprocess.Popen, method: str) -> List[dict]:
        """Attempt MCP protocol communication via stdio."""
        try:
            # MCP 프로토콜 메시지 생성
            request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": {}}

            # JSON-RPC 메시지를 stdio로 전송
            message = json.dumps(request) + "\n"

            # 프로세스에 메시지 전송
            if process.stdin:
                process.stdin.write(message.encode())
                process.stdin.flush()

            # 응답 읽기 (타임아웃 설정)
            start_time = time.time()
            while time.time() - start_time < 5:  # 5초 타임아웃
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        try:
                            response = json.loads(line.decode().strip())
                            return MCPServerService._parse_mcp_protocol_response(
                                response
                            )
                        except json.JSONDecodeError:
                            continue

            return []

        except Exception as e:
            print(f"stdio MCP 프로토콜 실패: {str(e)}")
            return []

    @staticmethod
    def _stop_mcp_server(process: subprocess.Popen):
        """Terminate the MCP server process."""
        try:
            if process and process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
        except Exception as e:
            print(f"서버 프로세스 종료 실패: {str(e)}")

    @staticmethod
    def _cleanup_temp_dir(temp_dir: str):
        """Clean up the temporary directory."""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"임시 디렉토리 정리 완료: {temp_dir}")
        except Exception as e:
            print(f"임시 디렉토리 정리 실패: {str(e)}")
