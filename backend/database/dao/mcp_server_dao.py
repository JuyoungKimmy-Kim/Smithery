from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import Optional, List, Dict, Any
from backend.database.model import MCPServer, MCPServerTool, MCPServerProperty, Tag, User, UserFavorite

class MCPServerDAO:
    def __init__(self, db: Session):
        self.db = db
    
    def create_mcp_server(self, mcp_server_data: Dict[str, Any], owner_id: int, tags: List[str] = None) -> MCPServer:
        """새 MCP 서버를 생성합니다."""
        # 태그 처리
        tag_objects = []
        if tags:
            for tag_name in tags:
                tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    self.db.add(tag)
                    self.db.flush()
                tag_objects.append(tag)
        
        mcp_server = MCPServer(
            name=mcp_server_data['name'],
            github_link=mcp_server_data['github_link'],
            description=mcp_server_data['description'],
            category=mcp_server_data['category'],
            status='pending',  # 승인 대기 상태로 생성
            config=mcp_server_data.get('config'),
            owner_id=owner_id,
            tags=tag_objects
        )
        
        self.db.add(mcp_server)
        self.db.commit()
        self.db.refresh(mcp_server)
        return mcp_server
    
    def get_mcp_server_by_id(self, mcp_server_id: int) -> Optional[MCPServer]:
        """ID로 MCP 서버를 조회합니다."""
        return self.db.query(MCPServer).filter(MCPServer.id == mcp_server_id).first()
    
    def get_approved_mcp_servers(self, limit: int = None, offset: int = 0) -> List[MCPServer]:
        """승인된 MCP 서버 목록을 조회합니다."""
        query = self.db.query(MCPServer).options(
            joinedload(MCPServer.owner)
        ).filter(MCPServer.status == 'approved')
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def get_pending_mcp_servers(self) -> List[MCPServer]:
        """승인 대기 중인 MCP 서버 목록을 조회합니다."""
        return self.db.query(MCPServer).options(
            joinedload(MCPServer.owner)
        ).filter(MCPServer.status == 'pending').all()
    
    def search_mcp_servers(self, keyword: str, status: str = 'approved') -> List[MCPServer]:
        """키워드로 MCP 서버를 검색합니다."""
        return self.db.query(MCPServer).options(
            joinedload(MCPServer.owner)
        ).filter(
            and_(
                MCPServer.status == status,
                or_(
                    MCPServer.name.ilike(f'%{keyword}%'),
                    MCPServer.description.ilike(f'%{keyword}%'),
                    MCPServer.category.ilike(f'%{keyword}%'),
                    MCPServer.tags.any(Tag.name.ilike(f'%{keyword}%'))
                )
            )
        ).all()
    
    def get_mcp_servers_by_category(self, category: str, status: str = 'approved') -> List[MCPServer]:
        """카테고리별 MCP 서버 목록을 조회합니다."""
        return self.db.query(MCPServer).options(
            joinedload(MCPServer.owner)
        ).filter(
            and_(MCPServer.category == category, MCPServer.status == status)
        ).all()
    
    def update_mcp_server_status(self, mcp_server_id: int, status: str) -> Optional[MCPServer]:
        """MCP 서버 상태를 업데이트합니다."""
        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if mcp_server:
            mcp_server.status = status
            self.db.commit()
            self.db.refresh(mcp_server)
        return mcp_server
    
    def approve_all_pending_servers(self) -> dict:
        """모든 승인 대기중인 MCP 서버를 일괄 승인합니다."""
        result = self.db.query(MCPServer).filter(MCPServer.status == 'pending').update(
            {MCPServer.status: 'approved'}
        )
        self.db.commit()
        return {"approved_count": result}
    
    def delete_mcp_server(self, mcp_server_id: int) -> bool:
        """MCP 서버를 삭제합니다."""
        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if mcp_server:
            # 먼저 관련된 즐겨찾기 데이터 삭제
            self.db.query(UserFavorite).filter(UserFavorite.mcp_server_id == mcp_server_id).delete()
            
            # MCP 서버 삭제
            self.db.delete(mcp_server)
            self.db.commit()
            return True
        return False
    
    def add_tools_to_mcp_server(self, mcp_server_id: int, tools_data: List[Dict[str, Any]]) -> bool:
        """MCP 서버에 도구들을 추가합니다."""
        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            return False
        
        for tool_data in tools_data:
            tool = MCPServerTool(
                name=tool_data['name'],
                description=tool_data.get('description'),
                mcp_server_id=mcp_server_id
            )
            self.db.add(tool)
            self.db.flush()
            
            # 파라미터 추가
            for param_data in tool_data.get('parameters', []):
                param = MCPServerProperty(
                    name=param_data['name'],
                    description=param_data.get('description'),
                    tool_id=tool.id
                )
                self.db.add(param)
        
        self.db.commit()
        return True
    
    def get_mcp_server_with_tools(self, mcp_server_id: int) -> Optional[MCPServer]:
        """도구 정보와 함께 MCP 서버를 조회합니다."""
        return self.db.query(MCPServer).options(
            joinedload(MCPServer.tools).joinedload(MCPServerTool.parameters)
        ).filter(MCPServer.id == mcp_server_id).first()
    
    def get_mcp_servers_by_owner(self, owner_id: int) -> List[MCPServer]:
        """소유자별 MCP 서버 목록을 조회합니다."""
        return self.db.query(MCPServer).filter(MCPServer.owner_id == owner_id).all()
    
    def get_popular_tags(self, limit: int = 10) -> List[Tag]:
        """인기 태그 목록을 조회합니다."""
        return self.db.query(Tag).join(MCPServer.tags).filter(MCPServer.status == 'approved').limit(limit).all()
    
    def get_categories(self) -> List[str]:
        """모든 카테고리 목록을 조회합니다."""
        categories = self.db.query(MCPServer.category).distinct().all()
        return [category[0] for category in categories if category[0]]
    
    def update_mcp_server(self, mcp_server_id: int, update_data: Dict[str, Any]) -> Optional[MCPServer]:
        """MCP 서버를 수정합니다."""
        print(f"DAO: Updating MCP server {mcp_server_id} with data: {update_data}")  # 디버깅 로그
        
        # Pydantic 모델을 딕셔너리로 변환
        if hasattr(update_data, 'dict'):
            update_data = update_data.dict(exclude_unset=True)
        elif hasattr(update_data, 'model_dump'):
            update_data = update_data.model_dump(exclude_unset=True)
        
        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            print(f"DAO: MCP server {mcp_server_id} not found")  # 디버깅 로그
            return None
        
        print(f"DAO: Before update - name: '{mcp_server.name}', description: '{mcp_server.description}', category: '{mcp_server.category}'")  # 디버깅 로그
        
        # 업데이트 가능한 필드들
        updatable_fields = ['name', 'description', 'category', 'config']
        
        print(f"DAO: Checking updatable fields: {updatable_fields}")  # 디버깅 로그
        print(f"DAO: Update data keys: {list(update_data.keys())}")  # 디버깅 로그
        
        for field in updatable_fields:
            print(f"DAO: Checking field '{field}'")  # 디버깅 로그
            if field in update_data:
                print(f"DAO: Field '{field}' found in update_data")  # 디버깅 로그
                if update_data[field] is not None:
                    old_value = getattr(mcp_server, field)
                    new_value = update_data[field]
                    print(f"DAO: Updating field '{field}' from '{old_value}' to '{new_value}'")  # 디버깅 로그
                    setattr(mcp_server, field, new_value)
                else:
                    print(f"DAO: Skipping field '{field}' because value is None")  # 디버깅 로그
            else:
                print(f"DAO: Field '{field}' not found in update_data")  # 디버깅 로그
        
        # 태그 업데이트
        if 'tags' in update_data:
            print(f"DAO: Updating tags from '{mcp_server.tags}' to '{update_data['tags']}'")  # 디버깅 로그
            tags = update_data['tags']
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            tag_objects = []
            for tag_name in tags:
                tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    self.db.add(tag)
                    self.db.flush()
                tag_objects.append(tag)
            
            mcp_server.tags = tag_objects
        
        print(f"DAO: After update - name: '{mcp_server.name}', description: '{mcp_server.description}', category: '{mcp_server.category}'")  # 디버깅 로그
        print(f"DAO: Committing changes to database...")  # 디버깅 로그
        self.db.commit()
        self.db.refresh(mcp_server)
        print(f"DAO: Update completed successfully")  # 디버깅 로그
        return mcp_server
