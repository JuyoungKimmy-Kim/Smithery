from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

# 데이터베이스 URL 설정
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/smithery_db"
)

# 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=False,
    echo=False,  # SQL 로그 출력 여부
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Database:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_db(self) -> Generator[Session, None, None]:
        """
        데이터베이스 세션을 생성하는 제너레이터
        """
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def create_tables(self):
        """
        모든 테이블을 생성합니다.
        """
        from .model import Base
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """
        모든 테이블을 삭제합니다.
        """
        from .model import Base
        Base.metadata.drop_all(bind=self.engine)
    
    def reset_database(self):
        """
        데이터베이스를 초기화합니다.
        """
        self.drop_tables()
        self.create_tables()

# 전역 데이터베이스 인스턴스
database = Database()

# 의존성 주입을 위한 함수
def get_db():
    """
    FastAPI Depends에서 사용할 데이터베이스 세션 의존성
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
