# 데이터베이스 마이그레이션 가이드

## 현재 상태: SQLite (로컬 개발)

현재 SQLite를 사용하고 있으며, 나중에 서버 DB(MySQL/PostgreSQL)로 마이그레이션할 수 있도록 설계되어 있습니다.

## 🔄 마이그레이션 준비사항

### 1. 환경 변수 설정

`.env` 파일에 데이터베이스 설정을 추가:

```bash
# 현재: SQLite (기본값)
DB_TYPE=sqlite
SQLITE_DB_PATH=mcp_market.db

# 나중에: MySQL로 변경 시
DB_TYPE=mysql
MYSQL_HOST=your-mysql-server.com
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mcp_market

# 또는 PostgreSQL로 변경 시
DB_TYPE=postgresql
POSTGRES_HOST=your-postgres-server.com
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=mcp_market
```

### 2. 필요한 의존성 추가

서버 DB 사용 시 추가할 의존성:

```bash
# MySQL 사용 시
pip install pymysql

# PostgreSQL 사용 시
pip install psycopg2-binary
```

## 🚀 마이그레이션 단계

### 1단계: 서버 DB 설정

1. **MySQL 또는 PostgreSQL 서버 설정**
2. **데이터베이스 생성**
3. **사용자 권한 설정**

### 2단계: 스키마 마이그레이션

#### MySQL 스키마:
```sql
-- MySQL용 스키마 (database_schema_mysql.sql)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE mcp_servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    github_link VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    transport ENUM('sse', 'streamable-http', 'stdio') DEFAULT 'stdio',
    category VARCHAR(50),
    tags JSON,
    status ENUM('pending', 'approved', 'rejected', 'private') DEFAULT 'pending',
    config JSON,
    created_by INT NOT NULL,
    approved_by INT,
    approved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- 나머지 테이블들...
```

#### PostgreSQL 스키마:
```sql
-- PostgreSQL용 스키마 (database_schema_postgresql.sql)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(10) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mcp_servers (
    id SERIAL PRIMARY KEY,
    github_link VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    transport VARCHAR(20) DEFAULT 'stdio' CHECK (transport IN ('sse', 'streamable-http', 'stdio')),
    category VARCHAR(50),
    tags JSONB,
    status VARCHAR(10) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'private')),
    config JSONB,
    created_by INTEGER NOT NULL,
    approved_by INTEGER,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- 나머지 테이블들...
```

### 3단계: 데이터 마이그레이션

#### SQLite에서 서버 DB로 데이터 이전:

```python
# migration_script.py
import sqlite3
import mysql.connector  # 또는 psycopg2
from backend.database.config import DatabaseConfig

def migrate_data():
    # SQLite 연결
    sqlite_conn = sqlite3.connect('mcp_market.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # 서버 DB 연결
    if DatabaseConfig.is_mysql():
        server_conn = mysql.connector.connect(
            host=DatabaseConfig.MYSQL_HOST,
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.MYSQL_PASSWORD,
            database=DatabaseConfig.MYSQL_DATABASE
        )
    else:
        import psycopg2
        server_conn = psycopg2.connect(
            host=DatabaseConfig.POSTGRES_HOST,
            user=DatabaseConfig.POSTGRES_USER,
            password=DatabaseConfig.POSTGRES_PASSWORD,
            database=DatabaseConfig.POSTGRES_DATABASE
        )
    
    server_cursor = server_conn.cursor()
    
    # 사용자 데이터 마이그레이션
    sqlite_cursor.execute("SELECT * FROM users")
    users = sqlite_cursor.fetchall()
    
    for user in users:
        server_cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, avatar_url, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, user[1:])  # id 제외
    
    # MCP 서버 데이터 마이그레이션
    sqlite_cursor.execute("SELECT * FROM mcp_servers")
    servers = sqlite_cursor.fetchall()
    
    for server in servers:
        server_cursor.execute("""
            INSERT INTO mcp_servers (github_link, name, description, transport, category, tags, status, config, created_by, approved_by, approved_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, server[1:])  # id 제외
    
    # 나머지 테이블들...
    
    server_conn.commit()
    sqlite_conn.close()
    server_conn.close()
```

### 4단계: DAO 업데이트

서버 DB 사용 시 DAO를 업데이트:

```python
# backend/database/dao/mysql_user_dao.py (예시)
import mysql.connector
from backend.database.database import Database
from backend.database.model.user import User

class MySQLUserDAO(Database):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
    
    def connect(self):
        # MySQL 연결 로직
        pass
    
    def create_table(self):
        # MySQL 테이블 생성 로직
        pass
    
    # 나머지 메서드들...
```

## ✅ 마이그레이션 체크리스트

### 준비 단계
- [ ] 서버 DB 설치 및 설정
- [ ] 환경 변수 설정
- [ ] 의존성 설치
- [ ] 스키마 생성

### 마이그레이션 단계
- [ ] 데이터 백업
- [ ] 스키마 마이그레이션
- [ ] 데이터 이전
- [ ] DAO 업데이트
- [ ] 연결 테스트

### 검증 단계
- [ ] 데이터 무결성 확인
- [ ] API 테스트
- [ ] 성능 테스트
- [ ] 롤백 계획 수립

## 🎯 권장사항

1. **개발 단계**: SQLite 사용 (현재)
2. **테스트 단계**: 서버 DB 사용
3. **운영 단계**: 서버 DB 사용

현재 구조로도 충분히 마이그레이션 가능하므로, 지금은 SQLite로 개발을 계속 진행하시면 됩니다! 