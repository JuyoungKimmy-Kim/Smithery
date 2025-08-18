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
from backend.database.model import MCPServer, MCPServerTool, MCPServerProperty, Tag

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
        # GitHub 링크에서 도구 정보 추출 (skeleton 구현)
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
                        "description": "Example parameter"
                    }
                ]
            }
        ]
    
    def get_approved_mcp_servers(self, limit: int = None, offset: int = 0) -> List[MCPServer]:
        """승인된 MCP 서버 목록을 조회합니다."""
        return self.mcp_server_dao.get_approved_mcp_servers(limit, offset)
    
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
    
    def get_pending_mcp_servers(self) -> List[MCPServer]:
        """승인 대기 중인 MCP 서버 목록을 조회합니다."""
        return self.mcp_server_dao.get_pending_mcp_servers()
    
    def get_all_mcp_servers(self, limit: int = None, offset: int = 0) -> List[MCPServer]:
        """모든 MCP 서버 목록을 조회합니다 (승인된 것과 pending 모두)."""
        return self.mcp_server_dao.get_all_mcp_servers(limit, offset)
    
    def approve_mcp_server(self, mcp_server_id: int) -> Optional[MCPServer]:
        """MCP 서버를 승인합니다."""
        return self.mcp_server_dao.update_mcp_server_status(mcp_server_id, 'approved')
    
    def reject_mcp_server(self, mcp_server_id: int) -> Optional[MCPServer]:
        """MCP 서버를 거부합니다."""
        return self.mcp_server_dao.update_mcp_server_status(mcp_server_id, 'rejected')
    
    def approve_all_pending_servers(self) -> dict:
        """모든 승인 대기중인 MCP 서버를 일괄 승인합니다."""
        return self.mcp_server_dao.approve_all_pending_servers()
    
    def delete_mcp_server(self, mcp_server_id: int) -> bool:
        """MCP 서버를 삭제합니다."""
        return self.mcp_server_dao.delete_mcp_server(mcp_server_id)
    
    def get_mcp_servers_by_owner(self, owner_id: int) -> List[MCPServer]:
        """소유자별 MCP 서버 목록을 조회합니다."""
        return self.mcp_server_dao.get_mcp_servers_by_owner(owner_id)
    
    def get_popular_tags(self, limit: int = 10) -> List[Tag]:
        """인기 태그 목록을 조회합니다."""
        return self.mcp_server_dao.get_popular_tags(limit)
    
    def get_categories(self) -> List[str]:
        """모든 카테고리 목록을 조회합니다."""
        return self.mcp_server_dao.get_categories()
    
    def update_mcp_server(self, mcp_server_id: int, update_data: Dict[str, Any]) -> Optional[MCPServer]:
        """MCP 서버를 수정합니다."""
        return self.mcp_server_dao.update_mcp_server(mcp_server_id, update_data)
