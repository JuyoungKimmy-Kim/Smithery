#!/usr/bin/env python3
"""
Python 기반 MCP 서버의 정적 분석 서비스

@tool, @resource 데코레이터를 사용하는 Python MCP 서버에서
tools와 resources의 정보를 추출하고 데이터베이스에 저장합니다.
"""

import ast
import os
import re
import json
import tempfile
import shutil
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import inspect
import importlib.util
import sys
from urllib.parse import urlparse

# 데이터베이스 모델 import
from backend.database.model.mcp_server import (
    MCPServerTool,
    MCPServerProperty,
    MCPServerResource,
    MCPServer,
    TransportType,
)
from backend.database.dao.mcp_server_dao import MCPServerDAO


class MCPServerService:
    """
    Python 기반 MCP 서버의 정적 분석기

    @tool, @resource 데코레이터를 사용하는 함수들을 찾아서
    tools와 resources의 정보를 추출하고 데이터베이스에 저장합니다.
    """

    def __init__(self, github_link: str = None, db_path: str = "mcp_market.db"):
        """
        MCPServerService 초기화

        Args:
            github_link (str, optional): GitHub 저장소 링크
            db_path (str): 데이터베이스 파일 경로 (기본값: "mcp_market.db")
        """
        self.github_link = github_link
        self.tools = []
        self.resources = []
        self.dao = MCPServerDAO(db_path)
        self.dao.connect()
        self.dao.create_table()

    def analyze_python_mcp_server(self, repo_path: str) -> Dict[str, Any]:
        """
        Python MCP 서버 저장소를 분석하여 tools와 resources를 추출합니다.

        Args:
            repo_path (str): MCP 서버 저장소 경로

        Returns:
            Dict[str, Any]: 추출된 tools와 resources 정보
        """
        try:
            repo_path = Path(repo_path)
            if not repo_path.exists():
                return {"error": f"Repository path does not exist: {repo_path}"}

            # Python 파일들을 찾습니다
            python_files = self._find_python_files(repo_path)

            tools = []
            resources = []

            for py_file in python_files:
                try:
                    file_tools, file_resources = self._analyze_python_file(py_file)
                    tools.extend(file_tools)
                    resources.extend(file_resources)
                except Exception as e:
                    print(f"Error analyzing {py_file}: {e}")
                    continue

            # 중복 제거 (이름 기준)
            tools = self._remove_duplicates(tools, "name")
            resources = self._remove_duplicates(resources, "name")

            return {
                "tools": tools,
                "resources": resources,
                "analyzed_files": [str(f) for f in python_files],
                "total_files": len(python_files),
            }

        except Exception as e:
            return {"error": f"Failed to analyze Python MCP server: {str(e)}"}

    def convert_to_mcp_models(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        정적 분석 결과를 MCPServerTool, MCPServerProperty 모델 형식으로 변환합니다.

        Args:
            analysis_result (Dict[str, Any]): 정적 분석 결과

        Returns:
            Dict[str, Any]: 변환된 모델들
        """
        try:
            mcp_tools = []
            mcp_resources = []

            # Tools 변환
            for tool_data in analysis_result.get("tools", []):
                # MCPServerProperty 리스트 생성
                input_properties = []
                for param in tool_data.get("parameters", []):
                    property_obj = MCPServerProperty(
                        name=param.get("name", ""),
                        description=f"Type: {param.get('type', 'any')}",
                        required=param.get("required", True),
                    )
                    input_properties.append(property_obj)

                # MCPServerTool 생성
                tool_obj = MCPServerTool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    input_properties=input_properties,
                )
                mcp_tools.append(tool_obj)

            # Resources 변환
            for resource_data in analysis_result.get("resources", []):
                # MCPServerResource 생성
                resource_obj = MCPServerResource(
                    name=resource_data.get("name", ""),
                    description=resource_data.get("description", ""),
                    url=f"file://{resource_data.get('file', '')}:{resource_data.get('line', 0)}",
                )
                mcp_resources.append(resource_obj)

            return {
                "mcp_tools": mcp_tools,
                "mcp_resources": mcp_resources,
                "raw_analysis": analysis_result,
            }

        except Exception as e:
            return {"error": f"Failed to convert to MCP models: {str(e)}"}

    def analyze_and_convert_to_models(self, repo_path: str) -> Dict[str, Any]:
        """
        Python MCP 서버를 분석하고 MCPServerTool, MCPServerProperty 모델로 변환합니다.

        Args:
            repo_path (str): MCP 서버 저장소 경로

        Returns:
            Dict[str, Any]: 변환된 모델들과 원본 분석 결과
        """
        # 1. 정적 분석 수행
        analysis_result = self.analyze_python_mcp_server(repo_path)

        if "error" in analysis_result:
            return analysis_result

        # 2. 모델로 변환
        conversion_result = self.convert_to_mcp_models(analysis_result)

        if "error" in conversion_result:
            return conversion_result

        # 3. 결과 통합
        return {**analysis_result, **conversion_result}

    def _find_python_files(self, repo_path: Path) -> List[Path]:
        """저장소에서 Python 파일들을 찾습니다."""
        python_files = []

        # 일반적인 MCP 서버 파일 패턴들
        common_patterns = ["*.py", "**/*.py"]

        for pattern in common_patterns:
            python_files.extend(repo_path.glob(pattern))

        # 중복 제거 및 정렬
        python_files = list(set(python_files))
        python_files.sort()

        return python_files

    def _analyze_python_file(self, file_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """
        단일 Python 파일을 분석하여 tools와 resources를 추출합니다.

        Returns:
            Tuple[List[Dict], List[Dict]]: (tools, resources)
        """
        tools = []
        resources = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # AST를 사용한 분석
            tree = ast.parse(content)

            # 데코레이터가 있는 함수들을 찾습니다
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    tool_info = self._extract_tool_info(node, content, file_path)
                    if tool_info:
                        tools.append(tool_info)

                    resource_info = self._extract_resource_info(
                        node, content, file_path
                    )
                    if resource_info:
                        resources.append(resource_info)

            # 문자열 기반 분석 (AST로 찾지 못한 경우)
            string_tools = self._extract_tools_from_string(content, file_path)
            tools.extend(string_tools)

            string_resources = self._extract_resources_from_string(content, file_path)
            resources.extend(string_resources)

            # 중복 제거 (이름 기준)
            tools = self._remove_duplicates(tools, "name")
            resources = self._remove_duplicates(resources, "name")

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        return tools, resources

    def _extract_tool_info(
        self, node: ast.FunctionDef, content: str, file_path: Path
    ) -> Optional[Dict]:
        """@tool 데코레이터가 있는 함수에서 tool 정보를 추출합니다."""
        if not node.decorator_list:
            return None

        for decorator in node.decorator_list:
            tool_info = self._parse_tool_decorator(decorator, node, content, file_path)
            if tool_info:
                return tool_info

        return None

    def _extract_resource_info(
        self, node: ast.FunctionDef, content: str, file_path: Path
    ) -> Optional[Dict]:
        """@resource 데코레이터가 있는 함수에서 resource 정보를 추출합니다."""
        if not node.decorator_list:
            return None

        for decorator in node.decorator_list:
            resource_info = self._parse_resource_decorator(
                decorator, node, content, file_path
            )
            if resource_info:
                return resource_info

        return None

    def _parse_tool_decorator(
        self, decorator: ast.expr, node: ast.FunctionDef, content: str, file_path: Path
    ) -> Optional[Dict]:
        """@tool 데코레이터를 파싱합니다."""
        try:
            # @tool 형태
            if isinstance(decorator, ast.Name) and decorator.id == "tool":
                return self._extract_basic_tool_info(node, content, file_path)

            # @tool() 형태
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == "tool":
                    return self._extract_tool_info_from_call(
                        decorator, node, content, file_path
                    )
                # @server.tool() 형태
                elif (
                    isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "tool"
                ):
                    return self._extract_tool_info_from_call(
                        decorator, node, content, file_path
                    )

            # @server.tool 형태
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr == "tool":
                    return self._extract_basic_tool_info(node, content, file_path)

        except Exception as e:
            print(f"Error parsing tool decorator: {e}")

        return None

    def _parse_resource_decorator(
        self, decorator: ast.expr, node: ast.FunctionDef, content: str, file_path: Path
    ) -> Optional[Dict]:
        """@resource 데코레이터를 파싱합니다."""
        try:
            # @resource 형태
            if isinstance(decorator, ast.Name) and decorator.id == "resource":
                return self._extract_basic_resource_info(node, content, file_path)

            # @resource() 형태
            elif isinstance(decorator, ast.Call):
                if (
                    isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "resource"
                ):
                    return self._extract_resource_info_from_call(
                        decorator, node, content, file_path
                    )
                # @server.resource() 형태
                elif (
                    isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "resource"
                ):
                    return self._extract_resource_info_from_call(
                        decorator, node, content, file_path
                    )

            # @server.resource 형태
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr == "resource":
                    return self._extract_basic_resource_info(node, content, file_path)

        except Exception as e:
            print(f"Error parsing resource decorator: {e}")

        return None

    def _extract_basic_tool_info(
        self, node: ast.FunctionDef, content: str, file_path: Path
    ) -> Dict:
        """기본 @tool 데코레이터에서 tool 정보를 추출합니다."""
        # 함수 이름을 tool 이름으로 사용
        tool_name = node.name

        # 함수의 docstring을 description으로 사용
        description = ast.get_docstring(node) or ""

        # 함수 시그니처에서 파라미터 추출
        parameters = self._extract_function_parameters(node)

        return {
            "name": tool_name,
            "description": description,
            "parameters": parameters,
            "file": str(file_path),
            "line": node.lineno,
            "type": "tool",
        }

    def _extract_basic_resource_info(
        self, node: ast.FunctionDef, content: str, file_path: Path
    ) -> Dict:
        """기본 @resource 데코레이터에서 resource 정보를 추출합니다."""
        # 함수 이름을 resource 이름으로 사용
        resource_name = node.name

        # 함수의 docstring을 description으로 사용
        description = ast.get_docstring(node) or ""

        return {
            "name": resource_name,
            "description": description,
            "file": str(file_path),
            "line": node.lineno,
            "type": "resource",
        }

    def _extract_tool_info_from_call(
        self, decorator: ast.Call, node: ast.FunctionDef, content: str, file_path: Path
    ) -> Dict:
        """@tool(name="...") 형태에서 tool 정보를 추출합니다."""
        tool_name = node.name  # 기본값
        description = ast.get_docstring(node) or ""

        # 데코레이터 인자에서 정보 추출
        for keyword in decorator.keywords:
            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                tool_name = keyword.value.value
            elif keyword.arg == "description" and isinstance(
                keyword.value, ast.Constant
            ):
                description = keyword.value.value

        # 함수 시그니처에서 파라미터 추출
        parameters = self._extract_function_parameters(node)

        return {
            "name": tool_name,
            "description": description,
            "parameters": parameters,
            "file": str(file_path),
            "line": node.lineno,
            "type": "tool",
        }

    def _extract_resource_info_from_call(
        self, decorator: ast.Call, node: ast.FunctionDef, content: str, file_path: Path
    ) -> Dict:
        """@resource(name="...") 형태에서 resource 정보를 추출합니다."""
        resource_name = node.name  # 기본값
        description = ast.get_docstring(node) or ""

        # 데코레이터 인자에서 정보 추출
        for keyword in decorator.keywords:
            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                resource_name = keyword.value.value
            elif keyword.arg == "description" and isinstance(
                keyword.value, ast.Constant
            ):
                description = keyword.value.value

        return {
            "name": resource_name,
            "description": description,
            "file": str(file_path),
            "line": node.lineno,
            "type": "resource",
        }

    def _extract_function_parameters(self, node: ast.FunctionDef) -> List[Dict]:
        """함수의 파라미터 정보를 추출합니다."""
        parameters = []

        # args.args는 위치 인자들
        for i, arg in enumerate(node.args.args):
            param_info = {"name": arg.arg, "type": "any", "required": True}

            # 타입 힌트가 있는 경우
            if arg.annotation:
                param_info["type"] = self._get_type_string(arg.annotation)

            # 기본값이 있는 경우 (required=False)
            # 기본값은 node.args.defaults에 있습니다
            if i >= len(node.args.args) - len(node.args.defaults):
                param_info["required"] = False
                default_index = i - (len(node.args.args) - len(node.args.defaults))
                if default_index < len(node.args.defaults):
                    param_info["default"] = self._get_value_string(
                        node.args.defaults[default_index]
                    )

            parameters.append(param_info)

        return parameters

    def _get_type_string(self, annotation: ast.expr) -> str:
        """타입 어노테이션을 문자열로 변환합니다."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_type_string(annotation.value)}.{annotation.attr}"
        else:
            return "any"

    def _get_value_string(self, value: ast.expr) -> str:
        """AST 값을 문자열로 변환합니다."""
        if isinstance(value, ast.Constant):
            return str(value.value)
        elif isinstance(value, ast.Name):
            return value.id
        else:
            return str(value)

    def _extract_tools_from_string(self, content: str, file_path: Path) -> List[Dict]:
        """문자열 기반으로 @tool 데코레이터를 찾습니다 (AST로 찾지 못한 경우)."""
        tools = []

        # @tool 패턴들
        patterns = [
            r'@\w+\.tool\s*\(\s*name\s*=\s*["\']([^"\']+)["\']\s*\)',
            r'@\w+\.tool\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r"@\w+\.tool\s*\(\s*\)",
            r"@\w+\.tool\s*\n\s*def\s+(\w+)",
            r'@tool\s*\(\s*name\s*=\s*["\']([^"\']+)["\']\s*\)',
            r'@tool\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r"@tool\s*\(\s*\)",
            r"@tool\s*\n\s*def\s+(\w+)",
        ]

        lines = content.split("\n")
        for i, line in enumerate(lines):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    # 그룹이 있는 경우와 없는 경우 처리
                    if match.groups():
                        tool_name = match.group(1)
                    else:
                        # 다음 함수 정의에서 이름 추출
                        func_match = re.search(
                            r"def\s+(\w+)\s*\(", content[i * len(line) :]
                        )
                        if func_match:
                            tool_name = func_match.group(1)
                        else:
                            continue

                    # docstring 찾기
                    docstring = self._find_docstring(content, i)

                    tools.append(
                        {
                            "name": tool_name,
                            "description": docstring,
                            "parameters": [],  # 문자열 분석으로는 파라미터 추출이 어려움
                            "file": str(file_path),
                            "line": i + 1,
                            "type": "tool",
                        }
                    )

        return tools

    def _extract_resources_from_string(
        self, content: str, file_path: Path
    ) -> List[Dict]:
        """문자열 기반으로 @resource 데코레이터를 찾습니다 (AST로 찾지 못한 경우)."""
        resources = []

        # @resource 패턴들
        patterns = [
            r'@\w+\.resource\s*\(\s*name\s*=\s*["\']([^"\']+)["\']\s*\)',
            r'@\w+\.resource\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r"@\w+\.resource\s*\(\s*\)",
            r"@\w+\.resource\s*\n\s*def\s+(\w+)",
            r'@resource\s*\(\s*name\s*=\s*["\']([^"\']+)["\']\s*\)',
            r'@resource\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r"@resource\s*\(\s*\)",
            r"@resource\s*\n\s*def\s+(\w+)",
        ]

        lines = content.split("\n")
        for i, line in enumerate(lines):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    # 그룹이 있는 경우와 없는 경우 처리
                    if match.groups():
                        resource_name = match.group(1)
                    else:
                        # 다음 함수 정의에서 이름 추출
                        func_match = re.search(
                            r"def\s+(\w+)\s*\(", content[i * len(line) :]
                        )
                        if func_match:
                            resource_name = func_match.group(1)
                        else:
                            continue

                    # docstring 찾기
                    docstring = self._find_docstring(content, i)

                    resources.append(
                        {
                            "name": resource_name,
                            "description": docstring,
                            "file": str(file_path),
                            "line": i + 1,
                            "type": "resource",
                        }
                    )

        return resources

    def _find_docstring(self, content: str, line_index: int) -> str:
        """특정 라인 근처의 docstring을 찾습니다."""
        lines = content.split("\n")

        # 해당 라인 이후의 docstring 찾기
        for i in range(line_index + 1, min(line_index + 10, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                # docstring 시작
                docstring_lines = []
                quote_type = line[:3]

                # 첫 줄에서 docstring이 끝나는 경우
                if line.endswith(quote_type) and len(line) > 6:
                    return line[3:-3].strip()

                # 여러 줄 docstring
                docstring_lines.append(line[3:])

                for j in range(i + 1, len(lines)):
                    if lines[j].strip().endswith(quote_type):
                        docstring_lines.append(lines[j].strip()[:-3])
                        break
                    else:
                        docstring_lines.append(lines[j])

                return "\n".join(docstring_lines).strip()

        return ""

    def _remove_duplicates(self, items: List[Dict], key: str) -> List[Dict]:
        """리스트에서 중복된 항목을 제거합니다."""
        seen = set()
        unique_items = []

        for item in items:
            item_key = item.get(key)
            if item_key and item_key not in seen:
                seen.add(item_key)
                unique_items.append(item)

        return unique_items

    def set_github_link(self, github_link: str):
        """
        GitHub 링크를 설정합니다.

        Args:
            github_link (str): GitHub 저장소 링크
        """
        self.github_link = github_link

    def extract_and_save_mcp_server(
        self, server_name: str = None, description: str = None, category: str = "python"
    ) -> Dict[str, Any]:
        """
        Python MCP 서버를 분석하고 데이터베이스에 저장합니다.

        Args:
            server_name (str, optional): 서버 이름 (기본값: 저장소 이름)
            description (str, optional): 서버 설명
            category (str): 서버 카테고리 (기본값: "python")

        Returns:
            Dict[str, Any]: 분석 및 저장 결과
        """
        if not self.github_link:
            return {
                "error": "GitHub link not provided. Set it in __init__ or use set_github_link()"
            }

        try:
            # 1. GitHub 저장소 클론
            repo_path = self._clone_github_repo(self.github_link)
            if not repo_path:
                return {"error": "Failed to clone repository"}

            try:
                # 2. Python MCP 서버 분석
                analysis_result = self.analyze_and_convert_to_models(repo_path)

                if "error" in analysis_result:
                    return analysis_result

                # 3. 서버 정보 추출
                repo_info = self._parse_github_url(self.github_link)
                if not repo_info:
                    return {"error": "Failed to parse GitHub URL"}

                owner, repo, _ = repo_info

                # 4. MCPServer 객체 생성
                mcp_server = MCPServer(
                    id=f"{owner}/{repo}",
                    github_link=self.github_link,
                    name=server_name or repo,
                    description=description or f"Python MCP server: {repo}",
                    transport=TransportType.stdio,  # Python MCP 서버는 주로 stdio 사용
                    category=category,
                    tags=["python", "mcp"],
                    status="analyzed",
                    tools=analysis_result.get("mcp_tools", []),
                    resources=analysis_result.get("mcp_resources", []),
                    config={
                        "analyzed_files": analysis_result.get("analyzed_files", []),
                        "total_files": analysis_result.get("total_files", 0),
                    },
                )

                # 5. 데이터베이스에 저장
                self.dao.create_mcp(mcp_server)

                return {
                    "success": True,
                    "mcp_server": mcp_server,
                    "analysis_result": analysis_result,
                    "message": f"Successfully analyzed and saved MCP server: {mcp_server.name}",
                }

            finally:
                # 6. 임시 디렉토리 정리
                try:
                    shutil.rmtree(repo_path)
                except:
                    pass

        except Exception as e:
            return {"error": f"Failed to extract and save MCP server: {str(e)}"}

    def _clone_github_repo(self, github_link: str) -> Optional[str]:
        """GitHub 저장소를 임시 디렉토리에 클론합니다."""
        try:
            temp_dir = tempfile.mkdtemp(prefix="mcp_server_")

            result = subprocess.run(
                ["git", "clone", github_link, temp_dir],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                print(f"Git clone failed: {result.stderr}")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return None

            print(f"Successfully cloned to: {temp_dir}")
            return temp_dir

        except Exception as e:
            print(f"Error cloning repository: {e}")
            return None

    def _parse_github_url(self, github_link: str) -> Optional[tuple]:
        """GitHub URL에서 owner, repo, path 정보를 추출합니다."""
        try:
            parsed = urlparse(github_link)
            if "github.com" in parsed.netloc:
                path_parts = parsed.path.strip("/").split("/")
                if len(path_parts) >= 2:
                    owner = path_parts[0]
                    repo = path_parts[1]
                    path = ""
                    if len(path_parts) > 4 and path_parts[2] == "tree":
                        path = "/".join(path_parts[4:])
                    return owner, repo, path
        except Exception as e:
            print(f"Error parsing GitHub URL: {e}")
        return None

    def get_mcp_server(self, mcp_id: str) -> Optional[MCPServer]:
        """데이터베이스에서 MCP 서버 정보를 가져옵니다."""
        return self.dao.get_mcp(mcp_id)

    def get_all_mcp_servers(self) -> List[MCPServer]:
        """데이터베이스에서 모든 MCP 서버 정보를 가져옵니다."""
        return self.dao.get_all_mcps()

    def update_mcp_server(self, mcp_id: str, **kwargs) -> bool:
        """MCP 서버 정보를 업데이트합니다."""
        try:
            self.dao.update_mcp(mcp_id, **kwargs)
            return True
        except Exception as e:
            print(f"Error updating MCP server: {e}")
            return False

    def delete_mcp_server(self, mcp_id: str) -> bool:
        """MCP 서버를 삭제합니다."""
        try:
            self.dao.delete_mcp(mcp_id)
            return True
        except Exception as e:
            print(f"Error deleting MCP server: {e}")
            return False


def analyze_python_mcp_repository(repo_path: str) -> Dict[str, Any]:
    """
    Python MCP 저장소를 분석하는 편의 함수

    Args:
        repo_path (str): 저장소 경로

    Returns:
        Dict[str, Any]: 분석 결과
    """
    analyzer = MCPServerService()
    return analyzer.analyze_python_mcp_server(repo_path)
