import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """데이터베이스 설정 관리"""
    
    # SQLite 설정 (현재)
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "mcp_market.db")
    
    # MySQL 설정 (나중에 사용)
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "mcp_market")
    
    # PostgreSQL 설정 (나중에 사용)
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "mcp_market")
    
    # 데이터베이스 타입 (현재: sqlite, 나중에: mysql, postgresql)
    DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
    
    @classmethod
    def get_connection_string(cls) -> str:
        """데이터베이스 연결 문자열 반환"""
        if cls.DB_TYPE == "mysql":
            return f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
        elif cls.DB_TYPE == "postgresql":
            return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DATABASE}"
        else:
            return cls.SQLITE_DB_PATH
    
    @classmethod
    def is_sqlite(cls) -> bool:
        return cls.DB_TYPE == "sqlite"
    
    @classmethod
    def is_mysql(cls) -> bool:
        return cls.DB_TYPE == "mysql"
    
    @classmethod
    def is_postgresql(cls) -> bool:
        return cls.DB_TYPE == "postgresql" 