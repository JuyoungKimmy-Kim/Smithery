-- user/user 계정 (user 비밀번호 해시)
INSERT INTO users (username, email, password_hash, is_admin, created_at) 
VALUES ('user', 'user@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8.', 'user', NOW()) 
ON CONFLICT (username) DO NOTHING;

-- admin/admin 계정 (admin 비밀번호 해시)
INSERT INTO users (username, email, password_hash, is_admin, created_at) 
VALUES ('admin', 'admin@example.com', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi.', 'admin', NOW()) 
ON CONFLICT (username) DO NOTHING; 