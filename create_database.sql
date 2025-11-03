-- ============================================================================
-- DS Smithery Database Schema - Complete Database Creation Script
-- ============================================================================
-- This script creates all tables for the MCP Server Marketplace
-- Database: smithery_db
-- PostgreSQL Version: 12+
-- ============================================================================

-- Drop existing tables in correct order (respecting foreign key constraints)
DROP TABLE IF EXISTS comments CASCADE;
DROP TABLE IF EXISTS user_favorites CASCADE;
DROP TABLE IF EXISTS mcp_server_tags CASCADE;
DROP TABLE IF EXISTS mcp_server_properties CASCADE;
DROP TABLE IF EXISTS mcp_server_tools CASCADE;
DROP TABLE IF EXISTS mcp_servers CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- 1. USERS TABLE
-- ============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50) UNIQUE NOT NULL,
    is_admin VARCHAR(10) DEFAULT 'user' NOT NULL,  -- 'user' or 'admin'
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for users table
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_nickname ON users(nickname);

-- ============================================================================
-- 2. TAGS TABLE
-- ============================================================================
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for tags table
CREATE INDEX idx_tags_name ON tags(name);

-- ============================================================================
-- 3. MCP_SERVERS TABLE
-- ============================================================================
CREATE TABLE mcp_servers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    github_link VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    protocol VARCHAR(20) NOT NULL,
    server_url VARCHAR(500),
    config JSONB,
    announcement TEXT,
    owner_id INTEGER NOT NULL,
    health_status VARCHAR(20) DEFAULT 'unknown',
    last_health_check TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint
    CONSTRAINT fk_mcp_servers_owner
        FOREIGN KEY (owner_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Indexes for mcp_servers table
CREATE INDEX idx_mcp_servers_owner_id ON mcp_servers(owner_id);
CREATE INDEX idx_mcp_servers_status ON mcp_servers(status);
CREATE INDEX idx_mcp_servers_protocol ON mcp_servers(protocol);
CREATE INDEX idx_mcp_servers_category ON mcp_servers(category);
CREATE INDEX idx_mcp_servers_health_status ON mcp_servers(health_status);
CREATE INDEX idx_mcp_servers_created_at ON mcp_servers(created_at);

-- ============================================================================
-- 4. MCP_SERVER_TAGS TABLE (Many-to-Many Relationship)
-- ============================================================================
CREATE TABLE mcp_server_tags (
    mcp_server_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,

    PRIMARY KEY (mcp_server_id, tag_id),

    CONSTRAINT fk_mcp_server_tags_server
        FOREIGN KEY (mcp_server_id)
        REFERENCES mcp_servers(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_mcp_server_tags_tag
        FOREIGN KEY (tag_id)
        REFERENCES tags(id)
        ON DELETE CASCADE
);

-- Indexes for mcp_server_tags table
CREATE INDEX idx_mcp_server_tags_server_id ON mcp_server_tags(mcp_server_id);
CREATE INDEX idx_mcp_server_tags_tag_id ON mcp_server_tags(tag_id);

-- ============================================================================
-- 5. MCP_SERVER_TOOLS TABLE
-- ============================================================================
CREATE TABLE mcp_server_tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    mcp_server_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mcp_server_tools_server
        FOREIGN KEY (mcp_server_id)
        REFERENCES mcp_servers(id)
        ON DELETE CASCADE
);

-- Indexes for mcp_server_tools table
CREATE INDEX idx_mcp_server_tools_server_id ON mcp_server_tools(mcp_server_id);
CREATE INDEX idx_mcp_server_tools_name ON mcp_server_tools(name);

-- ============================================================================
-- 6. MCP_SERVER_PROPERTIES TABLE
-- ============================================================================
CREATE TABLE mcp_server_properties (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50),
    required BOOLEAN DEFAULT FALSE,
    tool_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mcp_server_properties_tool
        FOREIGN KEY (tool_id)
        REFERENCES mcp_server_tools(id)
        ON DELETE CASCADE
);

-- Indexes for mcp_server_properties table
CREATE INDEX idx_mcp_server_properties_tool_id ON mcp_server_properties(tool_id);
CREATE INDEX idx_mcp_server_properties_name ON mcp_server_properties(name);

-- ============================================================================
-- 7. USER_FAVORITES TABLE
-- ============================================================================
CREATE TABLE user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    mcp_server_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint to prevent duplicate favorites
    CONSTRAINT unique_user_favorite UNIQUE (user_id, mcp_server_id),

    CONSTRAINT fk_user_favorites_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_favorites_server
        FOREIGN KEY (mcp_server_id)
        REFERENCES mcp_servers(id)
        ON DELETE CASCADE
);

-- Indexes for user_favorites table
CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_server_id ON user_favorites(mcp_server_id);

-- ============================================================================
-- 8. COMMENTS TABLE
-- ============================================================================
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    mcp_server_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT,  -- Can be NULL for deleted comments
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    rating NUMERIC(2, 1) DEFAULT 0.0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_comments_mcp_server
        FOREIGN KEY (mcp_server_id)
        REFERENCES mcp_servers(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_comments_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    -- Rating must be between 0.0 and 5.0
    CONSTRAINT check_rating_range CHECK (rating >= 0.0 AND rating <= 5.0)
);

-- Indexes for comments table
CREATE INDEX idx_comments_mcp_server_id ON comments(mcp_server_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_comments_created_at ON comments(created_at);
CREATE INDEX idx_comments_is_deleted ON comments(is_deleted);
CREATE INDEX idx_comments_rating ON comments(rating);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
CREATE TRIGGER trigger_update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for mcp_servers table
CREATE TRIGGER trigger_update_mcp_servers_updated_at
    BEFORE UPDATE ON mcp_servers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for comments table
CREATE TRIGGER trigger_update_comments_updated_at
    BEFORE UPDATE ON comments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Display all created tables
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Display table row counts
SELECT
    'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'tags', COUNT(*) FROM tags
UNION ALL
SELECT 'mcp_servers', COUNT(*) FROM mcp_servers
UNION ALL
SELECT 'mcp_server_tags', COUNT(*) FROM mcp_server_tags
UNION ALL
SELECT 'mcp_server_tools', COUNT(*) FROM mcp_server_tools
UNION ALL
SELECT 'mcp_server_properties', COUNT(*) FROM mcp_server_properties
UNION ALL
SELECT 'user_favorites', COUNT(*) FROM user_favorites
UNION ALL
SELECT 'comments', COUNT(*) FROM comments;

-- Success message
SELECT 'Database schema created successfully!' as status;
