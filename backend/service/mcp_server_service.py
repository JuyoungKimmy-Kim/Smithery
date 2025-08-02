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
        GitHub 저장소에서 MCP 서버의 tool 목록을 읽어옵니다.
        
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
            
            owner, repo = repo_info
            
            # 저장소의 파일 구조 확인
            files = self.github_api.get_repo_files(owner, repo)
            
            # MCP 서버 관련 파일들 찾기
            mcp_files = self._find_mcp_server_files(files)
            
            # src/tools 디렉토리도 추가로 탐색
            tools_dir_files = self.github_api.get_repo_files(owner, repo, "src/tools")
            if tools_dir_files:
                mcp_files.extend(tools_dir_files)
            
            tools = []
            for file_info in mcp_files:
                if file_info['type'] == 'file':
                    content = self.github_api.get_file_content(owner, repo, file_info['path'])
                    if content:
                        file_tools = self._extract_tools_from_file(content, file_info['path'])
                        tools.extend(file_tools)
            
            return tools
            
        except Exception as e:
            print(f"Error reading MCP server tools: {e}")
            return []

    def read_mcp_server_resource_list(self, github_link: str) -> list:
        """
        GitHub 저장소에서 MCP 서버의 resource 목록을 읽어옵니다.
        
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
            
            owner, repo = repo_info
            
            # 저장소의 파일 구조 확인
            files = self.github_api.get_repo_files(owner, repo)
            
            # MCP 서버 관련 파일들 찾기
            mcp_files = self._find_mcp_server_files(files)
            
            # src/tools 디렉토리도 추가로 탐색
            tools_dir_files = self.github_api.get_repo_files(owner, repo, "src/tools")
            if tools_dir_files:
                mcp_files.extend(tools_dir_files)
            
            resources = []
            for file_info in mcp_files:
                if file_info['type'] == 'file':
                    content = self.github_api.get_file_content(owner, repo, file_info['path'])
                    if content:
                        file_resources = self._extract_resources_from_file(content, file_info['path'])
                        resources.extend(file_resources)
            
            return resources
            
        except Exception as e:
            print(f"Error reading MCP server resources: {e}")
            return []

    def _parse_github_url(self, github_link: str) -> Optional[tuple]:
        """
        GitHub URL에서 owner와 repo 정보를 추출합니다.
        
        Args:
            github_link (str): GitHub 저장소 링크
            
        Returns:
            Optional[tuple]: (owner, repo) 튜플 또는 None
        """
        try:
            parsed = urlparse(github_link)
            if 'github.com' in parsed.netloc:
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    return path_parts[0], path_parts[1]
        except Exception as e:
            print(f"Error parsing GitHub URL: {e}")
        return None

    def _find_mcp_server_files(self, files: list) -> list:
        """
        파일 목록에서 MCP 서버 관련 파일들을 찾습니다.
        
        Args:
            files (list): 파일 목록
            
        Returns:
            list: MCP 서버 관련 파일들
        """
        mcp_files = []
        for file_info in files:
            path = file_info.get('path', '').lower()
            name = file_info.get('name', '').lower()
            
            # MCP 관련 키워드가 포함된 파일들
            if any(keyword in path for keyword in ['mcp', 'server', 'tool', 'resource']):
                mcp_files.append(file_info)
            # src/tools/ 디렉토리의 Python 파일들
            elif path.startswith('src/tools/') and name.endswith('.py'):
                mcp_files.append(file_info)
            # main.py 파일
            elif name == 'main.py':
                mcp_files.append(file_info)
        return mcp_files

    def _extract_tools_from_file(self, content: str, file_path: str) -> list:
        """
        파일 내용에서 Tool 정의를 추출합니다.
        
        Args:
            content (str): 파일 내용
            file_path (str): 파일 경로
            
        Returns:
            list: Tool 목록
        """
        tools = []
        try:
            # Python 파일에서 Tool 클래스 정의 찾기
            if file_path.endswith('.py'):
                # Tool 클래스 정의 패턴 찾기
                tool_patterns = [
                    r'class\s+(\w+Tool)\s*:',
                    r'@tool\s*\([^)]*\)\s*def\s+(\w+)',
                    r'@mcp\.tool\s*\([^)]*\)\s*async\s+def\s+(\w+)',
                    r'@mcp\.tool\s*\([^)]*\)\s*def\s+(\w+)',
                    r'@mcp\.tools\s*\([^)]*\)\s*async\s+def\s+(\w+)',
                    r'@mcp\.tools\s*\([^)]*\)\s*def\s+(\w+)',
                    r'@mcp\.tool\s*\([^)]*\)\s*async\s+def\s+(\w+)',
                    r'@mcp\.tool\s*\([^)]*\)\s*def\s+(\w+)',
                    r'@server\.tool\s*\([^)]*\)\s*async\s+def\s+(\w+)',
                    r'@server\.tool\s*\([^)]*\)\s*def\s+(\w+)',
                    r'Tool\s*\(\s*name\s*=\s*["\']([^"\']+)["\']',
                ]
                
                for pattern in tool_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        tool_info = {
                            'name': match,
                            'file': file_path,
                            'type': 'tool'
                        }
                        tools.append(tool_info)
            
            # JSON 파일에서 tool 정의 찾기
            elif file_path.endswith('.json'):
                try:
                    json_data = json.loads(content)
                    if 'tools' in json_data:
                        for tool in json_data['tools']:
                            tools.append({
                                'name': tool.get('name', 'Unknown'),
                                'description': tool.get('description', ''),
                                'file': file_path,
                                'type': 'tool'
                            })
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            print(f"Error extracting tools from {file_path}: {e}")
        
        return tools

    def _extract_resources_from_file(self, content: str, file_path: str) -> list:
        """
        파일 내용에서 Resource 정의를 추출합니다.
        
        Args:
            content (str): 파일 내용
            file_path (str): 파일 경로
            
        Returns:
            list: Resource 목록
        """
        resources = []
        try:
            # Python 파일에서 Resource 클래스 정의 찾기
            if file_path.endswith('.py'):
                # Resource 클래스 정의 패턴 찾기
                resource_patterns = [
                    r'class\s+(\w+Resource)\s*:',
                    r'@resource\s*\([^)]*\)\s*def\s+(\w+)',
                    r'@mcp\.resource\s*\([^)]*\)\s*async\s+def\s+(\w+)',
                    r'@mcp\.resource\s*\([^)]*\)\s*def\s+(\w+)',
                    r'@mcp\.resources\s*\([^)]*\)\s*async\s+def\s+(\w+)',
                    r'@mcp\.resources\s*\([^)]*\)\s*def\s+(\w+)',
                    r'@server\.resource\s*\([^)]*\)\s*async\s+def\s+(\w+)',
                    r'@server\.resource\s*\([^)]*\)\s*def\s+(\w+)',
                    r'Resource\s*\(\s*name\s*=\s*["\']([^"\']+)["\']',
                ]
                
                for pattern in resource_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        resource_info = {
                            'name': match,
                            'file': file_path,
                            'type': 'resource'
                        }
                        resources.append(resource_info)
            
            # JSON 파일에서 resource 정의 찾기
            elif file_path.endswith('.json'):
                try:
                    json_data = json.loads(content)
                    if 'resources' in json_data:
                        for resource in json_data['resources']:
                            resources.append({
                                'name': resource.get('name', 'Unknown'),
                                'description': resource.get('description', ''),
                                'file': file_path,
                                'type': 'resource'
                            })
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            print(f"Error extracting resources from {file_path}: {e}")
        
        return resources 