import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from backend.database.database import Database
from backend.database.model.mcp_server import (
    MCPServer, MCPServerTool, MCPServerResource, MCPServerProperty, 
    TransportType, MCPServerStatus, MCPServerCreate, MCPServerUpdate
)


class MCPServerDAO(Database):
    def create_table(self):
        """MCP 서버 관련 테이블들 생성"""
        cursor = self.conn.cursor()
        
        # MCP 서버 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mcp_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_link VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                transport TEXT DEFAULT 'stdio' CHECK(transport IN ('sse', 'streamable-http', 'stdio')),
                category VARCHAR(50),
                tags TEXT, -- JSON 배열로 저장
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'private')),
                config TEXT, -- JSON으로 저장
                created_by INTEGER NOT NULL,
                approved_by INTEGER,
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        ''')
        
        # MCP 도구 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mcp_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mcp_server_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                parameters TEXT, -- JSON으로 저장
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mcp_server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
            )
        ''')
        
        # MCP 리소스 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mcp_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mcp_server_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mcp_server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE
            )
        ''')
        
        # 사용자 즐겨찾기 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mcp_server_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (mcp_server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE,
                UNIQUE(user_id, mcp_server_id)
            )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mcp_servers_status ON mcp_servers(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mcp_servers_category ON mcp_servers(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mcp_servers_created_by ON mcp_servers(created_by)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mcp_tools_server_id ON mcp_tools(mcp_server_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mcp_resources_server_id ON mcp_resources(mcp_server_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_favorites_server_id ON user_favorites(mcp_server_id)')
        
        self.conn.commit()

    def create_mcp_server(self, mcp: MCPServerCreate, created_by: int) -> Optional[int]:
        """새 MCP 서버 생성"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO mcp_servers (github_link, name, description, transport, category, tags, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                mcp.github_link,
                mcp.name,
                mcp.description,
                mcp.transport.value,
                mcp.category,
                json.dumps(mcp.tags) if mcp.tags else None,
                created_by
            ))
            
            mcp_server_id = cursor.lastrowid
            self.conn.commit()
            return mcp_server_id
        except sqlite3.IntegrityError:
            return None

    def get_mcp_server(self, mcp_id: int) -> Optional[MCPServer]:
        """ID로 MCP 서버 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, github_link, name, description, transport, category, tags, status, config,
                   created_by, approved_by, approved_at, created_at, updated_at
            FROM mcp_servers WHERE id = ?
        ''', (mcp_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # 도구와 리소스 조회
        tools = self._get_tools_by_server_id(mcp_id)
        resources = self._get_resources_by_server_id(mcp_id)
        
        return MCPServer(
            id=row['id'],
            github_link=row['github_link'],
            name=row['name'],
            description=row['description'],
            transport=TransportType(row['transport']),
            category=row['category'],
            tags=json.loads(row['tags']) if row['tags'] else None,
            status=MCPServerStatus(row['status']),
            config=json.loads(row['config']) if row['config'] else {},
            created_by=row['created_by'],
            approved_by=row['approved_by'],
            approved_at=datetime.fromisoformat(row['approved_at']) if row['approved_at'] else None,
            tools=tools,
            resources=resources,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    def get_approved_mcp_servers(self) -> List[MCPServer]:
        """승인된 MCP 서버 목록 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, github_link, name, description, transport, category, tags, status, config,
                   created_by, approved_by, approved_at, created_at, updated_at
            FROM mcp_servers WHERE status = 'approved' ORDER BY created_at DESC
        ''')
        
        servers = []
        for row in cursor.fetchall():
            tools = self._get_tools_by_server_id(row['id'])
            resources = self._get_resources_by_server_id(row['id'])
            
            servers.append(MCPServer(
                id=row['id'],
                github_link=row['github_link'],
                name=row['name'],
                description=row['description'],
                transport=TransportType(row['transport']),
                category=row['category'],
                tags=json.loads(row['tags']) if row['tags'] else None,
                status=MCPServerStatus(row['status']),
                config=json.loads(row['config']) if row['config'] else {},
                created_by=row['created_by'],
                approved_by=row['approved_by'],
                approved_at=datetime.fromisoformat(row['approved_at']) if row['approved_at'] else None,
                tools=tools,
                resources=resources,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return servers

    def get_pending_mcp_servers(self) -> List[MCPServer]:
        """승인 대기 중인 MCP 서버 목록 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, github_link, name, description, transport, category, tags, status, config,
                   created_by, approved_by, approved_at, created_at, updated_at
            FROM mcp_servers WHERE status = 'pending' ORDER BY created_at DESC
        ''')
        
        servers = []
        for row in cursor.fetchall():
            tools = self._get_tools_by_server_id(row['id'])
            resources = self._get_resources_by_server_id(row['id'])
            
            servers.append(MCPServer(
                id=row['id'],
                github_link=row['github_link'],
                name=row['name'],
                description=row['description'],
                transport=TransportType(row['transport']),
                category=row['category'],
                tags=json.loads(row['tags']) if row['tags'] else None,
                status=MCPServerStatus(row['status']),
                config=json.loads(row['config']) if row['config'] else {},
                created_by=row['created_by'],
                approved_by=row['approved_by'],
                approved_at=datetime.fromisoformat(row['approved_at']) if row['approved_at'] else None,
                tools=tools,
                resources=resources,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return servers

    def get_mcp_servers_by_user(self, user_id: int) -> List[MCPServer]:
        """사용자가 등록한 MCP 서버 목록 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, github_link, name, description, transport, category, tags, status, config,
                   created_by, approved_by, approved_at, created_at, updated_at
            FROM mcp_servers WHERE created_by = ? ORDER BY created_at DESC
        ''', (user_id,))
        
        servers = []
        for row in cursor.fetchall():
            tools = self._get_tools_by_server_id(row['id'])
            resources = self._get_resources_by_server_id(row['id'])
            
            servers.append(MCPServer(
                id=row['id'],
                github_link=row['github_link'],
                name=row['name'],
                description=row['description'],
                transport=TransportType(row['transport']),
                category=row['category'],
                tags=json.loads(row['tags']) if row['tags'] else None,
                status=MCPServerStatus(row['status']),
                config=json.loads(row['config']) if row['config'] else {},
                created_by=row['created_by'],
                approved_by=row['approved_by'],
                approved_at=datetime.fromisoformat(row['approved_at']) if row['approved_at'] else None,
                tools=tools,
                resources=resources,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return servers

    def search_mcp_servers(self, keyword: str) -> List[MCPServer]:
        """키워드로 MCP 서버 검색"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, github_link, name, description, transport, category, tags, status, config,
                   created_by, approved_by, approved_at, created_at, updated_at
            FROM mcp_servers 
            WHERE status = 'approved' AND (
                name LIKE ? OR description LIKE ? OR category LIKE ? OR tags LIKE ?
            )
            ORDER BY created_at DESC
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        
        servers = []
        for row in cursor.fetchall():
            tools = self._get_tools_by_server_id(row['id'])
            resources = self._get_resources_by_server_id(row['id'])
            
            servers.append(MCPServer(
                id=row['id'],
                github_link=row['github_link'],
                name=row['name'],
                description=row['description'],
                transport=TransportType(row['transport']),
                category=row['category'],
                tags=json.loads(row['tags']) if row['tags'] else None,
                status=MCPServerStatus(row['status']),
                config=json.loads(row['config']) if row['config'] else {},
                created_by=row['created_by'],
                approved_by=row['approved_by'],
                approved_at=datetime.fromisoformat(row['approved_at']) if row['approved_at'] else None,
                tools=tools,
                resources=resources,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return servers

    def update_mcp_server_status(self, mcp_id: int, status: MCPServerStatus, approved_by: int = None) -> bool:
        """MCP 서버 상태 업데이트"""
        cursor = self.conn.cursor()
        try:
            if status == MCPServerStatus.approved:
                cursor.execute('''
                    UPDATE mcp_servers SET status = ?, approved_by = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status.value, approved_by, mcp_id))
            else:
                cursor.execute('''
                    UPDATE mcp_servers SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status.value, mcp_id))
            
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def delete_mcp_server(self, mcp_id: int) -> bool:
        """MCP 서버 삭제"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM mcp_servers WHERE id = ?', (mcp_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def add_favorite(self, user_id: int, mcp_server_id: int) -> bool:
        """즐겨찾기 추가"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO user_favorites (user_id, mcp_server_id)
                VALUES (?, ?)
            ''', (user_id, mcp_server_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_favorite(self, user_id: int, mcp_server_id: int) -> bool:
        """즐겨찾기 제거"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM user_favorites WHERE user_id = ? AND mcp_server_id = ?
        ''', (user_id, mcp_server_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_user_favorites(self, user_id: int) -> List[MCPServer]:
        """사용자의 즐겨찾기 목록 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT m.id, m.github_link, m.name, m.description, m.transport, m.category, m.tags, m.status, m.config,
                   m.created_by, m.approved_by, m.approved_at, m.created_at, m.updated_at
            FROM mcp_servers m
            JOIN user_favorites uf ON m.id = uf.mcp_server_id
            WHERE uf.user_id = ? AND m.status = 'approved'
            ORDER BY uf.created_at DESC
        ''', (user_id,))
        
        servers = []
        for row in cursor.fetchall():
            tools = self._get_tools_by_server_id(row['id'])
            resources = self._get_resources_by_server_id(row['id'])
            
            servers.append(MCPServer(
                id=row['id'],
                github_link=row['github_link'],
                name=row['name'],
                description=row['description'],
                transport=TransportType(row['transport']),
                category=row['category'],
                tags=json.loads(row['tags']) if row['tags'] else None,
                status=MCPServerStatus(row['status']),
                config=json.loads(row['config']) if row['config'] else {},
                created_by=row['created_by'],
                approved_by=row['approved_by'],
                approved_at=datetime.fromisoformat(row['approved_at']) if row['approved_at'] else None,
                tools=tools,
                resources=resources,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return servers

    def _get_tools_by_server_id(self, server_id: int) -> List[MCPServerTool]:
        """서버 ID로 도구 목록 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, name, description, parameters, created_at
            FROM mcp_tools WHERE mcp_server_id = ?
        ''', (server_id,))
        
        tools = []
        for row in cursor.fetchall():
            parameters = json.loads(row['parameters']) if row['parameters'] else []
            tools.append(MCPServerTool(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                parameters=[MCPServerProperty(**param) for param in parameters],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            ))
        return tools

    def _get_resources_by_server_id(self, server_id: int) -> List[MCPServerResource]:
        """서버 ID로 리소스 목록 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, name, description, url, created_at
            FROM mcp_resources WHERE mcp_server_id = ?
        ''', (server_id,))
        
        resources = []
        for row in cursor.fetchall():
            resources.append(MCPServerResource(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                url=row['url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            ))
        return resources

    def add_tools_to_server(self, server_id: int, tools: List[MCPServerTool]) -> bool:
        """서버에 도구 추가"""
        cursor = self.conn.cursor()
        try:
            for tool in tools:
                cursor.execute('''
                    INSERT INTO mcp_tools (mcp_server_id, name, description, parameters)
                    VALUES (?, ?, ?, ?)
                ''', (
                    server_id,
                    tool.name,
                    tool.description,
                    json.dumps([param.dict() for param in tool.parameters])
                ))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def add_resources_to_server(self, server_id: int, resources: List[MCPServerResource]) -> bool:
        """서버에 리소스 추가"""
        cursor = self.conn.cursor()
        try:
            for resource in resources:
                cursor.execute('''
                    INSERT INTO mcp_resources (mcp_server_id, name, description, url)
                    VALUES (?, ?, ?, ?)
                ''', (
                    server_id,
                    resource.name,
                    resource.description,
                    resource.url
                ))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False
