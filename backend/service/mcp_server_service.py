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
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.model import (
    MCPServer, MCPServerTool, MCPServerProperty, Tag,
    MCPServerPrompt, MCPServerPromptArgument, MCPServerResource
)
from datetime import datetime
import pytz

class MCPServerService:
    """
    Python 기반 MCP 서버의 정적 분석기

    @tool, @resource 데코레이터를 사용하는 함수들을 찾아서
    tools와 resources의 정보를 추출하고 데이터베이스에 저장합니다.
    """

    def __init__(self, db: Session):
        self.db = db
        self.mcp_server_dao = MCPServerDAO(db)
    
    def create_mcp_server(self, mcp_server_data: Dict[str, Any], owner_id: int) -> MCPServer:
        """새 MCP 서버를 생성합니다."""
        # 프론트엔드에서 전송한 데이터 추출
        tools_data = mcp_server_data.get('tools', [])
        prompts_data = mcp_server_data.get('prompts', [])
        resources_data = mcp_server_data.get('resources', [])

        # tools 데이터가 없으면 GitHub에서 추출 시도
        if not tools_data:
            tools_data = self._extract_tools_from_github(mcp_server_data['github_link'])

        # 태그 처리
        tags = mcp_server_data.get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]

        # MCP 서버 생성
        mcp_server = self.mcp_server_dao.create_mcp_server(mcp_server_data, owner_id, tags)

        # 도구 정보 추가
        if tools_data:
            self.mcp_server_dao.add_tools_to_mcp_server(mcp_server.id, tools_data)

        # 프롬프트 정보 추가
        if prompts_data:
            self._add_prompts_to_mcp_server(mcp_server.id, prompts_data)

        # 리소스 정보 추가
        if resources_data:
            self._add_resources_to_mcp_server(mcp_server.id, resources_data)

        return mcp_server
    
    def _extract_tools_from_github(self, github_link: str) -> List[Dict[str, Any]]:
        """
        GitHub 링크에서 도구 정보를 추출합니다. (Skeleton 구현)
        실제로는 git clone 후 MCP 서버의 tools 정보를 파싱해야 합니다.
        """
        # TODO: 실제 구현
        # 1. git clone
        # 2. MCP 서버 설정 파일 파싱
        # 3. tools 정보 추출
        
        # 임시 skeleton 데이터 반환
        return [
            {
                "name": "example_tool",
                "description": "Example tool extracted from GitHub",
                "parameters": [
                    {
                        "name": "param1",
                        "description": "Example parameter",
                        "required": False
                    }
                ]
            }
        ]
    
    def get_approved_mcp_servers(self, limit: int = None, offset: int = 0) -> List[MCPServer]:
        """승인된 MCP 서버 목록을 조회합니다."""
        return self.mcp_server_dao.get_approved_mcp_servers(limit, offset)
    
    def get_pending_mcp_servers(self) -> List[MCPServer]:
        """승인 대기중인 MCP 서버 목록을 조회합니다."""
        return self.mcp_server_dao.get_pending_mcp_servers()
    
    def get_mcp_server_by_id(self, mcp_server_id: int) -> Optional[MCPServer]:
        """ID로 MCP 서버를 조회합니다."""
        return self.mcp_server_dao.get_mcp_server_by_id(mcp_server_id)
    
    def get_mcp_server_with_tools(self, mcp_server_id: int) -> Optional[MCPServer]:
        """도구 정보와 함께 MCP 서버를 조회합니다."""
        return self.mcp_server_dao.get_mcp_server_with_tools(mcp_server_id)
    
    def search_mcp_servers(self, keyword: str, status: str = 'approved') -> List[MCPServer]:
        """키워드로 MCP 서버를 검색합니다."""
        return self.mcp_server_dao.search_mcp_servers(keyword, status)
    
    def get_mcp_servers_by_category(self, category: str, status: str = 'approved') -> List[MCPServer]:
        """카테고리별 MCP 서버 목록을 조회합니다."""
        return self.mcp_server_dao.get_mcp_servers_by_category(category, status)

    def get_mcp_servers_by_tags(self, tags: List[str], status: str = 'approved') -> List[MCPServer]:
        """태그별 MCP 서버 목록을 조회합니다."""
        return self.mcp_server_dao.search_mcp_servers_with_tags(None, tags, status)

    def search_mcp_servers_with_tags(self, keyword: str, tags: List[str], status: str = 'approved') -> List[MCPServer]:
        """키워드와 태그로 MCP 서버를 검색합니다. (AND 조건)"""
        return self.mcp_server_dao.search_mcp_servers_with_tags(keyword, tags, status)
    
    def update_mcp_server(self, mcp_server_id: int, mcp_server_data) -> Optional[MCPServer]:
        """MCP 서버를 수정합니다."""
        # Pydantic 모델을 딕셔너리로 변환
        if hasattr(mcp_server_data, 'dict'):
            data_dict = mcp_server_data.dict()
        else:
            data_dict = mcp_server_data

        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            return None

        # tools 데이터가 있으면 업데이트
        if 'tools' in data_dict and data_dict['tools'] is not None:
            # 기존 tools 삭제
            for tool in mcp_server.tools:
                self.db.delete(tool)
            self.db.commit()

            # 새 tools 추가
            tools_data = data_dict['tools']
            if tools_data:
                # Pydantic 모델을 딕셔너리로 변환
                tools_dict = []
                for tool in tools_data:
                    if hasattr(tool, 'dict'):
                        tool_dict = tool.dict()
                    else:
                        tool_dict = tool
                    tools_dict.append(tool_dict)

                self.mcp_server_dao.add_tools_to_mcp_server(mcp_server_id, tools_dict)

        # prompts 데이터가 있으면 업데이트
        if 'prompts' in data_dict and data_dict['prompts'] is not None:
            # 기존 prompts 삭제
            for prompt in mcp_server.prompts:
                self.db.delete(prompt)
            self.db.commit()

            # 새 prompts 추가
            prompts_data = data_dict['prompts']
            if prompts_data:
                prompts_dict = []
                for prompt in prompts_data:
                    if hasattr(prompt, 'dict'):
                        prompt_dict = prompt.dict()
                    else:
                        prompt_dict = prompt
                    prompts_dict.append(prompt_dict)

                self._add_prompts_to_mcp_server(mcp_server_id, prompts_dict)

        # resources 데이터가 있으면 업데이트
        if 'resources' in data_dict and data_dict['resources'] is not None:
            # 기존 resources 삭제
            for resource in mcp_server.resources:
                self.db.delete(resource)
            self.db.commit()

            # 새 resources 추가
            resources_data = data_dict['resources']
            if resources_data:
                resources_dict = []
                for resource in resources_data:
                    if hasattr(resource, 'dict'):
                        resource_dict = resource.dict()
                    else:
                        resource_dict = resource
                    resources_dict.append(resource_dict)

                self._add_resources_to_mcp_server(mcp_server_id, resources_dict)

        # tools, prompts, resources 키를 제거하고 나머지 데이터로 업데이트
        update_data = {k: v for k, v in data_dict.items() if k not in ['tools', 'prompts', 'resources']}
        return self.mcp_server_dao.update_mcp_server(mcp_server_id, update_data)
    
    def delete_mcp_server(self, mcp_server_id: int) -> bool:
        """MCP 서버를 삭제합니다."""
        return self.mcp_server_dao.delete_mcp_server(mcp_server_id)
    
    def approve_mcp_server(self, mcp_server_id: int) -> Optional[MCPServer]:
        """MCP 서버를 승인합니다."""
        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if mcp_server:
            mcp_server.status = 'approved'
            self.db.commit()
            self.db.refresh(mcp_server)
        return mcp_server
    
    def reject_mcp_server(self, mcp_server_id: int) -> Optional[MCPServer]:
        """MCP 서버를 거부합니다."""
        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if mcp_server:
            mcp_server.status = 'rejected'
            self.db.commit()
            self.db.refresh(mcp_server)
        return mcp_server
    
    def approve_all_pending_servers(self) -> Dict[str, int]:
        """모든 승인 대기중인 MCP 서버를 일괄 승인합니다."""
        pending_servers = self.get_pending_mcp_servers()
        approved_count = 0
        
        for server in pending_servers:
            server.status = 'approved'
            approved_count += 1
        
        self.db.commit()
        return {"approved_count": approved_count}
    
    def get_popular_tags(self, limit: int = 10) -> List[Tag]:
        """인기 태그 목록을 조회합니다."""
        # 간단한 구현 - 실제로는 사용 빈도 기반으로 정렬해야 함
        return self.db.query(Tag).limit(limit).all()
    
    def get_categories(self) -> List[str]:
        """모든 카테고리 목록을 조회합니다."""
        categories = self.db.query(MCPServer.category).distinct().all()
        return [cat[0] for cat in categories if cat[0]]
    
    def get_mcp_server_favorites_count(self, mcp_server_id: int) -> int:
        """특정 MCP 서버의 즐겨찾기 수를 조회합니다."""
        return self.mcp_server_dao.get_mcp_server_favorites_count(mcp_server_id)

    def get_top_mcp_servers(self, limit: int = 3) -> List[MCPServer]:
        """인기 MCP 서버 Top N을 조회합니다. (즐겨찾기 수 기준)"""
        return self.mcp_server_dao.get_top_mcp_servers(limit)
    
    def update_mcp_server_announcement(self, mcp_server_id: int, announcement: Optional[str]) -> Optional[MCPServer]:
        """MCP 서버의 공지사항을 업데이트합니다."""
        return self.mcp_server_dao.update_mcp_server_announcement(mcp_server_id, announcement)

    async def check_server_health(self, mcp_server_id: int) -> Dict[str, Any]:
        """
        MCP 서버의 헬스 체크를 수행합니다.
        - STDIO 서버는 건너뜁니다 (원격 health check 불가)
        - SSE/HTTP 서버만 server_url을 사용하여 체크합니다.
        """
        from backend.service.mcp_health_checker import MCPHealthChecker
        import logging
        logger = logging.getLogger(__name__)

        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            logger.error(f"Server {mcp_server_id} not found in database")
            return {"error": "Server not found"}

        transport_type = mcp_server.protocol.lower() if mcp_server.protocol else ""

        logger.info(f"Health check for server {mcp_server_id}:")
        logger.info(f"  - Name: {mcp_server.name}")
        logger.info(f"  - Protocol: {mcp_server.protocol}")
        logger.info(f"  - Server URL: {mcp_server.server_url}")
        logger.info(f"  - Transport type: {transport_type}")

        # STDIO 서버는 health check 건너뛰기
        if transport_type == "stdio":
            logger.info(f"Skipping health check for STDIO server {mcp_server_id}")
            return {
                "id": mcp_server.id,
                "health_status": "unknown",
                "last_health_check": None,
                "message": "Health check is not applicable for STDIO servers"
            }

        health_status = "unknown"
        error_message = None

        try:
            # server_url이 없으면 체크 불가
            if not mcp_server.server_url:
                health_status = "unknown"
                error_message = "No server URL configured"
                logger.warning(f"Server {mcp_server_id} has no server_url configured")
            else:
                # MCP Health Checker 생성 (MCP SDK 사용)
                health_checker = MCPHealthChecker()

                logger.info(f"Starting health check for {mcp_server.server_url} with transport {transport_type}")

                # Health check 수행
                result = await health_checker.check_server_health(
                    server_url=mcp_server.server_url,
                    transport_type=transport_type
                )

                logger.info(f"Health check result: {result}")

                # 결과 해석
                if result.get("healthy"):
                    health_status = "healthy"
                    logger.info(f"Server {mcp_server_id} is HEALTHY")
                else:
                    health_status = "unhealthy"
                    error_message = result.get("error", "Unknown error")
                    logger.warning(f"Server {mcp_server_id} is UNHEALTHY: {error_message}")

        except Exception as e:
            health_status = "unhealthy"
            error_message = f"Health check failed: {str(e)}"
            logger.error(f"Health check exception for server {mcp_server_id}: {str(e)}", exc_info=True)

        # 데이터베이스 업데이트 - 한국 시간으로 저장
        korea_tz = pytz.timezone('Asia/Seoul')
        korea_time = datetime.now(korea_tz)

        logger.info(f"Updating DB: health_status={health_status}, last_health_check={korea_time}")

        mcp_server.health_status = health_status
        mcp_server.last_health_check = korea_time
        self.db.commit()
        self.db.refresh(mcp_server)

        logger.info(f"DB updated successfully for server {mcp_server_id}")

        return {
            "id": mcp_server.id,
            "health_status": health_status,
            "last_health_check": mcp_server.last_health_check.isoformat() if mcp_server.last_health_check else None,
            "error": error_message
        }

    def _add_prompts_to_mcp_server(self, mcp_server_id: int, prompts_data: List[Dict[str, Any]]):
        """MCP 서버에 prompts를 추가합니다."""
        for prompt_data in prompts_data:
            prompt = MCPServerPrompt(
                name=prompt_data['name'],
                description=prompt_data.get('description'),
                mcp_server_id=mcp_server_id
            )
            self.db.add(prompt)
            self.db.flush()  # ID를 가져오기 위해 flush

            # arguments 추가
            for arg_data in prompt_data.get('arguments', []):
                argument = MCPServerPromptArgument(
                    name=arg_data['name'],
                    description=arg_data.get('description'),
                    required=arg_data.get('required', False),
                    prompt_id=prompt.id
                )
                self.db.add(argument)

        self.db.commit()

    def _add_resources_to_mcp_server(self, mcp_server_id: int, resources_data: List[Dict[str, Any]]):
        """MCP 서버에 resources를 추가합니다."""
        for resource_data in resources_data:
            resource = MCPServerResource(
                uri=resource_data['uri'],
                name=resource_data['name'],
                description=resource_data.get('description'),
                mime_type=resource_data.get('mimeType') or resource_data.get('mime_type'),
                mcp_server_id=mcp_server_id
            )
            self.db.add(resource)

        self.db.commit()