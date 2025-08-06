#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import init_database

if __name__ == "__main__":
    print("데이터베이스 초기화를 시작합니다...")
    init_database()
    print("데이터베이스 초기화가 완료되었습니다.") 