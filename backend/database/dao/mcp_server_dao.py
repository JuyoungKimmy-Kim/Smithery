from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func, desc
from typing import Optional, List, Dict, Any
from backend.database.model import MCPServer, MCPServerTool, MCPServerProperty, Tag, User, UserFavorite

class MCPServerDAO:
    def __init__(self, db: Session):
        self.db = db
    
    def create_mcp_server(self, mcp_server_data: Dict[str, Any], owner_id: int, tags: List[str] = None) -> MCPServer:
        """새 MCP 서버를 생성합니다."""
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
            category=mcp_server_data.get('category'),
            status='pending',
            protocol=mcp_server_data.get('protocol', 'http'),
            server_url=mcp_server_data.get('server_url'),
            config=mcp_server_data.get('config'),
            owner_id=owner_id,
            tags=tag_objects
        )
        
        self.db.add(mcp_server)
        self.db.commit()
        self.db.refresh(mcp_server)
        return mcp_server
    
    def get_mcp_servers(
        self,
        status: str = 'approved',
        category: Optional[str] = None,
        sort: str = 'favorites',
        order: str = 'desc',
        limit: int = 20,
        offset: int = 0
    ) -> List[MCPServer]:
        """
        MCP 서버 목록을 조회합니다. (통합 조회 메서드)

        Args:
            status: 서버 상태 (approved, pending)
            category: 카테고리 필터
            sort: 정렬 기준 (favorites, created_at)
            order: 정렬 순서 (asc, desc)
            limit: 조회 개수
            offset: 오프셋
        """
        query = self.db.query(MCPServer).options(
            joinedload(MCPServer.owner),
            joinedload(MCPServer.tags),
            joinedload(MCPServer.tools)
        )

        # 상태 필터
        query = query.filter(MCPServer.status == status)

        # 카테고리 필터
        if category:
            query = query.filter(MCPServer.category == category)

        # 정렬 처리
        if sort == 'favorites':
            # 즐겨찾기 수 기준 정렬
            favorites_subquery = self.db.query(
                UserFavorite.mcp_server_id,
                func.count(UserFavorite.id).label('favorites_count')
            ).group_by(UserFavorite.mcp_server_id).subquery()

            query = query.outerjoin(
                favorites_subquery, MCPServer.id == favorites_subquery.c.mcp_server_id
            )

            if order == 'desc':
                query = query.order_by(
                    desc(favorites_subquery.c.favorites_count),
                    MCPServer.created_at.desc()
                )
            else:
                query = query.order_by(
                    favorites_subquery.c.favorites_count,
                    MCPServer.created_at.asc()
                )
        elif sort == 'created_at':
            # 등록일 기준 정렬
            if order == 'desc':
                query = query.order_by(desc(MCPServer.created_at))
            else:
                query = query.order_by(MCPServer.created_at)
        else:
            # 기본: created_at desc
            query = query.order_by(desc(MCPServer.created_at))

        # limit, offset 적용
        if limit:
            query = query.limit(limit).offset(offset)

        return query.all()

    def get_mcp_server_by_id(self, mcp_server_id: int) -> Optional[MCPServer]:
        """ID로 MCP 서버를 조회합니다."""
        return self.db.query(MCPServer).filter(MCPServer.id == mcp_server_id).first()
    
    def get_approved_mcp_servers(self, limit: int = None, offset: int = 0) -> List[MCPServer]:
        """승인된 MCP 서버 목록을 조회합니다. (즐겨찾기 수 내림차순)"""
        # 서브쿼리로 각 MCP 서버의 즐겨찾기 수 계산
        favorites_subquery = self.db.query(
            UserFavorite.mcp_server_id,
            func.count(UserFavorite.id).label('favorites_count')
        ).group_by(UserFavorite.mcp_server_id).subquery()
        
        # 메인 쿼리에서 조인하고 정렬
        query = self.db.query(MCPServer).options(
            joinedload(MCPServer.owner)
        ).outerjoin(
            favorites_subquery, MCPServer.id == favorites_subquery.c.mcp_server_id
        ).filter(
            MCPServer.status == 'approved'
        ).order_by(
            desc(favorites_subquery.c.favorites_count),
            MCPServer.created_at.desc()
        )
        
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def get_pending_mcp_servers(self) -> List[MCPServer]:
        """승인 대기중인 MCP 서버 목록을 조회합니다."""
        return self.db.query(MCPServer).options(
            joinedload(MCPServer.owner)
        ).filter(MCPServer.status == 'pending').order_by(MCPServer.created_at.desc()).all()
    
    def search_mcp_servers(self, keyword: str, status: str = 'approved') -> List[MCPServer]:
        """키워드로 MCP 서버를 검색합니다."""
        query = self.db.query(MCPServer).options(
            joinedload(MCPServer.owner)
        ).filter(
            and_(
                MCPServer.status == status,
                or_(
                    MCPServer.name.ilike(f'%{keyword}%'),
                    MCPServer.description.ilike(f'%{keyword}%')
                )
            )
        ).order_by(MCPServer.created_at.desc())
        return query.all()
    
    def get_mcp_servers_by_category(self, category: str, status: str = 'approved') -> List[MCPServer]:
        """카테고리별 MCP 서버 목록을 조회합니다."""
        return self.db.query(MCPServer).options(
            joinedload(MCPServer.owner)
        ).filter(
            and_(
                MCPServer.category == category,
                MCPServer.status == status
            )
        ).order_by(MCPServer.created_at.desc()).all()

    def search_mcp_servers_with_tags(self, keyword: Optional[str], tags: List[str], status: str = 'approved') -> List[MCPServer]:
        """키워드와 태그로 MCP 서버를 검색합니다. keyword가 None이면 tags만으로 검색"""
        query = self.db.query(MCPServer).options(
            joinedload(MCPServer.owner),
            joinedload(MCPServer.tags)
        ).join(
            MCPServer.tags
        )

        # 필터 조건 구성
        conditions = [
            Tag.name.in_(tags),
            MCPServer.status == status
        ]

        # keyword가 있으면 추가 필터
        if keyword:
            conditions.append(
                or_(
                    MCPServer.name.ilike(f'%{keyword}%'),
                    MCPServer.description.ilike(f'%{keyword}%')
                )
            )

        return query.filter(and_(*conditions)).distinct().order_by(MCPServer.created_at.desc()).all()
    
    def update_mcp_server(self, mcp_server_id: int, mcp_server_data: Dict[str, Any]) -> Optional[MCPServer]:
        """MCP 서버를 수정합니다."""
        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            return None
        
        for field in ['name', 'description', 'category', 'protocol', 'server_url', 'config']:
            if field in mcp_server_data and mcp_server_data[field] is not None:
                setattr(mcp_server, field, mcp_server_data[field])
        
        if 'tags' in mcp_server_data and mcp_server_data['tags'] is not None:
            tags = mcp_server_data['tags']
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            mcp_server.tags.clear()
            
            for tag_name in tags:
                tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    self.db.add(tag)
                    self.db.flush()
                mcp_server.tags.append(tag)
        
        self.db.commit()
        self.db.refresh(mcp_server)
        return mcp_server
    
    def delete_mcp_server(self, mcp_server_id: int) -> bool:
        """MCP 서버를 삭제합니다."""
        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if mcp_server:
            self.db.query(UserFavorite).filter(UserFavorite.mcp_server_id == mcp_server_id).delete()
            
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
            
            for param_data in tool_data.get('parameters', []):
                param = MCPServerProperty(
                    name=param_data['name'],
                    description=param_data.get('description'),
                    type=param_data.get('type'),
                    required=param_data.get('required', False),
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
    
    def get_mcp_server_favorites_count(self, mcp_server_id: int) -> int:
        """특정 MCP 서버의 즐겨찾기 수를 조회합니다."""
        return self.db.query(UserFavorite).filter(
            UserFavorite.mcp_server_id == mcp_server_id
        ).count()
    
    def update_mcp_server_announcement(self, mcp_server_id: int, announcement: Optional[str]) -> Optional[MCPServer]:
        """MCP 서버의 공지사항을 업데이트합니다."""
        mcp_server = self.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            return None

        mcp_server.announcement = announcement
        self.db.commit()
        self.db.refresh(mcp_server)
        return mcp_server

    def get_top_mcp_servers(self, limit: int = 3) -> List[MCPServer]:
        """인기 MCP 서버 Top N을 조회합니다. (즐겨찾기 수 기준, 내림차순)"""
        # 서브쿼리로 각 MCP 서버의 즐겨찾기 수 계산
        favorites_subquery = self.db.query(
            UserFavorite.mcp_server_id,
            func.count(UserFavorite.id).label('favorites_count')
        ).group_by(UserFavorite.mcp_server_id).subquery()

        # 메인 쿼리에서 조인하고 정렬하여 Top N 반환
        return self.db.query(MCPServer).options(
            joinedload(MCPServer.owner),
            joinedload(MCPServer.tags),
            joinedload(MCPServer.tools)
        ).join(
            favorites_subquery, MCPServer.id == favorites_subquery.c.mcp_server_id
        ).filter(
            MCPServer.status == 'approved'
        ).order_by(
            desc(favorites_subquery.c.favorites_count)
        ).limit(limit).all()

    def get_latest_mcp_servers(self, limit: int = 3) -> List[MCPServer]:
        """최신 등록된 MCP 서버 Top N을 조회합니다. (등록일 기준, 내림차순)"""
        return self.db.query(MCPServer).options(
            joinedload(MCPServer.owner),
            joinedload(MCPServer.tags),
            joinedload(MCPServer.tools)
        ).filter(
            MCPServer.status == 'approved'
        ).order_by(
            desc(MCPServer.created_at)
        ).limit(limit).all()