#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
새로운 스키마로 데이터베이스를 생성하고 기본 관리자 계정을 설정합니다.
"""

import sqlite3
import os
from pathlib import Path


def init_database():
    """데이터베이스 초기화"""
    db_path = "mcp_market.db"
    
    # 기존 데이터베이스 백업 (존재하는 경우)
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        print(f"기존 데이터베이스를 {backup_path}로 백업합니다...")
        os.rename(db_path, backup_path)
    
    # 새 데이터베이스 생성
    print("새 데이터베이스를 생성합니다...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # 스키마 파일 읽기
    schema_file = Path("database_schema.sql")
    if not schema_file.exists():
        print("❌ database_schema.sql 파일을 찾을 수 없습니다.")
        return False
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # 스키마 실행
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print("✅ 데이터베이스 스키마가 성공적으로 생성되었습니다.")
        
        # 테이블 확인
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"생성된 테이블: {[table['name'] for table in tables]}")
        
        # 관리자 계정 확인
        cursor.execute("SELECT username, email, role FROM users WHERE role = 'admin'")
        admin_users = cursor.fetchall()
        print(f"관리자 계정: {[user['username'] for user in admin_users]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 중 오류 발생: {e}")
        conn.close()
        return False


if __name__ == "__main__":
    print("🚀 DS Smithery 데이터베이스 초기화를 시작합니다...")
    success = init_database()
    
    if success:
        print("\n✅ 데이터베이스 초기화가 완료되었습니다!")
        print("\n📋 기본 관리자 계정:")
        print("   사용자명: admin")
        print("   이메일: admin@smithery.com")
        print("   비밀번호: admin123")
        print("\n⚠️  보안을 위해 기본 비밀번호를 변경하세요.")
    else:
        print("\n❌ 데이터베이스 초기화에 실패했습니다.") 