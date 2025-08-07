-- Smithery 데이터베이스 테이블 생성 스크립트
-- PostgreSQL용

-- 1. 사용자 테이블
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin VARCHAR(10) DEFAULT 'user',
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 2. 태그 테이블
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. MCP 서버 테이블
CREATE TABLE mcp_servers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    github_link VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    config JSONB,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 4. MCP 서버와 태그의 다대다 관계 테이블
CREATE TABLE mcp_server_tags (
    mcp_server_id INTEGER NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (mcp_server_id, tag_id)
);

-- 5. MCP 서버 도구 테이블
CREATE TABLE mcp_server_tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    mcp_server_id INTEGER NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. MCP 서버 도구 속성 테이블
CREATE TABLE mcp_server_properties (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tool_id INTEGER NOT NULL REFERENCES mcp_server_tools(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. 사용자 즐겨찾기 테이블
CREATE TABLE user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mcp_server_id INTEGER NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, mcp_server_id)
);

-- 인덱스 생성 (성능 향상)
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_mcp_servers_owner_id ON mcp_servers(owner_id);
CREATE INDEX idx_mcp_servers_status ON mcp_servers(status);
CREATE INDEX idx_mcp_servers_category ON mcp_servers(category);
CREATE INDEX idx_mcp_server_tools_server_id ON mcp_server_tools(mcp_server_id);
CREATE INDEX idx_mcp_server_properties_tool_id ON mcp_server_properties(tool_id);
CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_server_id ON user_favorites(mcp_server_id);

-- 기본 데이터 삽입
-- 1. 관리자 계정 생성
INSERT INTO users (username, email, password_hash, is_admin) 
VALUES ('admin', 'admin@smithery.com', 'admin123', 'admin');

-- 2. 기본 태그들 생성
INSERT INTO tags (name) VALUES 
('AI'),
('Automation'),
('Productivity'),
('Development'),
('Tools'),
('API'),
('Integration'),
('Data'),
('Analysis'),
('Machine Learning');

-- 성공 메시지
SELECT '모든 테이블이 성공적으로 생성되었습니다!' as message; 