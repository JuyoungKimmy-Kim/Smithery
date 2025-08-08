import pytest
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.model.base import Base
from backend.database.dao.user_dao import UserDAO
from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.service.user_service import UserService
from backend.service.mcp_server_service import MCPServerService

@pytest.fixture(scope="function")
def db_session():
    """In-memory SQLite 데이터베이스 세션을 생성합니다."""
    # In-memory SQLite 데이터베이스 생성
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 세션 생성
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def user_dao(db_session):
    """UserDAO 인스턴스를 생성합니다."""
    return UserDAO(db_session)

@pytest.fixture(scope="function")
def mcp_server_dao(db_session):
    """MCPServerDAO 인스턴스를 생성합니다."""
    return MCPServerDAO(db_session)

@pytest.fixture(scope="function")
def user_service(db_session):
    """UserService 인스턴스를 생성합니다."""
    return UserService(db_session)

@pytest.fixture(scope="function")
def mcp_server_service(db_session):
    """MCPServerService 인스턴스를 생성합니다."""
    return MCPServerService(db_session) 