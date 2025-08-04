import sqlite3
import json
from typing import Optional, List
from datetime import datetime
from backend.database.model.user import User, UserCreate, UserResponse
from backend.database.database import Database


class UserDAO(Database):
    def create_table(self):
        """사용자 테이블 생성"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin')),
                avatar_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def create_user(self, user: UserCreate, password_hash: str) -> Optional[User]:
        """새 사용자 생성"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (user.username, user.email, password_hash, 'user'))
            
            user_id = cursor.lastrowid
            self.conn.commit()
            
            return self.get_user_by_id(user_id)
        except sqlite3.IntegrityError:
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, username, email, password_hash, role, avatar_url, created_at, updated_at
            FROM users WHERE id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                role=row['role'],
                avatar_url=row['avatar_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, username, email, password_hash, role, avatar_url, created_at, updated_at
            FROM users WHERE username = ?
        ''', (username,))
        
        row = cursor.fetchone()
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                role=row['role'],
                avatar_url=row['avatar_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, username, email, password_hash, role, avatar_url, created_at, updated_at
            FROM users WHERE email = ?
        ''', (email,))
        
        row = cursor.fetchone()
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                role=row['role'],
                avatar_url=row['avatar_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None

    def get_all_users(self) -> List[User]:
        """모든 사용자 조회"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, username, email, password_hash, role, avatar_url, created_at, updated_at
            FROM users ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append(User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                role=row['role'],
                avatar_url=row['avatar_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            ))
        return users

    def update_user(self, user_id: int, **kwargs) -> bool:
        """사용자 정보 업데이트"""
        cursor = self.conn.cursor()
        
        # 업데이트할 필드들
        update_fields = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['username', 'email', 'role', 'avatar_url']:
                update_fields.append(f"{key} = ?")
                values.append(value)
        
        if not update_fields:
            return False
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)
        
        try:
            cursor.execute(f'''
                UPDATE users SET {', '.join(update_fields)}
                WHERE id = ?
            ''', values)
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False

    def delete_user(self, user_id: int) -> bool:
        """사용자 삭제"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def is_admin(self, user_id: int) -> bool:
        """사용자가 관리자인지 확인"""
        user = self.get_user_by_id(user_id)
        return user and user.role == 'admin' 